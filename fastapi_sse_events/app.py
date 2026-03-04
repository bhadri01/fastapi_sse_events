"""FastAPI application with built-in SSE support."""

import logging
import os

from fastapi import FastAPI

from fastapi_sse_events.broker import EventBroker
from fastapi_sse_events.config import RealtimeConfig
from fastapi_sse_events.redis_backend import RedisBackend

logger = logging.getLogger(__name__)


class SSEApp(FastAPI):
    """
    FastAPI application with automatic SSE event broker configuration.

    This class extends FastAPI and automatically sets up:
    - Redis backend for pub/sub
    - Event broker for publishing/subscribing
    - CORS middleware (optional)
    - Lifecycle events for broker connection

    Example:
        ```python
        from fastapi_sse_events import SSEApp, sse_event, sse_endpoint
        from fastapi import Request

        # Create app with automatic SSE setup
        app = SSEApp(
            title="My API",
            redis_url="redis://localhost:6379"
        )

        # Use decorators - no manual configuration needed!
        @app.post("/comments")
        @sse_event(topic="comments")
        async def create_comment(request: Request, comment: dict):
            return comment

        @app.get("/events")
        @sse_endpoint(topics=["comments"])
        async def events(request: Request):
            pass
        ```
    """

    def __init__(
        self,
        *,
        redis_url: str | None = None,
        redis_host: str | None = None,
        redis_port: int | None = None,
        redis_db: int = 0,
        topic_prefix: str = "",
        enable_cors: bool = True,
        cors_origins: list[str] | None = None,
        **fastapi_kwargs,
    ):
        """
        Initialize SSEApp with automatic broker configuration.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            redis_host: Redis host (alternative to redis_url)
            redis_port: Redis port (alternative to redis_url)
            redis_db: Redis database number
            topic_prefix: Optional prefix for all topics (e.g., "myapp:")
            enable_cors: Whether to enable CORS middleware
            cors_origins: List of allowed origins (default: ["*"])
            **fastapi_kwargs: Additional arguments passed to FastAPI

        Environment Variables:
            REDIS_URL: Redis connection URL
            REDIS_HOST: Redis host
            REDIS_PORT: Redis port
            REDIS_DB: Redis database
            TOPIC_PREFIX: Topic prefix
            CORS_ORIGINS: Comma-separated list of allowed origins
        """
        super().__init__(**fastapi_kwargs)

        # Build Redis connection config
        final_redis_url = redis_url or os.getenv("REDIS_URL")
        final_redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        final_redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        final_redis_db = redis_db if redis_db is not None else int(os.getenv("REDIS_DB", "0"))
        final_topic_prefix = topic_prefix or os.getenv("TOPIC_PREFIX", "")

        # Create config
        if final_redis_url:
            config = RealtimeConfig(redis_url=final_redis_url, topic_prefix=final_topic_prefix)
        else:
            config = RealtimeConfig(
                redis_host=final_redis_host,
                redis_port=final_redis_port,
                redis_db=final_redis_db,
                topic_prefix=final_topic_prefix,
            )

        # Create broker
        redis_backend = RedisBackend(config.redis_url)
        self.state.broker = EventBroker(config, redis_backend)
        logger.info("EventBroker configured and attached to app state")

        # Configure CORS if enabled
        if enable_cors:
            final_cors_origins = cors_origins
            if not final_cors_origins:
                env_origins = os.getenv("CORS_ORIGINS", "*")
                final_cors_origins = env_origins.split(",") if env_origins != "*" else ["*"]

            from fastapi.middleware.cors import CORSMiddleware

            self.add_middleware(
                CORSMiddleware,
                allow_origins=final_cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            logger.info(f"CORS enabled with origins: {final_cors_origins}")

        # Setup lifecycle events
        @self.on_event("startup")
        async def startup_broker():
            """Connect to Redis on startup."""
            await self.state.broker.redis.connect()
            logger.info("EventBroker connected to Redis")

        @self.on_event("shutdown")
        async def shutdown_broker():
            """Disconnect from Redis on shutdown."""
            await self.state.broker.redis.disconnect()
            logger.info("EventBroker disconnected from Redis")

    @property
    def broker(self) -> EventBroker:
        """
        Access the event broker.

        Returns:
            EventBroker instance

        Example:
            ```python
            app = SSEApp()
            await app.broker.publish("topic", "event", {"data": "value"})
            ```
        """
        return self.state.broker
