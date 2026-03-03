"""Integration tests for FastAPI SSE Events."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, Request
from httpx import AsyncClient

from fastapi_sse_events import mount_sse, RealtimeConfig
from fastapi_sse_events.helpers import TopicBuilder


@pytest.mark.asyncio
async def test_mount_sse_integration():
    """Test mounting SSE to FastAPI app."""
    app = FastAPI()

    with patch("fastapi_sse_events.fastapi_integration.RedisBackend") as MockRedisBackend:
        mock_backend = AsyncMock()
        mock_backend.connect = AsyncMock()
        mock_backend.disconnect = AsyncMock()
        MockRedisBackend.return_value = mock_backend

        config = RealtimeConfig(sse_path="/events")
        broker = mount_sse(app, config)

        # Verify broker is stored in app state
        assert hasattr(app.state, "event_broker")
        assert app.state.event_broker == broker

        # Verify SSE endpoint is registered
        routes = [route.path for route in app.routes]
        assert "/events" in routes


@pytest.mark.asyncio
async def test_mount_sse_with_authorization():
    """Test mounting SSE with authorization function."""
    app = FastAPI()

    async def custom_authorize(request: Request, topic: str) -> bool:
        # Custom authorization logic
        return topic.startswith("allowed_")

    with patch("fastapi_sse_events.fastapi_integration.RedisBackend") as MockRedisBackend:
        mock_backend = AsyncMock()
        mock_backend.connect = AsyncMock()
        mock_backend.disconnect = AsyncMock()
        mock_backend.publish = AsyncMock()
        MockRedisBackend.return_value = mock_backend

        broker = mount_sse(app, authorize=custom_authorize)

        # Verify broker works
        assert broker is not None


@pytest.mark.asyncio
async def test_publish_and_subscribe_flow():
    """Test end-to-end publish and subscribe flow."""
    app = FastAPI()

    with patch("fastapi_sse_events.fastapi_integration.RedisBackend") as MockRedisBackend:
        mock_backend = AsyncMock()
        mock_backend.connect = AsyncMock()
        mock_backend.disconnect = AsyncMock()
        mock_backend.publish = AsyncMock()
        MockRedisBackend.return_value = mock_backend

        config = RealtimeConfig()
        broker = mount_sse(app, config)

        # Publish an event
        await broker.publish(
            topic="comment_thread:123",
            event="comment_created",
            data={"comment_id": "456"},
        )

        # Verify publish was called
        mock_backend.publish.assert_called_once()


@pytest.mark.asyncio
async def test_topic_builder_integration():
    """Test TopicBuilder helper integration."""
    app = FastAPI()

    with patch("fastapi_sse_events.fastapi_integration.RedisBackend") as MockRedisBackend:
        mock_backend = AsyncMock()
        mock_backend.connect = AsyncMock()
        mock_backend.disconnect = AsyncMock()
        mock_backend.publish = AsyncMock()
        MockRedisBackend.return_value = mock_backend

        broker = mount_sse(app)
        topics = TopicBuilder()

        # Test various topic builders
        await broker.publish(
            topic=topics.comment_thread(123),
            event="comment_created",
            data={"id": "1"},
        )

        await broker.publish(
            topic=topics.ticket(456),
            event="ticket_updated",
            data={"status": "closed"},
        )

        await broker.publish(
            topic=topics.user("user_789"),
            event="notification",
            data={"message": "Hello"},
        )

        # Verify all publishes were called
        assert mock_backend.publish.call_count == 3


@pytest.mark.asyncio
async def test_application_startup_shutdown():
    """Test application startup and shutdown with SSE."""
    app = FastAPI()

    with patch("fastapi_sse_events.fastapi_integration.RedisBackend") as MockRedisBackend:
        mock_backend = AsyncMock()
        mock_backend.connect = AsyncMock()
        mock_backend.disconnect = AsyncMock()
        MockRedisBackend.return_value = mock_backend

        mount_sse(app)

        # Simulate startup
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Client context manager triggers startup/shutdown
            pass

        # Note: In actual test, startup/shutdown events would be triggered
        # by lifespan context or on_event decorators


def test_helpers_topic_builder():
    """Test TopicBuilder helper methods."""
    topics = TopicBuilder()

    assert topics.comment_thread(123) == "comment_thread:123"
    assert topics.ticket(456) == "ticket:456"
    assert topics.task("789") == "task:789"
    assert topics.workspace("workspace1") == "workspace:workspace1"
    assert topics.user("user123") == "user:user123"
    assert topics.custom("project", "proj1") == "project:proj1"
