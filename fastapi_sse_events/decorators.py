"""Decorator-based utilities for simplified SSE event handling."""

import asyncio
import inspect
import logging
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import Request
from sse_starlette.sse import EventSourceResponse

from fastapi_sse_events.broker import EventBroker

logger = logging.getLogger(__name__)


def sse_event(
    topic: Optional[str] = None,
    event: Optional[str] = None,
    extract_data: Optional[Callable] = None,
    auto_topic: bool = True,
):
    """
    Decorator to automatically publish SSE events after endpoint execution.
    
    This decorator wraps your endpoint function and automatically publishes
    the result as an SSE event, eliminating the need for manual broker calls.
    
    Args:
        topic: Topic to publish to. If None, auto-inferred from route path
        event: Event name. If None, uses the function name
        extract_data: Optional function to extract/transform event data from response
        auto_topic: If True and topic is None, auto-generate topic from route path
    
    Example:
        ```python
        @app.post("/comments")
        @sse_event(topic="comments", event="comment_created")
        async def create_comment(comment: CommentCreate):
            # Your logic here
            return {"id": 1, "content": comment.content}
            # Event automatically published to "comments" topic
        ```
        
        With auto topic inference:
        ```python
        @app.post("/threads/{thread_id}/comments")
        @sse_event()  # Auto-infers topic: "threads.comments"
        async def create_comment(thread_id: int, comment: CommentCreate):
            return {"id": 1, "thread_id": thread_id}
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Execute original function
            result = await func(*args, **kwargs)
            
            # Get request and broker from args
            request = _extract_request_from_args(args, kwargs)
            if not request:
                logger.warning(
                    f"Could not find Request in {func.__name__} args. "
                    "SSE event not published. Add Request parameter to your endpoint."
                )
                return result
            
            broker = _get_broker_from_request(request)
            if not broker:
                logger.warning(f"EventBroker not found in app state for {func.__name__}")
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
                if hasattr(event_data, "dict"):
                    event_data = event_data.dict()
                elif hasattr(event_data, "model_dump"):
                    event_data = event_data.model_dump()
                else:
                    event_data = {"data": event_data}
            
            # Publish event asynchronously (don't block response)
            try:
                await broker.publish(event_topic, event_name, event_data)
                logger.debug(f"Published SSE event: {event_name} to topic: {event_topic}")
            except Exception as e:
                logger.error(f"Failed to publish SSE event: {e}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
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
                if hasattr(event_data, "dict"):
                    event_data = event_data.dict()
                elif hasattr(event_data, "model_dump"):
                    event_data = event_data.model_dump()
                else:
                    event_data = {"data": event_data}
            
            # Publish event (create task for async publish)
            try:
                asyncio.create_task(broker.publish(event_topic, event_name, event_data))
            except Exception as e:
                logger.error(f"Failed to publish SSE event: {e}")
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def sse_endpoint(
    topics: Optional[list[str]] = None,
    authorize: Optional[Callable] = None,
    heartbeat: int = 30,
):
    """
    Decorator to create SSE streaming endpoint.
    
    This decorator automatically handles SSE connection setup, topic subscription,
    and event streaming, eliminating boilerplate code.
    
    Args:
        topics: List of topics to subscribe to. If None, uses 'topic' query param
        authorize: Optional authorization function (request, topic) -> bool
        heartbeat: Heartbeat interval in seconds (0 to disable)
    
    Example:
        ```python
        # Simple SSE endpoint subscribing to specific topics
        @app.get("/events")
        @sse_endpoint(topics=["comments", "users"])
        async def events(request: Request):
            pass  # Decorator handles everything
        
        # With dynamic topics from query params
        @app.get("/events")
        @sse_endpoint()  # Topics from ?topic=comments,users
        async def events(request: Request):
            pass
        
        # With authorization
        async def check_auth(request: Request, topic: str) -> bool:
            # Check if user can access topic
            return True
        
        @app.get("/events")
        @sse_endpoint(authorize=check_auth)
        async def events(request: Request):
            pass
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request) -> EventSourceResponse:
            broker = _get_broker_from_request(request)
            if not broker:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="EventBroker not configured. Use SSEApp or mount_sse()."
                )
            
            # Determine topics to subscribe
            subscribe_topics = topics
            if not subscribe_topics:
                # Get from query params: /events?topic=comments,users
                topic_param = request.query_params.get("topic")
                if topic_param:
                    subscribe_topics = [t.strip() for t in topic_param.split(",") if t.strip()]
            
            if not subscribe_topics:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No topics specified. Provide topics in decorator or as ?topic= query param."
                )
            
            # Authorization check
            if authorize:
                for topic_name in subscribe_topics:
                    try:
                        authorized = await authorize(request, topic_name)
                        if not authorized:
                            from fastapi import HTTPException, status
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Not authorized to access topic: {topic_name}"
                            )
                    except Exception as e:
                        logger.error(f"Authorization failed: {e}")
                        from fastapi import HTTPException, status
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Authorization check failed"
                        )
            
            # Create event generator
            async def event_generator():
                async for message in broker.subscribe(subscribe_topics):
                    yield message
            
            # Return SSE response
            return EventSourceResponse(
                event_generator(),
                ping=heartbeat if heartbeat > 0 else None,
                ping_message_factory=lambda: "ping" if heartbeat > 0 else None,
            )
        
        return wrapper
    
    return decorator


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
