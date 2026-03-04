"""Type definitions for FastAPI SSE Events."""

from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias

from fastapi import Request
from pydantic import BaseModel, Field


class EventData(BaseModel):
    """
    Data structure for an event message.

    Attributes:
        event: Event type/name (e.g., "comment_created", "ticket_updated")
        data: Event payload dictionary
        id: Optional event ID for client-side deduplication and last-event-ID tracking
    """

    event: str = Field(..., description="Event type/name")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload")
    id: str | None = Field(default=None, description="Optional event ID")


# Type alias for authorization callback
# Takes a request and topic, returns True if authorized
AuthorizeFn: TypeAlias = Callable[[Request, str], Awaitable[bool]]
