"""
CRM Comment System Example with Real-time SSE Updates.

This example demonstrates a FastAPI application with:
- REST API for comment CRUD operations
- Server-Sent Events for real-time updates
- Authorization for topic access
- Multi-client synchronization via Redis Pub/Sub

Run with: uvicorn app:app --reload
Then open b in multiple browsers to see real-time updates.
"""

import logging
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from fastapi_sse_events import mount_sse, RealtimeConfig, TopicBuilder

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CRM Comment System with SSE",
    description="Real-time comment updates using Server-Sent Events",
    version="1.0.0",
)

# Enable CORS for frontend access
cors_origins = os.getenv("CORS_ORIGINS", "*")
allowed_origins = cors_origins.split(",") if cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use database in production)
comments_db: dict[str, dict[str, Any]] = {}
threads_db: dict[int, list[str]] = {1: [], 2: [], 3: []}  # Thread IDs
comment_id_counter = 0


# Pydantic models
class CommentCreate(BaseModel):
    """Request model for creating a comment."""

    thread_id: int = Field(..., description="Thread ID")
    author: str = Field(..., min_length=1, description="Comment author")
    content: str = Field(..., min_length=1, description="Comment content")


class CommentUpdate(BaseModel):
    """Request model for updating a comment."""

    content: str = Field(..., min_length=1, description="Updated content")


class Comment(BaseModel):
    """Comment response model."""

    id: str
    thread_id: int
    author: str
    content: str
    created_at: str
    updated_at: str


class Thread(BaseModel):
    """Thread response model."""

    id: int
    comment_count: int
    comments: list[Comment]


# Authorization function for SSE topics
async def authorize_topic(request: Request, topic: str) -> bool:
    """
    Authorize access to SSE topics.

    In production, implement proper authentication/authorization:
    - Check user JWT token
    - Verify user has access to the thread
    - Check user permissions
    """
    # For demo: allow all access
    # In production: verify user can access the thread
    logger.info(f"Authorizing topic access: {topic}")
    return True


# Mount SSE with configuration from environment variables
config = RealtimeConfig(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    heartbeat_seconds=int(os.getenv("SSE_HEARTBEAT_SECONDS", "15")),
    sse_path=os.getenv("SSE_PATH", "/events"),
)
broker = mount_sse(app, config=config, authorize=authorize_topic)

# Topic builder helper
topics = TopicBuilder()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "CRM Comment System with SSE",
        "endpoints": {
            "threads": "/threads",
            "thread_comments": "/threads/{thread_id}/comments",
            "create_comment": "POST /threads/{thread_id}/comments",
            "update_comment": "PUT /comments/{comment_id}",
            "delete_comment": "DELETE /comments/{comment_id}",
            "sse_stream": "/events?topic=comment_thread:{thread_id}",
        },
        "example": {
            "sse_url": "http://localhost:8000/events?topic=comment_thread:1",
            "rest_url": "http://localhost:8000/threads/1/comments",
        },
    }


@app.get("/threads", response_model=list[int], tags=["Threads"])
async def list_threads():
    """List all available thread IDs."""
    return list(threads_db.keys())


@app.get("/threads/{thread_id}/comments", response_model=Thread, tags=["Comments"])
async def get_thread_comments(thread_id: int):
    """Get all comments for a thread."""
    if thread_id not in threads_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread {thread_id} not found",
        )

    comment_ids = threads_db[thread_id]
    comments = [Comment(**comments_db[cid]) for cid in comment_ids]

    return Thread(
        id=thread_id,
        comment_count=len(comments),
        comments=comments,
    )


@app.post("/threads/{thread_id}/comments", response_model=Comment, tags=["Comments"])
async def create_comment(thread_id: int, comment: CommentCreate):
    """Create a new comment and notify subscribers."""
    global comment_id_counter

    if thread_id not in threads_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread {thread_id} not found",
        )

    # Create comment
    comment_id_counter += 1
    comment_id = str(comment_id_counter)
    now = datetime.utcnow().isoformat()

    new_comment = {
        "id": comment_id,
        "thread_id": thread_id,
        "author": comment.author,
        "content": comment.content,
        "created_at": now,
        "updated_at": now,
    }

    # Save to storage
    comments_db[comment_id] = new_comment
    threads_db[thread_id].append(comment_id)

    # Publish SSE event
    await broker.publish(
        topic=topics.comment_thread(thread_id),
        event="comment_created",
        data={
            "comment_id": comment_id,
            "thread_id": thread_id,
            "author": comment.author,
            "timestamp": now,
        },
    )

    logger.info(f"Comment {comment_id} created in thread {thread_id}")

    return Comment(**new_comment)


@app.put("/comments/{comment_id}", response_model=Comment, tags=["Comments"])
async def update_comment(comment_id: str, comment_update: CommentUpdate):
    """Update a comment and notify subscribers."""
    if comment_id not in comments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment {comment_id} not found",
        )

    # Update comment
    comment_data = comments_db[comment_id]
    comment_data["content"] = comment_update.content
    comment_data["updated_at"] = datetime.utcnow().isoformat()

    # Publish SSE event
    await broker.publish(
        topic=topics.comment_thread(comment_data["thread_id"]),
        event="comment_updated",
        data={
            "comment_id": comment_id,
            "thread_id": comment_data["thread_id"],
            "timestamp": comment_data["updated_at"],
        },
    )

    logger.info(f"Comment {comment_id} updated")

    return Comment(**comment_data)


@app.delete("/comments/{comment_id}", tags=["Comments"])
async def delete_comment(comment_id: str):
    """Delete a comment and notify subscribers."""
    if comment_id not in comments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment {comment_id} not found",
        )

    # Get comment data before deletion
    comment_data = comments_db[comment_id]
    thread_id = comment_data["thread_id"]

    # Delete comment
    del comments_db[comment_id]
    threads_db[thread_id].remove(comment_id)

    # Publish SSE event
    await broker.publish(
        topic=topics.comment_thread(thread_id),
        event="comment_deleted",
        data={
            "comment_id": comment_id,
            "thread_id": thread_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    logger.info(f"Comment {comment_id} deleted")

    return {"message": f"Comment {comment_id} deleted", "comment_id": comment_id}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    uvicorn.run(app, host=host, port=port, reload=reload)
