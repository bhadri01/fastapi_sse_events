"""Redis backend for pub/sub messaging."""

import asyncio
import logging
from typing import Any, AsyncGenerator

import redis.asyncio as redis
from redis.asyncio.client import PubSub

logger = logging.getLogger(__name__)


class RedisBackend:
    """
    Redis-based pub/sub backend for event distribution.

    Handles connection management, publishing, and subscribing to Redis channels
    with automatic retry logic and graceful error handling.
    """

    def __init__(self, redis_url: str, max_retries: int = 5, retry_delay: float = 1.0):
        """
        Initialize Redis backend.

        Args:
            redis_url: Redis connection URL
            max_retries: Maximum number of connection retry attempts
            retry_delay: Initial delay between retries (uses exponential backoff)
        """
        self.redis_url = redis_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: redis.Redis | None = None
        self._pubsub: PubSub | None = None

    async def connect(self) -> None:
        """
        Establish connection to Redis with retry logic.

        Raises:
            redis.RedisError: If connection fails after all retries
        """
        for attempt in range(self.max_retries):
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self._client.ping()
                logger.info("Connected to Redis at %s", self.redis_url)
                return
            except (redis.RedisError, ConnectionError) as e:
                if attempt == self.max_retries - 1:
                    logger.error("Failed to connect to Redis after %d attempts", self.max_retries)
                    raise
                delay = self.retry_delay * (2**attempt)
                logger.warning(
                    "Redis connection attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1,
                    self.max_retries,
                    e,
                    delay,
                )
                await asyncio.sleep(delay)

    async def disconnect(self) -> None:
        """Close Redis connection and cleanup resources."""
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe()
                await self._pubsub.close()
            except Exception as e:
                logger.warning("Error closing pubsub: %s", e)
            finally:
                self._pubsub = None

        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.warning("Error closing Redis client: %s", e)
            finally:
                self._client = None

        logger.info("Disconnected from Redis")

    async def publish(self, topic: str, message: str) -> None:
        """
        Publish a message to a Redis channel.

        Args:
            topic: Channel/topic name
            message: Message payload (as JSON string)

        Raises:
            redis.RedisError: If publish fails
        """
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            await self._client.publish(topic, message)
            logger.debug("Published message to topic '%s'", topic)
        except redis.RedisError as e:
            logger.error("Failed to publish to topic '%s': %s", topic, e)
            raise

    async def subscribe(self, topics: list[str]) -> AsyncGenerator[tuple[str, str], None]:
        """
        Subscribe to Redis channels and yield messages.

        Args:
            topics: List of channel/topic names to subscribe to

        Yields:
            Tuples of (topic, message) for each received message

        Raises:
            redis.RedisError: If subscription fails
        """
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        self._pubsub = self._client.pubsub()

        try:
            # Subscribe to all topics
            await self._pubsub.subscribe(*topics)
            logger.info("Subscribed to topics: %s", topics)

            # Listen for messages
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    topic = message["channel"]
                    data = message["data"]
                    logger.debug("Received message from topic '%s'", topic)
                    yield topic, data

        except redis.RedisError as e:
            logger.error("Redis subscription error: %s", e)
            raise
        finally:
            if self._pubsub:
                try:
                    await self._pubsub.unsubscribe()
                except Exception as e:
                    logger.warning("Error unsubscribing: %s", e)

    async def __aenter__(self) -> "RedisBackend":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()
