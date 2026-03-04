"""
Ultra-Simple CRM Comment System Example.

Demonstrates the easiest way to use fastapi-sse-events with decorators.

Run with: uvicorn app_simple_new:app --reload
"""

from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi_sse_events import mount_sse, publish_event, subscribe_to_events

app = FastAPI(title="Simple CRM Comments")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount SSE - one line setup!
mount_sse(app)

# Simple in-memory storage
comments = {}
comment_id = 0


class CommentCreate(BaseModel):
    """Create comment request."""

    thread_id: int
    author: str
    content: str


class Comment(BaseModel):
    """Comment response."""

    id: int
    thread_id: int
    author: str
    content: str
    created_at: str


@app.get("/")
async def root():
    """API info."""
    return {
        "message": "Simple CRM Comments with SSE",
        "sse_endpoint": "/events?topic=comments",
        "create_comment": "POST /comments",
        "list_comments": "GET /comments",
    }


@app.post("/comments")
@publish_event(topic="comments", event="created")
async def create_comment(_request: Request, comment: CommentCreate) -> Comment:
    """
    Create a comment.

    The @publish_event decorator automatically publishes SSE event!
    No manual broker.publish() needed. Just return the data.
    """
    global comment_id
    comment_id += 1

    new_comment = Comment(
        id=comment_id,
        thread_id=comment.thread_id,
        author=comment.author,
        content=comment.content,
        created_at=datetime.utcnow().isoformat(),
    )

    comments[comment_id] = new_comment

    # Simply return - decorator handles SSE publishing automatically!
    return new_comment


@app.get("/comments")
async def list_comments():
    """List all comments."""
    return {"comments": [c.dict() for c in comments.values()]}


@app.get("/events")
@subscribe_to_events()
async def events_endpoint(request: Request):
    """
    SSE endpoint.

    The @subscribe_to_events decorator handles all the SSE streaming!
    Usage: /events?topic=comments
    """
    # Decorator handles everything - this function body can be empty!
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
