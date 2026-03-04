"""Fan-out manager for efficient Redis pub/sub distribution."""

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator

from fastapi_sse_events.metrics import get_metrics_collector
from fastapi_sse_events.redis_backend import RedisBackend

logger = logging.getLogger(__name__)


class FanOutManager:
    """
    Manages Redis subscriptions with fan-out pattern.

    Single Redis subscriptions are shared among multiple clients,
    drastically reducing Redis connection count and improving scalability.
    """

    def __init__(self, redis_backend: RedisBackend, max_queue_size: int = 100):
        """
        Initialize fan-out manager.

        Args:
            redis_backend: Redis backend instance
            max_queue_size: Maximum queue size per client (prevents memory bloat)
        """
        self.redis = redis_backend
        self.max_queue_size = max_queue_size

        # Topic -> Set of client queues
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)

        # Topic -> Redis subscription task
        self._redis_tasks: dict[str, asyncio.Task] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # Instance ID for distributed event IDs
        self._instance_id = uuid.uuid4().hex[:8]
        self._event_counter = 0

        # Metrics
        self._metrics = get_metrics_collector()

    async def subscribe(self, topics: list[str]) -> AsyncGenerator[str, None]:
        """
        Subscribe to topics with fan-out pattern.

        Args:
            topics: List of topics to subscribe to

        Yields:
            Messages from subscribed topics
        """
        # Create bounded queue for this client
        client_queue: asyncio.Queue[str | None] = asyncio.Queue(
            maxsize=self.max_queue_size
        )

        async with self._lock:
            # Register client for each topic
            for topic in topics:
                self._subscribers[topic].add(client_queue)
                await self._metrics.record_topic_subscribed(topic)

                # Start Redis subscription if not already running
                if topic not in self._redis_tasks:
                    self._redis_tasks[topic] = asyncio.create_task(
                        self._redis_subscriber(topic)
                    )
                    logger.debug(f"Started Redis subscription for topic: {topic}")

        try:
            # Yield messages from queue
            while True:
                message = await client_queue.get()

                # None signals end of stream
                if message is None:
                    break

                yield message

        finally:
            # Cleanup: unregister client
            async with self._lock:
                for topic in topics:
                    if client_queue in self._subscribers[topic]:
                        self._subscribers[topic].discard(client_queue)
                        await self._metrics.record_topic_unsubscribed(topic)

                    # Stop Redis subscription if no clients left
                    if not self._subscribers[topic] and topic in self._redis_tasks:
                        self._redis_tasks[topic].cancel()
                        del self._redis_tasks[topic]
                        logger.debug(f"Stopped Redis subscription for topic: {topic}")

    async def _redis_subscriber(self, topic: str) -> None:
        """
        Internal Redis subscriber that fans out to clients.

        Args:
            topic: Topic to subscribe to
        """
        try:
            async for _, message in self.redis.subscribe([topic]):
                async with self._lock:
                    subscribers = list(self._subscribers[topic])

                # Fan out to all subscribers
                for client_queue in subscribers:
                    try:
                        # Non-blocking put with timeout
                        await asyncio.wait_for(
                            client_queue.put(message),
                            timeout=0.1
                        )
                    except asyncio.TimeoutError:
                        # Client queue full (slow consumer) - drop message
                        await self._metrics.record_message_dropped()
                        logger.warning(
                            f"Dropped message for slow client on topic: {topic}"
                        )
                    except Exception as e:
                        logger.error(f"Error delivering message: {e}")

        except asyncio.CancelledError:
            logger.debug(f"Redis subscriber cancelled for topic: {topic}")
        except Exception as e:
            logger.error(f"Redis subscriber error for topic {topic}: {e}")

    def generate_event_id(self) -> str:
        """
        Generate distributed-safe event ID.

        Returns:
            Unique event ID combining instance ID, timestamp, and counter
        """
        self._event_counter += 1
        import time
        timestamp = int(time.time() * 1000)
        return f"{self._instance_id}-{timestamp}-{self._event_counter}"

    async def get_stats(self) -> dict:
        """
        Get fan-out manager statistics.

        Returns:
            Dictionary with subscription stats
        """
        async with self._lock:
            return {
                "active_topics": len(self._subscribers),
                "total_clients": sum(len(subs) for subs in self._subscribers.values()),
                "topics": {
                    topic: len(subs)
                    for topic, subs in self._subscribers.items()
                },
            }

    async def close(self) -> None:
        """Close all Redis subscriptions and cleanup."""
        async with self._lock:
            # Cancel all Redis tasks
            for task in self._redis_tasks.values():
                task.cancel()

            # Wait for cancellation
            if self._redis_tasks:
                await asyncio.gather(
                    *self._redis_tasks.values(),
                    return_exceptions=True
                )

            self._redis_tasks.clear()
            self._subscribers.clear()

        logger.info("Fan-out manager closed")
