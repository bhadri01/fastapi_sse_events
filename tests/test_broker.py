"""Tests for event broker module."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from fastapi_sse_events.broker import EventBroker
from fastapi_sse_events.config import RealtimeConfig
from fastapi_sse_events.types import EventData


@pytest.mark.asyncio
async def test_publish(config: RealtimeConfig, mock_redis_backend: AsyncMock):
    """Test event publishing."""
    broker = EventBroker(config, mock_redis_backend)

    await broker.publish("test_topic", "test_event", {"key": "value"})

    # Verify Redis publish was called
    mock_redis_backend.publish.assert_called_once()
    call_args = mock_redis_backend.publish.call_args

    # Check topic with prefix
    assert call_args[0][0] == "test:test_topic"

    # Check message format
    message_json = call_args[0][1]
    event_data = EventData.model_validate_json(message_json)
    assert event_data.event == "test_event"
    assert event_data.data == {"key": "value"}
    assert event_data.id is not None


@pytest.mark.asyncio
async def test_format_sse_message(config: RealtimeConfig, mock_redis_backend: AsyncMock):
    """Test SSE message formatting."""
    broker = EventBroker(config, mock_redis_backend)

    event_data = EventData(
        event="comment_created",
        data={"comment_id": "123"},
        id="event-123",
    )

    sse_message = broker._format_sse_message(event_data)

    assert "event: comment_created\n" in sse_message
    assert 'data: {"comment_id": "123"}\n' in sse_message
    assert "id: event-123\n" in sse_message
    assert sse_message.endswith("\n\n")


@pytest.mark.asyncio
async def test_subscribe_redis_messages(config: RealtimeConfig, mock_redis_backend: AsyncMock):
    """Test subscribing to Redis messages."""
    broker = EventBroker(config, mock_redis_backend)

    # Mock Redis subscription to yield messages
    async def mock_subscribe(_topics):
        event_data = EventData(event="test_event", data={"key": "value"}, id="123")
        yield ("test:test_topic", event_data.model_dump_json())

    mock_redis_backend.subscribe.return_value = mock_subscribe(["test:test_topic"])

    # Collect one message
    messages = []
    async for sse_message in broker.subscribe(["test_topic"]):
        messages.append(sse_message)
        if len(messages) == 1:
            break

    assert len(messages) == 1
    assert "event: test_event" in messages[0]
    assert '"key": "value"' in messages[0]


@pytest.mark.asyncio
async def test_heartbeat_generation(config: RealtimeConfig, mock_redis_backend: AsyncMock):
    """Test heartbeat message generation."""
    # Use short heartbeat for testing
    config.heartbeat_seconds = 0.1

    broker = EventBroker(config, mock_redis_backend)

    # Mock empty Redis subscription
    async def mock_subscribe(_topics):
        # Yield nothing (wait for heartbeat)
        await asyncio.sleep(10)
        yield ("", "")

    mock_redis_backend.subscribe.return_value = mock_subscribe([])

    # Collect messages with timeout
    messages = []
    try:
        async with asyncio.timeout(0.3):
            async for sse_message in broker.subscribe(["test_topic"]):
                messages.append(sse_message)
                if len(messages) >= 2:
                    break
    except asyncio.TimeoutError:
        pass

    # Should have received heartbeat messages
    assert len(messages) >= 1
    assert any("event: ping" in msg for msg in messages)


@pytest.mark.asyncio
async def test_event_id_generation(config: RealtimeConfig, mock_redis_backend: AsyncMock):
    """Test event ID generation."""
    broker = EventBroker(config, mock_redis_backend)

    id1 = broker._generate_event_id()
    id2 = broker._generate_event_id()

    # IDs should be unique
    assert id1 != id2

    # IDs should follow format: timestamp-counter
    assert "-" in id1
    assert "-" in id2
