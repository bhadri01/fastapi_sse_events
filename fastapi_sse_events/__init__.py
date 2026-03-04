"""
FastAPI SSE Events - Server-Sent Events notifications using Redis Pub/Sub.

This package provides a lightweight way to add real-time notifications to
FastAPI REST applications using Server-Sent Events (SSE) and Redis Pub/Sub.

Quick Start:
    >>> from fastapi_sse_events import SSEApp, publish_event, subscribe_to_events
    >>>
    >>> app = SSEApp(redis_url="redis://localhost:6379")
    >>>
    >>> @app.post("/comments")
    >>> @publish_event(topic="comments", event="created")
    >>> async def create_comment(comment: Comment):
    ...     return save_comment(comment)
    >>>
    >>> @app.get("/events")
    >>> @subscribe_to_events()
    >>> async def events(request: Request):
    ...     pass  # Returns EventSourceResponse

For more information, visit: https://github.com/bhadri01/fastapi_sse_events
"""

# Core application
from fastapi_sse_events.app import SSEApp

# Advanced API
from fastapi_sse_events.broker import EventBroker
from fastapi_sse_events.config import RealtimeConfig

# Decorators (Simplified API - Recommended)
# Legacy decorators (backward compatibility)
from fastapi_sse_events.decorators import (
    publish_event,
    sse_endpoint,
    sse_event,
    subscribe_to_events,
)
from fastapi_sse_events.fastapi_integration import mount_sse

# Monitoring & Health
from fastapi_sse_events.health import create_health_router

# Helpers & Utilities
from fastapi_sse_events.helpers import TopicBuilder
from fastapi_sse_events.metrics import MetricsCollector, get_metrics_collector
from fastapi_sse_events.types import AuthorizeFn, EventData

__version__ = "0.2.0"
__author__ = "bhadri01"
__license__ = "MIT"

__all__ = [
    # Core
    "SSEApp",
    "EventBroker",
    "RealtimeConfig",
    # Decorators (Recommended)
    "publish_event",
    "subscribe_to_events",
    # Advanced
    "mount_sse",
    "TopicBuilder",
    # Types
    "AuthorizeFn",
    "EventData",
    # Monitoring
    "create_health_router",
    "MetricsCollector",
    "get_metrics_collector",
    # Legacy (Deprecated but maintained for compatibility)
    "sse_event",
    "sse_endpoint",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
