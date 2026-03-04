"""
Simplified CRM Comment System using decorator-based SSE API.

This is a simplified version of the CRM example demonstrating
the new decorator-based API that eliminates boilerplate code.

Compare this to app.py to see the difference!

Run with: poetry run uvicorn app_simple:app --reload
Then open client.html in your browser.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field

# Import the simplified API - just 3 imports!
from fastapi_sse_events import SSEApp, sse_endpoint, sse_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app with automatic SSE setup - just one line!
# No need for mount_sse, RealtimeConfig, EventBroker, etc.
app = SSEApp(
    title="CRM Comments (Simplified)",
    description="Real-time comments with decorator-based SSE",
    version="2.0.0",
    redis_url="redis://localhost:6379",  # or use env: REDIS_URL
    enable_cors=True,  # CORS automatically configured
)

# In-memory storage
comments_db: dict[str, dict[str, Any]] = {}
threads_db: dict[int, list[str]] = {1: [], 2: [], 3: []}
comment_id_counter = 0


# Models
class CommentCreate(BaseModel):
    thread_id: int = Field(..., description="Thread ID")
    author: str = Field(..., min_length=1, description="Author")
    content: str = Field(..., min_length=1, description="Content")


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, description="Updated content")


class Comment(BaseModel):
    id: str
    thread_id: int
    author: str
    content: str
    created_at: str
    updated_at: str


# ============================================================================
# API Endpoints - No manual broker calls needed!
# ============================================================================


@app.post("/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
@sse_event(topic="comments", event="comment_created")  # Automatically publishes!
async def create_comment(_request: Request, comment: CommentCreate) -> Comment:
    """
    Create a new comment.

    The @sse_event decorator automatically publishes the result to SSE clients.
    No manual broker.publish() needed!
    """
    global comment_id_counter
    comment_id_counter += 1
    comment_id = str(comment_id_counter)

    now = datetime.now().isoformat()
    new_comment = Comment(
        id=comment_id,
        thread_id=comment.thread_id,
        author=comment.author,
        content=comment.content,
        created_at=now,
        updated_at=now,
    )

    # Store comment
    comments_db[comment_id] = new_comment.dict()
    threads_db.setdefault(comment.thread_id, []).append(comment_id)

    logger.info(f"Created comment {comment_id} in thread {comment.thread_id}")

    # Return the comment - decorator publishes it automatically!
    return new_comment


@app.put("/comments/{comment_id}", response_model=Comment)
@sse_event(topic="comments", event="comment_updated")  # Auto-publish on update
async def update_comment(
    _request: Request, comment_id: str, comment_update: CommentUpdate
) -> Comment:
    """
    Update a comment.

    The @sse_event decorator handles SSE publishing automatically.
    """
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Update comment
    comments_db[comment_id]["content"] = comment_update.content
    comments_db[comment_id]["updated_at"] = datetime.now().isoformat()

    updated_comment = Comment(**comments_db[comment_id])
    logger.info(f"Updated comment {comment_id}")

    return updated_comment


@app.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
@sse_event(topic="comments", event="comment_deleted")
async def delete_comment(_request: Request, comment_id: str) -> dict:
    """
    Delete a comment.

    Returns a dict for the SSE event (won't be in HTTP response due to 204).
    """
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Get thread_id before deleting
    thread_id = comments_db[comment_id]["thread_id"]

    # Delete comment
    del comments_db[comment_id]
    threads_db[thread_id] = [cid for cid in threads_db[thread_id] if cid != comment_id]

    logger.info(f"Deleted comment {comment_id}")

    # Return data for SSE event
    return {"comment_id": comment_id, "thread_id": thread_id}


@app.get("/comments/{comment_id}", response_model=Comment)
async def get_comment(comment_id: str) -> Comment:
    """Get a single comment (no SSE event)."""
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")

    return Comment(**comments_db[comment_id])


@app.get("/threads/{thread_id}/comments", response_model=list[Comment])
async def get_thread_comments(thread_id: int) -> list[Comment]:
    """Get all comments in a thread (no SSE event)."""
    comment_ids = threads_db.get(thread_id, [])
    return [Comment(**comments_db[cid]) for cid in comment_ids]


# ============================================================================
# SSE Endpoint - Just one decorator!
# ============================================================================


@app.get("/events")
@sse_endpoint(topics=["comments"])  # Automatic SSE streaming!
async def events(request: Request):
    """
    SSE endpoint for real-time updates.

    The @sse_endpoint decorator handles all the SSE complexity:
    - Subscription management
    - Event streaming
    - Heartbeat
    - Connection handling

    No manual code needed!
    """
    pass  # Decorator does everything!


# Alternative: Dynamic topics from query params
@app.get("/events/dynamic")
@sse_endpoint()  # Topics from ?topic=comments,users
async def events_dynamic(request: Request):
    """
    SSE endpoint with dynamic topic subscription.

    Usage: GET /events/dynamic?topic=comments,users
    """
    pass


# With authorization
async def authorize_topic(_request: Request, topic: str) -> bool:
    """Check if user can access topic."""
    # In production: check JWT, permissions, etc.
    logger.info(f"Authorizing topic: {topic}")
    return True  # Allow all for demo


@app.get("/events/secure")
@sse_endpoint(topics=["comments"], authorize=authorize_topic)
async def events_secure(request: Request):
    """SSE endpoint with authorization."""
    pass


# ============================================================================
# Health Check
# ============================================================================


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "broker": "connected" if app.broker else "not configured",
    }


# ============================================================================
# Comparison with Original API
# ============================================================================

"""
BEFORE (Original API - app.py):
===================================

# 1. Create config
config = RealtimeConfig(redis_url="redis://localhost:6379")

# 2. Create backend
redis_backend = RedisBackend(config)

# 3. Create broker
broker = EventBroker(config, redis_backend)

# 4. Mount SSE
mount_sse(app, broker, authorize_fn=authorize_topic)

# 5. Manual lifecycle
@app.on_event("startup")
async def startup():
    await redis_backend.connect()

@app.on_event("shutdown")
async def shutdown():
    await redis_backend.disconnect()

# 6. Manual event publishing in each endpoint
@app.post("/comments")
async def create_comment(comment: CommentCreate):
    new_comment = create_comment_logic(comment)

    # Manual publish
    await broker.publish(
        topic=f"comment_thread:{comment.thread_id}",
        event="comment_created",
        data=new_comment.dict()
    )

    return new_comment

# 7. Manual SSE endpoint creation
from fastapi_sse_events import create_sse_endpoint
sse_handler = create_sse_endpoint(broker, authorize_topic)
app.get("/events")(sse_handler)


AFTER (New Decorator API - this file):
======================================

# 1. One-line app creation with auto-config
app = SSEApp(redis_url="redis://localhost:6379")

# 2. Decorator-based event publishing
@app.post("/comments")
@sse_event(topic="comments", event="comment_created")
async def create_comment(request: Request, comment: CommentCreate):
    return create_comment_logic(comment)  # Auto-published!

# 3. Decorator-based SSE endpoint
@app.get("/events")
@sse_endpoint(topics=["comments"])
async def events(request: Request):
    pass  # Everything automatic!


LINES OF CODE:
- Original: ~50 lines of setup + manual publish in each endpoint
- New API: ~3 lines of setup + 1 decorator per endpoint

That's 90%+ reduction in boilerplate! 🎉
"""
