"""
FastAPI SSE Events - Server-Sent Events notifications using Redis Pub/Sub.

This package provides a lightweight way to add real-time notifications to
FastAPI REST applications using Server-Sent Events (SSE) and Redis Pub/Sub.
"""

from fastapi_sse_events.app import SSEApp
from fastapi_sse_events.broker import EventBroker
from fastapi_sse_events.config import RealtimeConfig
from fastapi_sse_events.decorators import sse_endpoint, sse_event
from fastapi_sse_events.fastapi_integration import mount_sse
from fastapi_sse_events.helpers import TopicBuilder
from fastapi_sse_events.types import AuthorizeFn, EventData

__version__ = "0.1.0"

__all__ = [
    # Simplified API (recommended)
    "SSEApp",
    "sse_event",
    "sse_endpoint",
    # Advanced API
    "EventBroker",
    "RealtimeConfig",
    "mount_sse",
    "TopicBuilder",
    "AuthorizeFn",
    "EventData",
]
