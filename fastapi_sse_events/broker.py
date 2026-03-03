"""Event broker for managing SSE events."""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator

from fastapi_sse_events.config import RealtimeConfig
from fastapi_sse_events.redis_backend import RedisBackend
from fastapi_sse_events.types import EventData

logger = logging.getLogger(__name__)


class EventBroker:
    """
    Event broker for publishing and subscribing to SSE events via Redis.

    Handles event serialization, SSE message formatting, and heartbeat generation.
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
        self._event_id_counter = 0

    def _generate_event_id(self) -> str:
        """
        Generate a unique event ID.

        Returns:
            Event ID string combining timestamp and counter
        """
        self._event_id_counter += 1
        return f"{int(time.time() * 1000)}-{self._event_id_counter}"

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

        # Publish to Redis
        await self.redis.publish(full_topic, message)
        logger.info("Published event '%s' to topic '%s'", event, full_topic)

    async def subscribe(
        self, topics: list[str]
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to topics and yield SSE-formatted messages.

        This method listens to Redis pub/sub and yields SSE messages including:
        - Regular events from the subscribed topics
        - Periodic heartbeat/ping events to keep the connection alive

        Args:
            topics: List of topic names to subscribe to

        Yields:
            SSE-formatted message strings

        Example:
            async for sse_message in broker.subscribe(["comment_thread:123"]):
                # Send to client via StreamingResponse
                yield sse_message
        """
        # Apply topic prefix to all topics
        full_topics = [self.config.get_topic(topic) for topic in topics]

        # Create async task for Redis subscription
        redis_task = asyncio.create_task(self._redis_message_loop(full_topics))

        # Create async task for heartbeat
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        try:
            # Use a queue to merge Redis messages and heartbeats
            message_queue: asyncio.Queue[str] = asyncio.Queue()

            # Background task to process Redis messages
            async def process_redis_messages() -> None:
                try:
                    async for sse_message in redis_task:
                        await message_queue.put(sse_message)
                except Exception as e:
                    logger.error("Redis message processing error: %s", e)
                finally:
                    await message_queue.put("")  # Signal end

            # Background task to process heartbeats
            async def process_heartbeats() -> None:
                try:
                    async for heartbeat_message in heartbeat_task:
                        await message_queue.put(heartbeat_message)
                except Exception as e:
                    logger.error("Heartbeat processing error: %s", e)

            # Start background tasks
            redis_processor = asyncio.create_task(process_redis_messages())
            heartbeat_processor = asyncio.create_task(process_heartbeats())

            # Yield messages from queue
            while True:
                message = await message_queue.get()
                if message == "":  # End signal
                    break
                yield message

        finally:
            # Cleanup
            redis_task.cancel()
            heartbeat_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _redis_message_loop(self, topics: list[str]) -> AsyncGenerator[str, None]:
        """
        Internal generator for Redis pub/sub messages.

        Args:
            topics: List of topics to subscribe to

        Yields:
            SSE-formatted messages from Redis
        """
        async for _topic, message_json in self.redis.subscribe(topics):
            try:
                # Deserialize from JSON
                event_data = EventData.model_validate_json(message_json)

                # Format as SSE message
                sse_message = self._format_sse_message(event_data)

                yield sse_message

            except Exception as e:
                logger.error("Error processing Redis message: %s", e)
                continue

    async def _heartbeat_loop(self) -> AsyncGenerator[str, None]:
        """
        Internal generator for heartbeat/ping events.

        Yields:
            SSE-formatted heartbeat messages at configured intervals
        """
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

            yield sse_message
