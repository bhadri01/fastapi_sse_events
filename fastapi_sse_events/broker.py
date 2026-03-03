"""Event broker for managing SSE events."""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator

from fastapi_sse_events.config import RealtimeConfig
from fastapi_sse_events.fanout import FanOutManager
from fastapi_sse_events.metrics import get_metrics_collector
from fastapi_sse_events.redis_backend import RedisBackend
from fastapi_sse_events.types import EventData

logger = logging.getLogger(__name__)


class EventBroker:
    """
    Event broker for publishing and subscribing to SSE events via Redis.

    Handles event serialization, SSE message formatting, and heartbeat generation.
    Uses fan-out pattern for efficient Redis connection management.
    """

    def __init__(self, config: RealtimeConfig, redis_backend: RedisBackend):
        """
        Initialize the event broker.

        Args:
            config: Real-time configuration
            redis_backend: Redis backend instance
        """
        self.config = config
        self.redis = redis_backend
        
        # Fan-out manager for efficient subscriptions
        self._fanout = FanOutManager(
            redis_backend,
            max_queue_size=config.max_queue_size
        )
        
        # Connection tracking
        self._active_connections = 0
        self._connection_lock = asyncio.Lock()
        
        # Shared heartbeat
        self._heartbeat_task: asyncio.Task | None = None
        self._heartbeat_queues: set[asyncio.Queue] = set()
        
        # Metrics collector
        self._metrics = get_metrics_collector()

    def _generate_event_id(self) -> str:
        """
        Generate a distributed-safe unique event ID.

        Returns:
            Event ID string with instance ID, timestamp, and counter
        """
        return self._fanout.generate_event_id()

    def _format_sse_message(self, event_data: EventData) -> str:
        """
        Format event data as SSE message.

        SSE format:
            event: event_name
            data: {"key": "value"}
            id: event_id

        Args:
            event_data: Event data to format

        Returns:
            SSE-formatted message string
        """
        lines = []

        # Add event type
        lines.append(f"event: {event_data.event}")

        # Add data (JSON encoded)
        data_json = json.dumps(event_data.data)
        lines.append(f"data: {data_json}")

        # Add ID if present
        if event_data.id:
            lines.append(f"id: {event_data.id}")

        # SSE messages end with double newline
        return "\n".join(lines) + "\n\n"

    async def publish(self, topic: str, event: str, data: dict[str, Any]) -> None:
        """
        Publish an event to a topic.

        Args:
            topic: Topic name (will be prefixed if config has topic_prefix)
            event: Event type/name
            data: Event payload dictionary

        Raises:
            ValueError: If message exceeds size limit

        Example:
            await broker.publish(
                topic="comment_thread:123",
                event="comment_created",
                data={"comment_id": "456", "thread_id": "123"}
            )
        """
        # Apply topic prefix
        full_topic = self.config.get_topic(topic)

        # Create event data with auto-generated ID
        event_data = EventData(
            event=event,
            data=data,
            id=self._generate_event_id(),
        )

        # Serialize to JSON for Redis
        message = event_data.model_dump_json()
        
        # Validate message size
        message_size = len(message.encode('utf-8'))
        if message_size > self.config.max_message_size:
            logger.error(
                f"Message too large: {message_size} bytes (limit: {self.config.max_message_size})"
            )
            await self._metrics.record_publish_error()
            raise ValueError(
                f"Message size {message_size} exceeds limit {self.config.max_message_size}"
            )

        # Publish to Redis with latency tracking
        try:
            start_time = time.time()
            await self.redis.publish(full_topic, message)
            latency_ms = (time.time() - start_time) * 1000
            
            await self._metrics.record_message_published(latency_ms)
            logger.debug("Published event '%s' to topic '%s' (%.2fms)", event, full_topic, latency_ms)
        except Exception as e:
            await self._metrics.record_publish_error()
            raise

    async def subscribe(
        self, topics: list[str]
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to topics and yield SSE-formatted messages.

        This method uses fan-out pattern for efficient Redis connection management
        and includes connection limits, backpressure handling, and shared heartbeats.

        Args:
            topics: List of topic names to subscribe to

        Yields:
            SSE-formatted message strings

        Raises:
            RuntimeError: If max connections exceeded

        Example:
            async for sse_message in broker.subscribe(["comment_thread:123"]):
                # Send to client via StreamingResponse
                yield sse_message
        """
        # Check connection limit
        async with self._connection_lock:
            if self._active_connections >= self.config.max_connections:
                logger.warning(
                    f"Max connections ({self.config.max_connections}) reached"
                )
                await self._metrics.record_connection_rejected()
                raise RuntimeError("Maximum concurrent connections exceeded")
            self._active_connections += 1
        
        await self._metrics.record_connection_opened()
        logger.info(f"Active connections: {self._active_connections}/{self.config.max_connections}")

        # Apply topic prefix to all topics
        full_topics = [self.config.get_topic(topic) for topic in topics]

        # Create heartbeat queue for this connection
        heartbeat_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=1)
        self._heartbeat_queues.add(heartbeat_queue)
        
        # Start shared heartbeat if not running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._shared_heartbeat_loop())

        try:
            # Subscribe using fan-out manager
            async for message_json in self._fanout.subscribe(full_topics):
                # Check for heartbeat
                try:
                    heartbeat = heartbeat_queue.get_nowait()
                    yield heartbeat
                except asyncio.QueueEmpty:
                    pass
                
                # Process Redis message
                try:
                    event_data = EventData.model_validate_json(message_json)
                    sse_message = self._format_sse_message(event_data)
                    await self._metrics.record_message_delivered()
                    yield sse_message
                except Exception as e:
                    logger.error("Error processing message: %s", e)
                    continue

        finally:
            # Cleanup
            self._heartbeat_queues.discard(heartbeat_queue)
            
            async with self._connection_lock:
                self._active_connections -= 1
            
            await self._metrics.record_connection_closed()
            logger.info(f"Active connections: {self._active_connections}/{self.config.max_connections}")

    async def _shared_heartbeat_loop(self) -> None:
        """
        Shared heartbeat loop that broadcasts to all connected clients.
        
        Uses a single timer instead of one per client for efficiency.
        """
        logger.info("Starting shared heartbeat loop")
        
        try:
            while True:
                await asyncio.sleep(self.config.heartbeat_seconds)
                
                # Create heartbeat event
                heartbeat_data = EventData(
                    event="ping",
                    data={"timestamp": int(time.time())},
                    id=self._generate_event_id(),
                )
                
                # Format as SSE message
                sse_message = self._format_sse_message(heartbeat_data)
                
                # Broadcast to all heartbeat queues
                for queue in list(self._heartbeat_queues):
                    try:
                        queue.put_nowait(sse_message)
                    except asyncio.QueueFull:
                        pass  # Skip if queue full
                    except Exception as e:
                        logger.error(f"Error broadcasting heartbeat: {e}")
        
        except asyncio.CancelledError:
            logger.info("Shared heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Shared heartbeat loop error: {e}")

    async def get_stats(self) -> dict:
        """
        Get broker statistics.
        
        Returns:
            Dictionary with broker stats including connections and topics
        """
        fanout_stats = await self._fanout.get_stats()
        
        return {
            "active_connections": self._active_connections,
            "max_connections": self.config.max_connections,
            "heartbeat_clients": len(self._heartbeat_queues),
            **fanout_stats,
        }

    async def close(self) -> None:
        """Close the broker and cleanup resources."""
        # Stop heartbeat
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close fan-out manager
        await self._fanout.close()
        
        logger.info("Event broker closed")
