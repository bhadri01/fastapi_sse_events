"""Tests for Redis backend module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis

from fastapi_sse_events.redis_backend import RedisBackend


@pytest.mark.asyncio
async def test_connect_success():
    """Test successful Redis connection."""
    backend = RedisBackend("redis://localhost:6379/0")

    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_from_url.return_value = mock_client

        await backend.connect()

        mock_from_url.assert_called_once()
        mock_client.ping.assert_called_once()
        assert backend._client is not None


@pytest.mark.asyncio
async def test_connect_retry():
    """Test Redis connection with retry logic."""
    backend = RedisBackend("redis://localhost:6379/0", max_retries=3, retry_delay=0.01)

    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        # Fail twice, succeed third time
        mock_client.ping = AsyncMock(
            side_effect=[redis.RedisError("fail"), redis.RedisError("fail"), None]
        )
        mock_from_url.return_value = mock_client

        await backend.connect()

        assert mock_client.ping.call_count == 3


@pytest.mark.asyncio
async def test_connect_fail_all_retries():
    """Test Redis connection failure after all retries."""
    backend = RedisBackend("redis://localhost:6379/0", max_retries=2, retry_delay=0.01)

    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=redis.RedisError("fail"))
        mock_from_url.return_value = mock_client

        with pytest.raises(redis.RedisError):
            await backend.connect()


@pytest.mark.asyncio
async def test_disconnect():
    """Test Redis disconnection."""
    backend = RedisBackend("redis://localhost:6379/0")

    # Setup mock client and pubsub
    backend._client = AsyncMock()
    backend._pubsub = AsyncMock()
    backend._pubsub.unsubscribe = AsyncMock()
    backend._pubsub.close = AsyncMock()
    backend._client.close = AsyncMock()

    await backend.disconnect()

    backend._pubsub.unsubscribe.assert_called_once()
    backend._pubsub.close.assert_called_once()
    backend._client.close.assert_called_once()
    assert backend._client is None
    assert backend._pubsub is None


@pytest.mark.asyncio
async def test_publish_success():
    """Test successful message publishing."""
    backend = RedisBackend("redis://localhost:6379/0")
    backend._client = AsyncMock()
    backend._client.publish = AsyncMock()

    await backend.publish("test_topic", "test_message")

    backend._client.publish.assert_called_once_with("test_topic", "test_message")


@pytest.mark.asyncio
async def test_publish_not_connected():
    """Test publishing when not connected."""
    backend = RedisBackend("redis://localhost:6379/0")

    with pytest.raises(RuntimeError, match="not connected"):
        await backend.publish("test_topic", "test_message")


@pytest.mark.asyncio
async def test_subscribe_success():
    """Test successful subscription."""
    backend = RedisBackend("redis://localhost:6379/0")
    backend._client = MagicMock()

    # Mock pubsub
    mock_pubsub = AsyncMock()
    backend._client.pubsub.return_value = mock_pubsub
    mock_pubsub.subscribe = AsyncMock()

    # Mock message stream
    async def mock_listen():
        yield {"type": "message", "channel": "topic1", "data": "data1"}
        yield {"type": "subscribe", "channel": "topic1", "data": 1}
        yield {"type": "message", "channel": "topic2", "data": "data2"}

    mock_pubsub.listen = mock_listen
    mock_pubsub.unsubscribe = AsyncMock()

    messages = []
    async for topic, data in backend.subscribe(["topic1", "topic2"]):
        messages.append((topic, data))
        if len(messages) == 2:
            break

    assert len(messages) == 2
    assert messages[0] == ("topic1", "data1")
    assert messages[1] == ("topic2", "data2")


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager."""
    backend = RedisBackend("redis://localhost:6379/0")

    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_client.close = AsyncMock()
        mock_from_url.return_value = mock_client

        async with backend:
            assert backend._client is not None

        mock_client.close.assert_called_once()
