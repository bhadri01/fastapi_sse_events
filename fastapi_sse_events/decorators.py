"""Decorator-based utilities for simplified SSE event handling."""

import asyncio
import inspect
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, ParamSpec

from fastapi import Request, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from fastapi_sse_events.broker import EventBroker

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def publish_event(
    topic: Optional[str] = None,
    event: Optional[str] = None,
    extract_data: Optional[Callable[[Any], dict]] = None,
    auto_topic: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to automatically publish SSE events after endpoint execution.
    
    This is the PRIMARY method for publishing events - eliminates manual broker calls.
    
    Args:
        topic: Topic to publish to. If None, auto-inferred from route path
        event: Event name. If None, uses the function name
        extract_data: Optional function to extract/transform event data from response
        auto_topic: If True and topic is None, auto-generate topic from route path
    
    Examples:
        ```python
        # Basic usage with explicit topic
        @app.post("/comments")
        @publish_event(topic="comments", event="created")
        async def create_comment(comment: CommentCreate):
            new_comment = save_comment(comment)
            return new_comment
            # Event automatically published!
        
        # Auto-infer topic from route
        @app.post("/threads/{thread_id}/comments")
        @publish_event()  # Topic: "threads.comments", Event: "create_comment"
        async def create_comment(thread_id: int, comment: CommentCreate):
            return {"id": 1, "thread_id": thread_id}
        
        # Custom data extraction
        @app.put("/comments/{id}")
        @publish_event(
            topic="comments",
            event="updated",
            extract_data=lambda result: {"id": result["id"], "timestamp": result["updated_at"]}
        )
        async def update_comment(id: int, comment: CommentUpdate):
            return update_comment_in_db(id, comment)
        ```
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Execute original function
            result = await func(*args, **kwargs)
            
            # Get request and broker from args
            request = _extract_request_from_args(args, kwargs)
            if not request:
                logger.debug(
                    f"No Request parameter in {func.__name__}. "
                    "SSE event not published. Add Request parameter to enable auto-publish."
                )
                return result
            
            broker = _get_broker_from_request(request)
            if not broker:
                logger.debug(f"EventBroker not found in app state for {func.__name__}")
                return result
            
            # Determine topic
            event_topic = topic
            if not event_topic and auto_topic:
                event_topic = _infer_topic_from_route(request.url.path)
            if not event_topic:
                event_topic = "default"
            
            # Determine event name
            event_name = event or func.__name__
            
            # Extract event data
            event_data = extract_data(result) if extract_data else result
            
            # Ensure event_data is a dict
            if not isinstance(event_data, dict):
                event_data = _convert_to_dict(event_data)
            
            # Publish event asynchronously (don't block response)
            try:
                await broker.publish(event_topic, event_name, event_data)
                logger.debug(f"Published event '{event_name}' to topic '{event_topic}'")
            except ValueError as e:
                # Message too large
                logger.error(f"Failed to publish event (message too large): {e}")
            except Exception as e:
                logger.error(f"Failed to publish SSE event: {e}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Execute original function
            result = func(*args, **kwargs)
            
            # Get request and broker
            request = _extract_request_from_args(args, kwargs)
            if not request:
                return result
            
            broker = _get_broker_from_request(request)
            if not broker:
                return result
            
            # Determine topic and event
            event_topic = topic
            if not event_topic and auto_topic:
                event_topic = _infer_topic_from_route(request.url.path)
            if not event_topic:
                event_topic = "default"
            
            event_name = event or func.__name__
            
            # Extract event data
            event_data = extract_data(result) if extract_data else result
            if not isinstance(event_data, dict):
                event_data = _convert_to_dict(event_data)
            
            # Publish event (create task for async publish)
            try:
                asyncio.create_task(broker.publish(event_topic, event_name, event_data))
            except Exception as e:
                logger.error(f"Failed to publish SSE event: {e}")
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


def subscribe_to_events(
    topics: Optional[list[str]] = None,
    authorize: Optional[Callable[[Request, str], bool]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., EventSourceResponse]]:
    """
    Decorator to create SSE streaming endpoint.
    
    This is the PRIMARY method for creating SSE endpoints - eliminates boilerplate.
    
    Args:
        topics: List of topics to subscribe to. If None, uses 'topic' query param
        authorize: Optional authorization function (request, topic) -> bool
    
    Examples:
        ```python
        # Simple SSE endpoint with specific topics
        @app.get("/events")
        @subscribe_to_events(topics=["comments", "users"])
        async def events_endpoint(request: Request):
            pass  # Decorator handles everything!
        
        # Dynamic topics from query params: /events?topic=comments,users
        @app.get("/events")
        @subscribe_to_events()
        async def events_endpoint(request: Request):
            pass
        
        # With authorization
        async def check_auth(request: Request, topic: str) -> bool:
            user_id = request.state.user_id  # From auth middleware
            return can_access_topic(user_id, topic)
        
        @app.get("/events")
        @subscribe_to_events(authorize=check_auth)
        async def events_endpoint(request: Request):
            pass
        ```
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., EventSourceResponse]:
        @wraps(func)
        async def wrapper(request: Request, **kwargs: Any) -> EventSourceResponse:
            broker = _get_broker_from_request(request)
            if not broker:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="EventBroker not configured. Use mount_sse() to configure.",
                )
            
            # Determine topics to subscribe
            subscribe_topics = topics
            if not subscribe_topics:
                # Get from query params: /events?topic=comments,users
                topic_param = request.query_params.get("topic")
                if topic_param:
                    subscribe_topics = [t.strip() for t in topic_param.split(",") if t.strip()]
            
            if not subscribe_topics:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No topics specified. Provide topics in decorator or ?topic= query param.",
                )
            
            # Authorization check (parallelized)
            if authorize:
                try:
                    auth_results = await asyncio.gather(
                        *[authorize(request, topic_name) for topic_name in subscribe_topics],
                        return_exceptions=True
                    )
                    
                    for topic_name, result in zip(subscribe_topics, auth_results):
                        if isinstance(result, Exception):
                            logger.error(f"Authorization failed for {topic_name}: {result}")
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Authorization check failed"
                            )
                        if not result:
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Not authorized to access topic: {topic_name}"
                            )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Authorization error: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Authorization failed"
                    )
            
            # Create event generator
            async def event_generator():
                try:
                    async for message in broker.subscribe(subscribe_topics):
                        if await request.is_disconnected():
                            logger.info(f"Client disconnected from topics: {subscribe_topics}")
                            break
                        yield message
                except RuntimeError as e:
                    if "Maximum concurrent connections exceeded" in str(e):
                        logger.warning("Connection limit reached")
                        yield f"event: error\ndata: {{'message': 'Connection limit reached'}}\n\n"
                    else:
                        raise
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    yield f"event: error\ndata: {{'message': 'Stream error'}}\n\n"
            
            # Return SSE response
            return EventSourceResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
        
        return wrapper
    
    return decorator


# Legacy alias for backward compatibility
sse_endpoint = subscribe_to_events
sse_event = publish_event


def _convert_to_dict(obj: Any) -> dict:
    """Convert object to dictionary."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    elif isinstance(obj, dict):
        return obj
    else:
        return {"data": obj}


def _extract_request_from_args(args: tuple, kwargs: dict) -> Optional[Request]:
    """Extract Request object from function arguments."""
    # Check kwargs first
    if "request" in kwargs:
        return kwargs["request"]
    
    # Check args
    for arg in args:
        if isinstance(arg, Request):
            return arg
    
    return None


def _get_broker_from_request(request: Request) -> Optional[EventBroker]:
    """Get EventBroker from app state."""
    if hasattr(request.app, "state") and hasattr(request.app.state, "event_broker"):
        return request.app.state.event_broker
    # Legacy fallback
    if hasattr(request.app, "state") and hasattr(request.app.state, "broker"):
        return request.app.state.broker
    return None


def _infer_topic_from_route(path: str) -> str:
    """
    Convert route path to topic name.
    
    Examples:
        /comments -> comments
        /threads/123/comments -> threads.comments
        /api/v1/users/456/posts -> users.posts
    """
    # Remove leading/trailing slashes
    path = path.strip("/")
    
    # Split by slash and filter out numeric IDs and common prefixes
    parts = []
    for part in path.split("/"):
        # Skip numeric IDs
        if part.isdigit():
            continue
        # Skip common API prefixes
        if part.lower() in ["api", "v1", "v2", "v3"]:
            continue
        parts.append(part)
    
    # Join with dots
    return ".".join(parts) if parts else "default"
