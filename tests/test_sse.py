"""Tests for SSE endpoint handler."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status

from fastapi_sse_events.broker import EventBroker
from fastapi_sse_events.sse import create_sse_endpoint


@pytest.mark.asyncio
async def test_sse_endpoint_missing_topic(
    _fastapi_app: FastAPI,
    event_broker: EventBroker,
    mock_request: Request,
):
    """Test SSE endpoint with missing topic parameter."""
    sse_handler = create_sse_endpoint(event_broker)

    # Mock request with no topic
    mock_request.query_params = {}

    with pytest.raises(Exception) as exc_info:
        await sse_handler(mock_request, topic=None)

    # Should raise HTTPException for missing topic
    assert "Missing" in str(exc_info.value) or exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_sse_endpoint_unauthorized(
    event_broker: EventBroker,
    mock_request: Request,
):
    """Test SSE endpoint with unauthorized access."""
    # Authorization function that denies access
    async def deny_all(_request: Request, _topic: str) -> bool:
        return False

    sse_handler = create_sse_endpoint(event_broker, authorize_fn=deny_all)

    with pytest.raises(Exception) as exc_info:
        await sse_handler(mock_request, topic="test_topic")

    # Should raise HTTPException for unauthorized access
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_sse_endpoint_authorized(
    event_broker: EventBroker,
    mock_request: Request,
    _mock_redis_backend: AsyncMock,
):
    """Test SSE endpoint with authorized access."""
    # Authorization function that allows access
    async def allow_all(_request: Request, _topic: str) -> bool:
        return True

    # Mock broker subscription
    async def mock_subscribe(_topics):
        yield "event: test\ndata: {}\n\n"

    event_broker.subscribe = AsyncMock(return_value=mock_subscribe([]))

    sse_handler = create_sse_endpoint(event_broker, authorize_fn=allow_all)

    response = await sse_handler(mock_request, topic="test_topic")

    # Should return EventSourceResponse
    assert response is not None
    assert response.media_type == "text/event-stream"


@pytest.mark.asyncio
async def test_sse_endpoint_multiple_topics(
    event_broker: EventBroker,
    mock_request: Request,
):
    """Test SSE endpoint with multiple topics."""
    async def allow_all(_request: Request, _topic: str) -> bool:
        return True

    async def mock_subscribe(topics):
        # Verify multiple topics were passed
        assert len(topics) == 2
        assert "topic1" in topics
        assert "topic2" in topics
        yield "event: test\ndata: {}\n\n"

    event_broker.subscribe = AsyncMock(return_value=mock_subscribe([]))

    sse_handler = create_sse_endpoint(event_broker, authorize_fn=allow_all)

    response = await sse_handler(mock_request, topic="topic1,topic2")

    assert response is not None


@pytest.mark.asyncio
async def test_sse_endpoint_client_disconnect(
    event_broker: EventBroker,
    mock_request: Request,
):
    """Test SSE endpoint handling client disconnect."""
    async def allow_all(_request: Request, _topic: str) -> bool:
        return True

    # Simulate client disconnect after first message
    disconnect_call_count = 0

    async def mock_is_disconnected():
        nonlocal disconnect_call_count
        disconnect_call_count += 1
        return disconnect_call_count > 1

    mock_request.is_disconnected = mock_is_disconnected

    # Mock broker subscription with multiple messages
    async def mock_subscribe(_topics):
        for i in range(5):
            yield f"event: test{i}\ndata: {{}}\n\n"
            await asyncio.sleep(0.01)

    event_broker.subscribe = AsyncMock(return_value=mock_subscribe([]))

    sse_handler = create_sse_endpoint(event_broker, authorize_fn=allow_all)
    response = await sse_handler(mock_request, topic="test_topic")

    # Collect messages
    messages = []
    async for message in response.body_iterator:
        messages.append(message)

    # Should stop after disconnect
    assert len(messages) < 5


@pytest.mark.asyncio
async def test_sse_endpoint_no_authorization(
    event_broker: EventBroker,
    mock_request: Request,
):
    """Test SSE endpoint without authorization function."""
    async def mock_subscribe(_topics):
        yield "event: test\ndata: {}\n\n"

    event_broker.subscribe = AsyncMock(return_value=mock_subscribe([]))

    # No authorize_fn provided
    sse_handler = create_sse_endpoint(event_broker, authorize_fn=None)

    response = await sse_handler(mock_request, topic="test_topic")

    # Should work without authorization
    assert response is not None
    assert response.media_type == "text/event-stream"
