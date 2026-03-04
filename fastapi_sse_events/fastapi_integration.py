"""FastAPI integration for SSE events."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_sse_events.broker import EventBroker
from fastapi_sse_events.config import RealtimeConfig
from fastapi_sse_events.health import create_health_router
from fastapi_sse_events.redis_backend import RedisBackend
from fastapi_sse_events.sse import create_sse_endpoint
from fastapi_sse_events.types import AuthorizeFn

logger = logging.getLogger(__name__)


def mount_sse(
    app: FastAPI,
    config: RealtimeConfig | None = None,
    authorize: AuthorizeFn | None = None,
    include_health_checks: bool = True,
) -> EventBroker:
    """
    Mount SSE event streaming to a FastAPI application.

    This function:
    1. Creates Redis backend and event broker
    2. Registers SSE endpoint at configured path
    3. Sets up startup/shutdown handlers for Redis connection
    4. Exposes broker via app.state for easy access
    5. Optionally includes health check endpoints

    Args:
        app: FastAPI application instance
        config: Configuration (uses defaults if not provided)
        authorize: Optional authorization callback for topic access
        include_health_checks: Whether to include /health endpoints (default: True)

    Returns:
        EventBroker instance for publishing events

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_sse_events import mount_sse, RealtimeConfig

        app = FastAPI()

        # Mount SSE with default config
        broker = mount_sse(app)

        # Or with custom config optimized for 100K users
        config = RealtimeConfig(
            redis_url="redis://localhost:6379/0",
            max_connections=10000,  # Per instance
            max_queue_size=50,
        )
        broker = mount_sse(app, config)

        # Publish events from your endpoints
        @app.post("/comments")
        async def create_comment(comment: Comment):
            # ... save comment ...
            await broker.publish(
                topic=f"comment_thread:{comment.thread_id}",
                event="comment_created",
                data={"comment_id": comment.id}
            )
            return comment
        ```
    """
    # Use default config if not provided
    if config is None:
        config = RealtimeConfig()

    # Create Redis backend
    redis_backend = RedisBackend(config.redis_url)

    # Create event broker
    broker = EventBroker(config, redis_backend)

    # Store broker in app state for easy access
    app.state.event_broker = broker

    # Create lifespan context manager if not already defined
    if not hasattr(app.router, "lifespan_context"):
        # For newer FastAPI versions that use lifespan parameter
        original_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def lifespan_with_redis(app: FastAPI) -> AsyncGenerator[None, None]:
            """Lifespan context manager with Redis connection management."""
            # Startup
            logger.info("Starting SSE event system...")
            await redis_backend.connect()
            logger.info("SSE event system ready")

            # Run original lifespan if exists
            if original_lifespan:
                async with original_lifespan(app):
                    yield
            else:
                yield

            # Shutdown
            logger.info("Shutting down SSE event system...")
            await broker.close()  # Close broker and fan-out manager
            await redis_backend.disconnect()
            logger.info("SSE event system stopped")

        # Replace lifespan
        app.router.lifespan_context = lifespan_with_redis
    else:
        # Fallback for older FastAPI or apps with existing startup/shutdown
        @app.on_event("startup")
        async def startup_event() -> None:
            """Initialize Redis connection on startup."""
            logger.info("Starting SSE event system...")
            await redis_backend.connect()
            logger.info("SSE event system ready")

        @app.on_event("shutdown")
        async def shutdown_event() -> None:
            """Close Redis connection on shutdown."""
            logger.info("Shutting down SSE event system...")
            await broker.close()  # Close broker and fan-out manager
            await redis_backend.disconnect()
            logger.info("SSE event system stopped")

    # Create and register SSE endpoint
    sse_endpoint = create_sse_endpoint(broker, authorize)
    app.get(
        config.sse_path,
        summary="Server-Sent Events stream",
        description="Subscribe to real-time events for specified topics",
        tags=["SSE"],
    )(sse_endpoint)

    logger.info("SSE endpoint mounted at: %s", config.sse_path)

    # Include health check endpoints for monitoring
    if include_health_checks:
        health_router = create_health_router()
        app.include_router(health_router)
        logger.info("Health check endpoints mounted: /health, /metrics")

    return broker
