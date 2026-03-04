"""SSE endpoint handler for FastAPI."""

import asyncio
import logging
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from fastapi_sse_events.broker import EventBroker
from fastapi_sse_events.types import AuthorizeFn

logger = logging.getLogger(__name__)


def create_sse_endpoint(
    broker: EventBroker,
    authorize_fn: AuthorizeFn | None = None,
) -> Callable:
    """
    Create an SSE endpoint handler for FastAPI.

    Args:
        broker: Event broker instance for publishing/subscribing
        authorize_fn: Optional authorization callback to validate topic access

    Returns:
        FastAPI endpoint function that handles SSE connections

    Example:
        ```python
        async def authorize(request: Request, topic: str) -> bool:
            # Check if user can access this topic
            return True

        sse_endpoint = create_sse_endpoint(broker, authorize)
        app.get("/events")(sse_endpoint)
        ```
    """

    async def sse_handler(request: Request, topic: str | None = None) -> EventSourceResponse:
        """
        Handle SSE connection requests.

        Args:
            request: FastAPI request object
            topic: Topic name(s) to subscribe to (query parameter)

        Returns:
            EventSourceResponse streaming SSE messages

        Raises:
            HTTPException: If topic is missing or authorization fails
        """
        # Validate topic parameter
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required query parameter: topic",
            )

        # Parse topics (support comma-separated list)
        topics = [t.strip() for t in topic.split(",") if t.strip()]

        if not topics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one topic is required",
            )

        # Authorization check for each topic (parallelized)
        if authorize_fn:
            try:
                # Run all authorization checks in parallel
                auth_results = await asyncio.gather(
                    *[authorize_fn(request, topic_name) for topic_name in topics],
                    return_exceptions=True,
                )

                # Check results
                for topic_name, result in zip(topics, auth_results, strict=False):
                    if isinstance(result, Exception):
                        logger.error("Authorization check failed for %s: %s", topic_name, result)
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Authorization check failed",
                        )
                    if not result:
                        logger.warning(
                            "Unauthorized topic access attempt: %s from %s",
                            topic_name,
                            request.client.host if request.client else "unknown",
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Not authorized to access topic: {topic_name}",
                        )
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Authorization error: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization failed",
                ) from e

        logger.info(
            "SSE connection established for topics: %s from %s",
            topics,
            request.client.host if request.client else "unknown",
        )

        # Create SSE event generator
        async def event_generator():
            try:
                async for sse_message in broker.subscribe(topics):
                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.info("Client disconnected from topics: %s", topics)
                        break

                    yield sse_message

            except RuntimeError as e:
                if "Maximum concurrent connections exceeded" in str(e):
                    logger.warning("Connection limit reached for topics: %s", topics)
                    yield "event: error\ndata: {'message': 'Server connection limit reached. Try again later.'}\n\n"
                else:
                    logger.error("Runtime error in SSE stream: %s", e)
                    yield "event: error\ndata: {'message': 'Stream error'}\n\n"
            except Exception as e:
                logger.error("Error in SSE event stream: %s", e)
                yield "event: error\ndata: {'message': 'Stream error'}\n\n"

            finally:
                logger.info("SSE connection closed for topics: %s", topics)

        # Return SSE response
        return EventSourceResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Disable buffering for Nginx
            },
        )

    return sse_handler
