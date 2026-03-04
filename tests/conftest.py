"""Pytest configuration and shared fixtures."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request
from httpx import AsyncClient

from fastapi_sse_events.broker import EventBroker
from fastapi_sse_events.config import RealtimeConfig
from fastapi_sse_events.redis_backend import RedisBackend


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def config() -> RealtimeConfig:
    """Create test configuration."""
    return RealtimeConfig(
        redis_url="redis://localhost:6379/0",
        heartbeat_seconds=15,
        sse_path="/events",
        topic_prefix="test",
    )


@pytest.fixture
def mock_redis_backend() -> AsyncMock:
    """Create mock Redis backend."""
    backend = AsyncMock(spec=RedisBackend)
    backend.connect = AsyncMock()
    backend.disconnect = AsyncMock()
    backend.publish = AsyncMock()
    backend.subscribe = AsyncMock()
    return backend


@pytest.fixture
def event_broker(config: RealtimeConfig, mock_redis_backend: AsyncMock) -> EventBroker:
    """Create event broker with mock Redis backend."""
    return EventBroker(config, mock_redis_backend)


@pytest.fixture
def fastapi_app() -> FastAPI:
    """Create FastAPI test application."""
    return FastAPI()


@pytest.fixture
async def async_client(fastapi_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_request() -> Request:
    """Create mock FastAPI request."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.is_disconnected = AsyncMock(return_value=False)
    return request
