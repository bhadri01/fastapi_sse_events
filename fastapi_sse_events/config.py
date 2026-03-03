"""Configuration for FastAPI SSE Events."""

from pydantic import Field
from pydantic_settings import BaseSettings


class RealtimeConfig(BaseSettings):
    """
    Configuration for the real-time SSE event system.

    Attributes:
        redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
        heartbeat_seconds: Interval between heartbeat/ping events to keep connections alive
        sse_path: HTTP path where the SSE endpoint will be mounted
        topic_prefix: Optional prefix for all topic names (useful for multi-tenancy)
        max_connections: Maximum concurrent SSE connections allowed
        max_queue_size: Maximum messages queued per client (prevents memory bloat)
        max_message_size: Maximum message size in bytes (prevents large message attacks)
        rate_limit_per_second: Rate limit for publish operations per second (0 = unlimited)
    """

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    heartbeat_seconds: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Heartbeat interval in seconds",
    )
    sse_path: str = Field(
        default="/events",
        description="Path where SSE endpoint will be mounted",
    )
    topic_prefix: str = Field(
        default="",
        description="Optional prefix for all topic names",
    )
    max_connections: int = Field(
        default=1000,
        ge=1,
        description="Maximum concurrent SSE connections",
    )
    max_queue_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Maximum queued messages per client",
    )
    max_message_size: int = Field(
        default=65536,  # 64 KB
        ge=1024,
        le=1048576,  # 1 MB
        description="Maximum message size in bytes",
    )
    rate_limit_per_second: int = Field(
        default=0,
        ge=0,
        description="Rate limit for publish operations (0 = unlimited)",
    )

    def get_topic(self, topic: str) -> str:
        """
        Get the full topic name with prefix applied.

        Args:
            topic: The base topic name

        Returns:
            The prefixed topic name
        """
        if self.topic_prefix:
            return f"{self.topic_prefix}:{topic}"
        return topic

    class Config:
        """Pydantic config."""

        env_prefix = "SSE_"
        case_sensitive = False
