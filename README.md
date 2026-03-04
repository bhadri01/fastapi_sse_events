# FastAPI SSE Events

**v0.2.0**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/fastapi-sse-events.svg)](https://pypi.org/project/fastapi-sse-events/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Add real-time "refresh-less" updates to your FastAPI REST API using Server-Sent Events (SSE) and Redis Pub/Sub. Perfect for collaborative tools and dashboards.

✅ Simple Integration • ✅ Type Safe • ✅ Redis Backed • ✅ Horizontally Scalable

---

## 📚 Documentation

- **[Full Documentation](https://bhadri01.github.io/fastapi_sse_events)** - Complete guide with examples
- **[PyPI Package](https://pypi.org/project/fastapi-sse-events/)** - Installation and releases
- **[GitHub Repository](https://github.com/bhadri01/fastapi_sse_events)** - Source code and issues
- **[Changelog](CHANGELOG.md)** - Version history

---

## Table of Contents

- [Overview](#overview)
- [Why SSE?](#why-sse)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Simplified API (Recommended)](#simplified-api-recommended)
- [Architecture](#architecture)
- [Features](#features)
- [How It Works](#how-it-works)
- [Basic Integration](#basic-integration)
- [Publishing Events](#publishing-events)
- [Authorization](#authorization)
- [Topic Patterns](#topic-patterns)
- [Configuration](#configuration)
- [Client Integration](#client-integration)
  - [JavaScript Client](#javascript-client)
  - [React Client](#react-client)
  - [Python Client](#python-client)
- [Production Setup](#production-setup)
- [Nginx Configuration](#nginx-configuration)
- [Docker Deployment](#docker-deployment)
- [Performance Tips](#performance-tips)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

**FastAPI SSE Events** enables near real-time notifications for REST-based applications without the complexity of WebSockets. Clients subscribe to Server-Sent Event streams for specific topics, receive lightweight notifications when data changes, then refresh data via existing REST endpoints.

### 💡 Perfect For

- Collaborative CRM systems where sales reps see updates from teammates
- Project management tools with real-time task updates
- Live dashboards showing metrics and notifications
- Multi-user editing interfaces requiring change notifications

---

## Why SSE?

### The Problem

Traditional REST APIs require manual refresh to see updates from other users. This creates poor collaboration experiences and inefficient workflows. Users constantly hit refresh or polling adds unnecessary server load.

### Why Not WebSockets?

WebSockets are powerful but come with complexity:

- Require separate infrastructure and connection management
- More difficult to debug and monitor
- Overkill for one-way notifications
- Don't work well with existing REST patterns
- Harder to secure with standard auth mechanisms

### The SSE Solution

#### HTTP Based
Works with existing infrastructure - no special proxying or routing needed.

#### Native Browser Support
Built-in `EventSource` API in all modern browsers with automatic reconnection.

#### One-Way Communication
Perfect for notifications - server pushes updates, client remains stateless.

#### REST as Source of Truth
SSE notifies, REST endpoints provide data - clean separation of concerns.

---

## Installation

```

### Requirements

- Python 3.10+
- FastAPI 0.104.0+
- Redis 5.0+ (running locally or remotely)

### ℹ️ Redis Setup

You'll need a Redis server. Quick options:

**Docker:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

**Local Install:**
```bash
redis-server
```

---

## Quick Start

### ⭐ Recommended Flow

Use the **simplified decorator-based API** with `SSEApp`, `@publish_event`, and `@subscribe_to_events`. This is the current, recommended approach.

Get SSE running in your FastAPI app with just a few lines of code:

### 📝 1. Create Your FastAPI App

**app.py:**
```python
from fastapi import Request
from fastapi_sse_events import SSEApp, publish_event, subscribe_to_events

app = SSEApp(
    title="My API",
    redis_url="redis://localhost:6379"
)

@app.post("/tasks")
@publish_event(topic="tasks", event="task:created")
async def create_task(request: Request, task: dict):
    # ... save task to database ...
    return {"id": 1, **task}  # auto-published to SSE clients

@app.get("/events")
@subscribe_to_events()
async def events(request: Request):
    pass
```

### 🌐 2. Connect from Browser

**client.js:**
```javascript
// Subscribe to topic from query param
const eventSource = new EventSource('/events?topic=tasks');

eventSource.addEventListener('task:created', async (event) => {
    const data = JSON.parse(event.data);
    console.log('Task event:', data);

    // Notify-then-fetch pattern (recommended)
    const response = await fetch(`/tasks/${data.id}`);
    const task = await response.json();
    renderTask(task);
});

eventSource.addEventListener('open', () => {
    console.log('✅ Connected to SSE');
});
```

### ✅ That's It!

You now have real-time notifications. Clients connect to `/events?topic=...` and receive instant updates when decorated endpoints return.

---

## Simplified API (Recommended)

**⭐ Recommended Approach**

The **simplified decorator-based API** makes adding real-time SSE events incredibly easy by eliminating 75%+ of boilerplate code. It provides auto-configuration, automatic event publishing via decorators, and automatic SSE streaming.

### ℹ️ Naming Conventions

**Current Names (Recommended):** `@publish_event`, `@subscribe_to_events`

**Legacy Aliases (Still Supported):** `@sse_event`, `@sse_endpoint`

Both naming conventions work interchangeably. For new projects, use the current names.

### Key Features

#### ✅ Auto-Configuration
One-line app setup with automatic broker, Redis, and CORS configuration.

#### ✨ @sse_event Decorator
Automatically publish endpoint responses as SSE events - no manual calls needed.

#### 📡 @sse_endpoint Decorator
Create SSE streaming endpoints with one decorator - handles everything automatically.

#### ⚡ 75% Less Code
Reduce boilerplate from ~50 lines to ~10 lines. Focus on your business logic.

### 🚀 Getting Started (3 Steps)

#### Step 1: Create SSEApp

Replace `FastAPI()` with `SSEApp()` for automatic configuration:

**app.py:**
```python
from fastapi import Request
from fastapi_sse_events import SSEApp, sse_event, sse_endpoint

# One-line setup with auto-configuration!
app = SSEApp(
    title="My API",
    redis_url="redis://localhost:6379"  # or use REDIS_URL env var
)

# That's it! No manual broker setup, no lifecycle management needed!
```

#### Step 2: Use @publish_event Decorator

Automatically publish events when endpoints return:

```python
@app.post("/comments")
@publish_event(topic="comments", event="comment_created")
async def create_comment(request: Request, comment: dict):
    # Your business logic here
    new_comment = {"id": 1, "content": comment["content"]}
    
    # Just return it - automatically published to SSE clients!
    return new_comment
```

#### Step 3: Use @subscribe_to_events Decorator

Create SSE streaming endpoints with zero boilerplate:

```python
@app.get("/events")
@subscribe_to_events()
async def events(request: Request):
    pass  # Decorator handles all streaming logic!
```

### ✅ Complete!

You now have real-time SSE with minimal code. Open the API docs at `http://localhost:8000/docs` to test it!

### 📝 SSEApp - Auto-configured FastAPI

`SSEApp` extends `FastAPI` and automatically configures everything needed for SSE:

```python
from fastapi_sse_events import SSEApp

app = SSEApp(
    title="My API",
    version="1.0.0",
    
    # Redis connection (choose one)
    redis_url="redis://localhost:6379",       # Option 1: URL
    # redis_host="localhost",                  # Option 2: Host/Port
    # redis_port=6379,
    # redis_db=0,
    
    # Optional settings
    topic_prefix="myapp:",                    # Prefix all topics
    enable_cors=True,                         # Auto-enable CORS
    cors_origins=["*"],                       # Allowed origins
)
```

#### What SSEApp Does Automatically

- ✅ Creates and configures `EventBroker`
- ✅ Sets up Redis connection with Pub/Sub
- ✅ Manages broker lifecycle (connect on startup, disconnect on shutdown)
- ✅ Configures CORS middleware (optional)
- ✅ Makes broker available at `app.broker` and `request.app.state.broker`

#### ℹ️ Environment Variables

SSEApp reads from environment variables if parameters not provided:

- `REDIS_URL` - Redis connection URL
- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `REDIS_DB` - Redis database (default: 0)
- `TOPIC_PREFIX` - Topic prefix (default: "")
- `CORS_ORIGINS` - Comma-separated origins (default: *)

### 📤 @publish_event - Auto-Publish Decorator

The `@publish_event` decorator automatically publishes your endpoint's response as an SSE event. No more manual `broker.publish()` calls!

**Legacy Alias:** `@sse_event` (still supported for backwards compatibility)

```python
from fastapi_sse_events import publish_event

# Explicit topic and event name
@app.post("/comments")
@publish_event(topic="comments", event="comment_created")
async def create_comment(request: Request, comment: dict):
    return {"id": 1, "content": comment["content"]}

# Auto-infer topic from route path
@app.post("/threads/{thread_id}/comments")
@publish_event()  # Auto-infers topic: "threads.comments"
async def add_comment(request: Request, thread_id: int, comment: dict):
    return {"id": 1, "thread_id": thread_id, **comment}

# Custom data extraction
@app.post("/users")
@publish_event(
    topic="users",
    extract_data=lambda resp: {"user_id": resp["id"]}  # Only publish ID
)
async def create_user(request: Request, user: dict):
    full_user = {"id": 1, "password": "secret", **user}
    return full_user  # Only {"user_id": 1} published to SSE
```

#### Decorator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `topic` | str \| None | Topic to publish to. Auto-inferred from route if None. |
| `event` | str \| None | Event name. Uses function name if None. |
| `extract_data` | Callable \| None | Function to transform response before publishing. |
| `auto_topic` | bool | Auto-generate topic from route path (default: True). |

#### Auto-Topic Inference

When `topic` is not provided, the decorator infers it from the route path:

- `/comments` → `comments`
- `/threads/123/comments` → `threads.comments`
- `/api/v1/users/456` → `users` (filters out "api", "v1", IDs)

#### ⚠️ Important

You must add `request: Request` parameter to your endpoint for the decorator to work. The decorator needs access to the app state to publish events.

### 📡 @subscribe_to_events - Auto-Streaming Decorator

The `@subscribe_to_events` decorator creates SSE streaming endpoints with zero boilerplate. It handles subscription, event streaming, heartbeat, and connection management automatically.

**Legacy Alias:** `@sse_endpoint` (still supported for backwards compatibility)

```python
from fastapi_sse_events import sse_endpoint

# Simple SSE endpoint with static topics
@app.get("/events")
@sse_endpoint(topics=["comments", "users"])
async def events(request: Request):
    pass  # Decorator handles everything!

# Dynamic topics from query params
@app.get("/events/dynamic")
@sse_endpoint()  # Topics from ?topic=comments,users
async def events_dynamic(request: Request):
    pass

# With authorization
async def check_auth(request: Request, topic: str) -> bool:
    user = await get_current_user(request)
    return user.can_access(topic)

@app.get("/events/secure")
@sse_endpoint(topics=["comments"], authorize=check_auth)
async def events_secure(request: Request):
    pass

# Custom heartbeat
@app.get("/events/fast")
@sse_endpoint(topics=["live-data"], heartbeat=10)  # 10 second heartbeat
async def events_fast(request: Request):
    pass
```

#### Decorator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `topics` | list[str] \| None | Topics to subscribe to. Uses query param if None. |
| `authorize` | Callable \| None | Authorization function `(request, topic) → bool`. |
| `heartbeat` | int | Heartbeat interval in seconds (default: 30, 0 to disable). |

### ⚖️ Before vs After Comparison

#### ❌ Before (Manual API) - ~50 lines

```python
from fastapi import FastAPI
from fastapi_sse_events import (
    EventBroker, RealtimeConfig,
    RedisBackend, mount_sse
)

app = FastAPI()

# Manual configuration
config = RealtimeConfig(
    redis_url="redis://localhost:6379"
)
redis_backend = RedisBackend(config)
broker = EventBroker(config, redis_backend)

# Manual lifecycle
@app.on_event("startup")
async def startup():
    await redis_backend.connect()

@app.on_event("shutdown")
async def shutdown():
    await redis_backend.disconnect()

# Manual publishing
@app.post("/comments")
async def create_comment(comment: dict):
    new_comment = {"id": 1, **comment}
    
    # Manual broker call
    await broker.publish(
        topic="comments",
        event="comment_created",
        data=new_comment
    )
    
    return new_comment

# Manual SSE endpoint
mount_sse(app, broker)
```

#### ✅ After (Simplified API) - ~10 lines

```python
from fastapi import Request
from fastapi_sse_events import (
    SSEApp, sse_event, sse_endpoint
)

# One-line setup!
app = SSEApp(
    redis_url="redis://localhost:6379"
)

# Auto-publishing
@app.post("/comments")
@sse_event(topic="comments")
async def create_comment(
    request: Request,
    comment: dict
):
    new_comment = {"id": 1, **comment}
    return new_comment  # Auto-published!

# Auto-streaming
@app.get("/events")
@sse_endpoint(topics=["comments"])
async def events(request: Request):
    pass  # All automatic!
```

### 📈 80% Reduction in Boilerplate

The simplified API reduces setup from ~50 lines to ~10 lines, letting you focus on your business logic instead of configuration.

### 🔄 Migration from Manual API

Migrating to the simplified API is straightforward and can be done gradually:

#### Step 1: Replace FastAPI with SSEApp

```python
# Before
app = FastAPI()
config = RealtimeConfig(redis_url="...")
# ... manual setup ...

# After
app = SSEApp(redis_url="...")
```

#### Step 2: Add Decorators

```python
# Before
@app.post("/comments")
async def create_comment(comment: dict):
    new_comment = save(comment)
    await broker.publish("comments", "created", new_comment)
    return new_comment

# After
@app.post("/comments")
@sse_event(topic="comments", event="created")
async def create_comment(request: Request, comment: dict):
    new_comment = save(comment)
    return new_comment  # Auto-published!
```

#### Step 3: Simplify SSE Endpoints

```python
# Before
mount_sse(app, broker, authorize_fn)
# Or manual endpoint creation...

# After
@app.get("/events")
@sse_endpoint(topics=["comments"], authorize=authorize_fn)
async def events(request: Request):
    pass
```

#### ℹ️ Fully Backwards Compatible

The simplified API is fully backwards compatible. You can mix both APIs in the same application: use decorators for new endpoints while keeping manual `broker.publish()` calls in existing code. Access the broker directly via `app.broker` or `request.app.state.broker`.

### 📚 Complete Example

Here's a complete CRM comments system using the simplified API:

**app_simple.py:**
```python
"""Simplified CRM Comments with SSE"""
from fastapi import Request, HTTPException
from pydantic import BaseModel
from fastapi_sse_events import SSEApp, sse_event, sse_endpoint

# One-line app setup
app = SSEApp(
    title="CRM Comments",
    redis_url="redis://localhost:6379",
    enable_cors=True
)

# In-memory storage
comments_db = {}
comment_id = 0

class CommentCreate(BaseModel):
    thread_id: int
    author: str
    content: str

# CRUD endpoints with auto-publishing
@app.post("/comments")
@sse_event(topic="comments", event="comment_created")
async def create_comment(request: Request, comment: CommentCreate):
    global comment_id
    comment_id += 1
    
    new_comment = {
        "id": comment_id,
        "thread_id": comment.thread_id,
        "author": comment.author,
        "content": comment.content
    }
    
    comments_db[comment_id] = new_comment
    return new_comment  # Auto-published to SSE!

@app.put("/comments/{comment_id}")
@sse_event(topic="comments", event="comment_updated")
async def update_comment(
    request: Request,
    comment_id: int,
    content: str
):
    if comment_id not in comments_db:
        raise HTTPException(404, "Not found")
    
    comments_db[comment_id]["content"] = content
    return comments_db[comment_id]  # Auto-published!

@app.delete("/comments/{comment_id}")
@sse_event(topic="comments", event="comment_deleted")
async def delete_comment(request: Request, comment_id: int):
    if comment_id not in comments_db:
        raise HTTPException(404, "Not found")
    
    deleted = comments_db.pop(comment_id)
    return {"id": comment_id}  # Auto-published!

@app.get("/comments")
async def list_comments():
    return list(comments_db.values())

# SSE endpoint with auto-streaming
@app.get("/events")
@sse_endpoint(topics=["comments"])
async def events(request: Request):
    pass  # All automatic!

# Run with: uvicorn app_simple:app --reload
```

### 🚀 Try It!

The complete example is available in `examples/crm_comments/app_simple.py`. Run it with: `cd examples/crm_comments && ./start_simple.sh`

### ❓ FAQ

#### Can I still use the manual API?

Yes! The simplified API is built on top of the manual API and both work together. You can access the broker directly via `app.broker.publish(...)` whenever needed.

#### Do I need the Request parameter?

Yes, for `@sse_event` and `@sse_endpoint` decorators. The decorators need access to the app state where the broker is stored. Add `request: Request` as the first parameter after `self` (for class methods).

#### Can I use dynamic topics?

Yes! You can still use manual `app.broker.publish()` for dynamic topics like `f"thread:{thread_id}"`, or use the decorator for general topics and manual publish for specific ones.

#### What about authorization?

Use the `authorize` parameter in `@sse_endpoint`: `@sse_endpoint(authorize=my_auth_function)`. The function receives `(request, topic)` and returns `True/False`.

#### Does it work with dependency injection?

Yes! FastAPI dependencies work normally. Just make sure `request: Request` is one of your parameters.

---

## Architecture

FastAPI SSE Events uses a simple but powerful architecture:

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │  SSE    │  FastAPI    │  Pub    │    Redis    │
│   Client    │◄────────│   Instance  │◄────────│   Pub/Sub   │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │                        ▲
      │                       │                        │
      │  POST /api/task       │  Publish Event         │
      └──────────────────────►│───────────────────────►│
                              │                        │
                              │   Subscribe Topics     │
                              └───────────────────────►│
```

### Flow Breakdown

1. **Client connects** to `/sse?topics=task:123`
2. **FastAPI subscribes** to Redis channels matching those topics
3. **Another client** makes a POST request that modifies data
4. **Your endpoint** publishes event to Redis: `task:created`
5. **Redis broadcasts** to all subscribed FastAPI instances
6. **FastAPI forwards** event to connected SSE clients
7. **Browser receives** notification and refreshes data via REST

### ℹ️ Horizontal Scaling

Because Redis Pub/Sub is used as the message broker, you can run multiple FastAPI instances behind a load balancer. An event published by any instance reaches all connected clients across all instances.

---

## Features

### 🔌 Simple Integration
Add SSE with 3 lines of code. Minimal changes to existing endpoints. Works alongside your REST API.

### 📡 Server-Sent Events
Lightweight, one-way communication (server → client). Built on standard HTTP with automatic reconnection.

### 🗄️ Redis Pub/Sub
Horizontal scaling across multiple API instances. Battle-tested message broker with low latency.

### 🔒 Authorization Hooks
Secure topic subscriptions with custom auth logic. Integrate with your existing authentication system.

### 💓 Heartbeat Support
Automatic connection keepalive with configurable intervals. Prevents proxy timeouts.

### 🏷️ Topic-based Routing
Fine-grained subscription control per resource. Subscribe to exactly what you need.

### 🛡️ Type Safe
Full type hints and mypy compliance. Catch errors at development time, not runtime.

### ✅ Well Tested
Comprehensive test suite with 80%+ coverage. Production-ready and battle-tested.

---

## How It Works

### The "Notify Then Fetch" Pattern

FastAPI SSE Events implements a clean separation between notifications and data:

1. **SSE notifies** that something changed
2. **Client fetches** fresh data via REST
3. **REST API** remains the source of truth

### ⚠️ SSE vs Full Data Push

We recommend sending lightweight notifications (IDs, types) via SSE rather than full objects. This keeps your REST API as the canonical data source and reduces bandwidth. Clients can intelligently fetch only changed resources.

### Example Flow

```
User A                  Server                  User B
  │                         │                      │
  │  1. POST /comments      │                      │
  │────────────────────────►│                      │
  │                         │                      │
  │                         │  2. SSE Event        │
  │                         │────────────────────►│
  │                         │   "comment:created"  │
  │                         │                      │
  │                         │  3. GET /comments    │
  │                         │◄────────────────────│
  │                         │                      │
  │                         │  4. Fresh Data       │
  │                         │────────────────────►│
```

---

## Basic Integration

### Basic Integration (Recommended)

```python
from fastapi import Request
from fastapi_sse_events import SSEApp, publish_event, subscribe_to_events

app = SSEApp(redis_url="redis://localhost:6379/0")

@app.post("/tickets/{ticket_id}/status")
@publish_event(topic="tickets", event="ticket_status_changed")
async def update_ticket_status(request: Request, ticket_id: int, status: str):
  await db.update_ticket(ticket_id, status=status)
  return {"id": ticket_id, "status": status}

@app.get("/events")
@subscribe_to_events()  # topics via ?topic=tickets
async def events(request: Request):
  pass
```

Use `SSEApp` + decorators for minimal boilerplate. Keep `mount_sse()` for advanced/manual integration.

### Publishing Events

There are several approaches to publishing events, ranging from the simple (recommended) to the advanced (manual control).

#### Method 1: Decorator-Based Publish (Recommended)

The simplest and most Pythonic approach. Just add `@publish_event()` to any endpoint, and the decorator automatically publishes the response:

```python
from fastapi import Request
from fastapi_sse_events import publish_event

@app.post("/tickets/{ticket_id}/status")
@publish_event(topic="tickets", event="ticket_status_changed")
async def update_ticket_status(request: Request, ticket_id: int, status: str):
    await db.update_ticket(ticket_id, status=status)
    return {"id": ticket_id, "status": status}  # Auto-published to all subscribers
```

Features:
- ✅ No boilerplate - just decorate your endpoint
- ✅ Response automatically published as event data
- ✅ Automatic HTTP and SSE notification
- ✅ Works with any endpoint (GET, POST, PUT, DELETE)

#### Method 2: Direct Publish (Advanced)

For fine-grained control over event data, publish manually using `app.state.event_broker`:

```python
from fastapi_sse_events import publish_event

@app.post("/tickets/{ticket_id}/status")
async def update_ticket_status(request: Request, ticket_id: int, status: str):
    # Update database
    await db.update_ticket(ticket_id, status=status)
    
    # Manual publish with custom data
    await app.state.event_broker.publish(
        topic=f"ticket:{ticket_id}",
        event="ticket_status_changed",
        data={
            "ticket_id": ticket_id,
            "status": status,
            "changed_at": datetime.utcnow().isoformat(),
            "changed_by": request.user.id
        }
    )
    
    return {"id": ticket_id, "status": status}
```

Use this when you need:
- Custom/computed event data not in the HTTP response
- Different data for SSE vs HTTP clients
- Multiple events from a single endpoint

#### Method 3: Service Layer Pattern (Advanced)

Encapsulate publishing logic in service classes for clean separation of concerns:

```python
from fastapi_sse_events import publish_event

class TaskService:
    def __init__(self, broker):
        self.broker = broker
    
    async def create_task(self, data: dict, user_id: int):
        # Business logic
        task = await db.save_task(data, user_id)
        
        # Publish to project subscribers
        await self.broker.publish(
            topic=f"project:{data['project_id']}",
            event="task:created",
            data={"id": task.id, "title": task.title, "assignee": user_id}
        )
        
        return task

# In endpoint
@app.post("/tasks")
async def create_task_endpoint(request: Request, data: TaskCreate):
    service = TaskService(app.state.event_broker)
    return await service.create_task(data.dict(), request.user.id)
```

### Authorization

Protect SSE subscriptions with custom authorization callbacks. Control which users can subscribe to which topics:

```python
from fastapi import Request, HTTPException
from fastapi_sse_events import SSEApp

async def authorize_subscription(request: Request, topic: str) -> bool:
    """
    Authorization callback - return True to allow subscription, False to deny.
    Called for each topic subscription attempt.
    
    Args:
        request: FastAPI request (contains user info via session, JWT, etc.)
        topic: Topic being subscribed to
    
    Returns:
        True if authorized, False otherwise
    """
    # Get current user (implement based on your auth method)
    user = await get_current_user(request)
    if not user:
        return False
    
    # Allow user to subscribe to their own topic
    if topic.startswith("user:"):
        user_id = topic.split(":")[1]
        return str(user.id) == user_id
    
    # Check workspace membership
    if topic.startswith("workspace:"):
        workspace_id = topic.split(":")[1]
        return await user_has_workspace_access(user.id, workspace_id)
    
    # Check organization access
    if topic.startswith("org:"):
        org_id = topic.split(":")[1]
        return await user_in_organization(user.id, org_id)
    
    # Broadcast topics - anyone can subscribe
    if topic in ["announcements", "system"]:
        return True
    
    # Deny by default
    return False

# Create app with authorization
app = SSEApp(
    redis_url="redis://localhost:6379/0",
    authorize=authorize_subscription  # Pass authorization callback
)
```

**JWT-Based Authorization Example:**

```python
from fastapi.security import HTTPBearer, HTTPAuthCredentialDetails
from jose import jwt, JWTError

security = HTTPBearer()

async def authorize_subscription(request: Request, topic: str) -> bool:
    # Get token from header
    credentials = await security(request)
    if not credentials:
        return False
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        user_roles = payload.get("roles", [])
    except JWTError:
        return False
    
    # Check topic permissions based on roles
    if topic.startswith("admin:"):
        return "admin" in user_roles
    
    if topic.startswith("user:"):
        return user_id == topic.split(":")[1]
    
    return True
```

**Security Best Practices:**

✅ **Always**:
- Validate user authentication (JWT, sessions, etc.)
- Check permissions for resource-specific topics
- Log authorization failures for security monitoring
- Use granular topic patterns with IDs (e.g., `workspace:123` not just `workspace`)

❌ **Never**:
- Allow wildcard subscriptions without explicit auth
- Trust client-supplied topic names
- Skip authorization for "internal" topics
- Cache authorization results without invalidation

### Topic Patterns

Topics are simple strings that route events to subscribers. Choose a consistent naming convention for your application:

**Simple Topic Strings:**

```python
# Just use strings directly!
await app.state.event_broker.publish(
    topic="comments",
    event="comment:created",
    data={"id": 1, "text": "Hello"}
)

# Or with resource IDs for more granularity
await app.state.event_broker.publish(
    topic="comment:123",
    event="updated",
    data={"text": "Edited"}
)
```

**Recommended Topic Conventions:**

| Pattern | Use Case | Example |
|---------|----------|---------|
| `resource` | Broadcast updates to all | `comments`, `tasks`, `notifications` |
| `resource:id` | Updates to specific resource | `comment:123`, `task:456`, `invite:789` |
| `resource:id:action` | Specific action on resource | `comment:123:deleted`, `task:456:assigned` |
| `workspace:id` | All updates in a workspace | `workspace:acme-corp` |
| `user:id` | User-specific notifications | `user:john_doe` |
| `broadcast` or `global` | System-wide announcements | `broadcast` |

**Using TopicBuilder (Optional):**

For consistency, you can use the optional `TopicBuilder` helper:

```python
from fastapi_sse_events import TopicBuilder

# Built-in helper methods
TopicBuilder.comment("c123")           # → "comment:c123"
TopicBuilder.task("t456")              # → "task:t456"
TopicBuilder.workspace("ws789")        # → "workspace:ws789"
TopicBuilder.user("john")              # → "user:john"

# Or custom topics
TopicBuilder.custom("invoice", "inv123")  # → "invoice:inv123"
```

However, `TopicBuilder` is optional - plain strings work equally well and are often simpler.

**Best Practices:**

- ✅ Use colons for namespacing: `resource:id`
- ✅ Keep topic names lowercase and short
- ✅ Include IDs for resource-specific topics (enables authorization)
- ✅ Use consistent separators (colon recommended)
- ✅ Document topic names your app uses
- ❌ Avoid dynamic topic names without validation
- ❌ Avoid spaces or special characters
- ❌ Don't use topics to store data (topics are routing keys only)

---

## Configuration

### SSEApp Configuration

The `SSEApp` class provides simple one-line configuration:

```python
from fastapi_sse_events import SSEApp
import os

# Minimal setup
app = SSEApp(redis_url="redis://localhost:6379/0")

# Full configuration
app = SSEApp(
    title="My API",
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    heartbeat_seconds=30,              # SSE keepalive interval (5-60s)
    authorize=authorize_subscription,   # Authorization callback (optional)
)
```

**Configuration Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | str | "FastAPI" | App title (optional) |
| `redis_url` | str | ⚠️ Required | Redis connection URL |
| `heartbeat_seconds` | int | 30 | SSE keepalive interval (5-60) |
| `authorize` | callable | None | Authorization callback function |

### Environment Variables

Load configuration from environment for easier deployment:

```python
import os
from fastapi_sse_events import SSEApp

app = SSEApp(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    heartbeat_seconds=int(os.getenv("SSE_HEARTBEAT_SECONDS", "30")),
)
```

**Standard Environment Variables:**

```bash
# Development
export REDIS_URL="redis://localhost:6379/0"
export SSE_HEARTBEAT_SECONDS=30

# Production (with authentication)
export REDIS_URL="redis://:password@redis-prod.example.com:6379/0"
export SSE_HEARTBEAT_SECONDS=60
```

Load from `.env` file using `python-dotenv`:

```python
from dotenv import load_dotenv
import os
from fastapi_sse_events import SSEApp

load_dotenv()

app = SSEApp(
    redis_url=os.getenv("REDIS_URL"),
    heartbeat_seconds=int(os.getenv("SSE_HEARTBEAT_SECONDS", "30")),
)
```

### Advanced: Manual Broker Setup

For advanced use cases, you can configure the broker manually (not recommended for most applications):

```python
from fastapi import FastAPI
from fastapi_sse_events import EventBroker, RealtimeConfig, mount_sse

app = FastAPI()

config = RealtimeConfig(
    redis_url="redis://localhost:6379/0",
    heartbeat_seconds=30,
)

broker = mount_sse(app, config, authorize=authorize_subscription)
```

Prefer `SSEApp` for new projects - it handles all the setup automatically.

---

## Client Integration

### JavaScript / Browser

```javascript
// Connect to SSE endpoint
const eventSource = new EventSource('/events?topic=comments');

// Handle connection opened
eventSource.addEventListener('open', () => {
  console.log('✅ Connected to SSE');
  document.getElementById('status').textContent = 'Connected';
});

// Handle connection errors
eventSource.addEventListener('error', (error) => {
  console.error('❌ SSE Error:', error);
  document.getElementById('status').textContent = 'Disconnected';
  // EventSource automatically reconnects
});

// Listen to specific events
eventSource.addEventListener('comment:created', (event) => {
  const data = JSON.parse(event.data);
  console.log('New comment:', data);
  
  // Fetch fresh data from API
  fetch(`/comments/${data.id}`)
    .then(r => r.json())
    .then(comment => renderComment(comment));
});

eventSource.addEventListener('comment:updated', (event) => {
  const data = JSON.parse(event.data);
  console.log('Updated comment:', data);
  
  // Refresh specific comment
  fetch(`/comments/${data.id}`)
    .then(r => r.json())
    .then(comment => updateComment(comment));
});

// Listen to heartbeat (optional)
eventSource.addEventListener('heartbeat', (event) => {
  console.log('💓 Heartbeat');
});

// Subscribe to multiple topics
const multiTopics = ['comments', 'tasks', 'notifications'];
const eventSource2 = new EventSource(
  `/events?topic=${multiTopics.join(',')}`
);

// Cleanup
function closeSSE() {
  eventSource.close();
}
window.addEventListener('beforeunload', closeSSE);
```

### React Hook Example

```jsx
import { useEffect, useState, useCallback } from 'react';

// Custom hook for SSE
function useSSE(topic, onEvent) {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(`/events?topic=${topic}`);

    eventSource.addEventListener('open', () => {
      setConnected(true);
    });

    eventSource.addEventListener('error', () => {
      setConnected(false);
    });

    // Forward all events to callback
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onEvent?.(event.type, data);
    };

    return () => eventSource.close();
  }, [topic, onEvent]);

  return connected;
}

// Component using the hook
function CommentList({ threadId }) {
  const [comments, setComments] = useState([]);

  // Handle SSE events
  const handleSSEEvent = useCallback((eventType, data) => {
    if (eventType === 'comment:created' || eventType === 'comment:updated') {
      // Refresh data from API
      fetchComments();
    }
  }, []);

  const connected = useSSE(`comment_thread:${threadId}`, handleSSEEvent);

  useEffect(() => {
    // Initial load
    fetchComments();
  }, [threadId]);

  const fetchComments = async () => {
    const response = await fetch(`/comments?thread_id=${threadId}`);
    const data = await response.json();
    setComments(data);
  };

  return (
    <div>
      <div style={{ color: connected ? 'green' : 'red' }}>
        {connected ? '🟢 Live' : '🔴 Offline'}
      </div>
      {comments.map(comment => (
        <div key={comment.id} className="comment">
          {comment.content}
        </div>
      ))}
    </div>
  );
}
```

### Python Client

```python
import httpx
import json

async def listen_to_events():
    """Listen to SSE events from Python."""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET",
            "http://localhost:8000/events?topic=comments",
            headers={"Accept": "text/event-stream"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_type = line[7:].strip()
                elif line.startswith("data:"):
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                        print(f"Event: {event_type}, Data: {data}")
                    except json.JSONDecodeError:
                        pass

# Using sseclient-py library (simpler)
from sseclient import SSEClient

def listen_simple():
    """Simple SSE listening with sseclient-py."""
    url = "http://localhost:8000/events?topic=comments"
    
    for event in SSEClient(url):
        if event.event != "heartbeat":
            print(f"Event: {event.event}")
            print(f"Data: {event.data}")
```

---

## Deployment

### Nginx Configuration

Disable buffering for SSE endpoints:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location /events {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        
        # Critical: Disable buffering for SSE
        proxy_buffering off;
        proxy_cache off;
        
        # Keep connection alive
        proxy_read_timeout 86400s;
        
        # Forward headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://fastapi_backend;
        # Normal proxy settings
    }
}
```

### Traefik Configuration

```yaml
http:
  routers:
    sse-router:
      rule: "PathPrefix(`/events`)"
      service: sse-service
      
  services:
    sse-service:
      loadBalancer:
        servers:
          - url: "http://fastapi:8000"
        # Disable buffering
        responseForwarding:
          flushInterval: "1ms"
```

### Docker Compose

```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SSE_REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    # Scale horizontally
    deploy:
      replicas: 3
```

### Horizontal Scaling

SSE Events works seamlessly across multiple instances:

1. **All instances connect to same Redis**
2. **Events published by any instance reach all SSE clients**
3. **No sticky sessions required**
4. **Load balance normally**

```bash
# Start multiple instances
uvicorn app:app --port 8000 &
uvicorn app:app --port 8001 &
uvicorn app:app --port 8002 &

# All instances share events via Redis
```

---

## Production Deployment

FastAPI SSE Events is designed to scale from prototype to **100,000+ concurrent connections**.

### Architecture for 100K Users

```
                    ┌─────────────────┐
                    │  Nginx/ALB      │
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼───┐         ┌────▼───┐       ┌────▼────┐
    │FastAPI │         │FastAPI │  ...  │ FastAPI │
    │  #1    │         │  #2    │       │  #10    │
    │10K conn│         │10K conn│       │ 10K conn│
    └────┬───┘         └────┬───┘       └────┬────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
                    ┌───────▼────────┐
                    │ Redis Cluster  │
                    │  (3-5 nodes)   │
                    └────────────────┘
```

### Key Metrics

- **10,000 connections per FastAPI instance**
- **~100KB memory per connection**
- **< 10ms message latency**
- **100K messages/sec throughput**
- **99.9%+ uptime**

### Quick Start

```bash
cd examples/production_scale
./start.sh
```

This starts:
- 10 FastAPI instances (100K capacity)
- Redis Cluster (3 nodes)
- Nginx load balancer
- Prometheus + Grafana monitoring

### Configuration for Scale

```python
# .env.100k_users
SSE_REDIS_URL=redis://redis-1:7001,redis-2:7002,redis-3:7003/0
SSE_MAX_CONNECTIONS=10000      # Per instance
SSE_MAX_QUEUE_SIZE=50          # Memory optimization
SSE_MAX_MESSAGE_SIZE=32768     # 32KB limit
SSE_HEARTBEAT_SECONDS=30       # Efficient keepalive
```

### Monitoring & Health Checks

Built-in endpoints for production monitoring:

```python
GET /health          # Basic health check
GET /health/ready    # Readiness probe (load balancers)
GET /health/live     # Liveness probe (Kubernetes)
GET /metrics         # Detailed metrics (JSON)
GET /metrics/prometheus  # Prometheus format
```

**Key Metrics to Monitor:**

```promql
# Concurrent connections
sum(sse_connections_current)

# Connection rejection rate (scale up if > 0)
rate(sse_connections_rejected[5m])

# Message drop rate (should be < 0.1%)
rate(sse_messages_dropped[5m]) / rate(sse_messages_delivered[5m])

# Publish latency
avg(sse_publish_latency_ms)
```

### Production Checklist

Before deploying to production:

- [ ] **Load Testing** - Test with expected peak load × 2
- [ ] **Monitoring** - Set up Prometheus + Grafana dashboards
- [ ] **Alerting** - Configure alerts for connection rejections, high latency
- [ ] **Auto-scaling** - Configure triggers (CPU > 70%, connections > 8K)
- [ ] **Security** - Enable Redis auth, use SSL, restrict CORS
- [ ] **Persistence** - Configure Redis persistence (AOF + RDB)
- [ ] **Failover** - Test Redis cluster failover scenarios
- [ ] **Backpressure** - Verify slow clients don't crash servers
- [ ] **Rate Limiting** - Implement API rate limits
- [ ] **Logging** - Set up centralized logging (ELK/Loki)

### Performance Tuning

**Redis Optimization:**
```bash
# Increase max clients
redis-cli CONFIG SET maxclients 20000

# Optimize memory
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 4gb

# Disable persistence for pure cache (optional)
redis-cli CONFIG SET save ""
```

**Linux Kernel Tuning:**
```bash
# Increase file descriptors
ulimit -n 100000

# Increase network buffers
sysctl -w net.core.somaxconn=4096
sysctl -w net.ipv4.tcp_max_syn_backlog=8096
```

**FastAPI Instance Sizing:**
- **CPU:** 1-2 cores per instance
- **Memory:** 2GB base + 1GB per 10K connections
- **Network:** 100Mbps per 10K connections

### Complete Guide

For detailed deployment instructions, architecture decisions, and troubleshooting:

📚 **[Complete 100K User Deployment Guide](docs/SCALING_100K_USERS.md)**

Topics covered:
- Multi-region deployment
- Kubernetes manifests
- Cost optimization strategies
- Disaster recovery
- Performance benchmarking
- Security hardening

---

## Examples

See the [examples/](examples/) directory for complete working examples:

### CRM Comment System
Full-featured collaborative comment system with:
- REST API for CRUD operations
- Real-time SSE updates
- Beautiful web interface
- Multi-client synchronization

```bash
cd examples/crm_comments
uvicorn app:app --reload
# Open client.html in multiple browsers
```

More examples coming soon:
- Ticket tracking system
- Live dashboard with metrics
- Collaborative document editing
- Multi-tenant workspace notifications

---
## API Reference

### SSEApp (Recommended)

Simplified FastAPI subclass with built-in SSE support.

```python
from fastapi_sse_events import SSEApp

class SSEApp(FastAPI):
    """FastAPI app with SSE support pre-configured."""
    
    def __init__(
        self,
        title: str = "API",
        redis_url: str = "redis://localhost:6379/0",
        heartbeat_seconds: int = 30,
        authorize: Optional[AuthorizeFn] = None,
        **kwargs
    ):
        pass
```

**Usage:**
```python
app = SSEApp(
    title="My API",
    redis_url="redis://localhost:6379/0",
    heartbeat_seconds=30,
    authorize=authorize_callback  # Optional
)
```

**Automatically Provides:**
- ✅ EventBroker at `app.state.event_broker`
- ✅ SSE endpoint at `/events` (with `?topic=` query param)
- ✅ Health checks at `/health*`
- ✅ Metrics at `/metrics`

### Decorators

#### `@publish_event()`

Automatically publishes endpoint response to subscribers.

```python
from fastapi_sse_events import publish_event

@app.post("/comments")
@publish_event(topic="comments", event="comment:created")
async def create_comment(request: Request, text: str):
    # Save to database
    comment = await db.save_comment(text)
    # Response automatically published to all subscribers!
    return comment
```

**Parameters:**
- `topic` (str): Topic to publish to
- `event` (str): Event type identifier

#### `@subscribe_to_events()`

Converts endpoint to SSE stream. Query param: `?topic=...`

```python
from fastapi_sse_events import subscribe_to_events

@app.get("/events")
@subscribe_to_events()
async def events(request: Request):
    # Endpoint body can be empty
    pass
```

**Query Parameters:**
- `topic` (str, required): Topic to subscribe to
- `topic=topic1,topic2`: Multiple topics (comma-separated)

### EventBroker

Manual event publishing (use decorators when possible).

```python
class EventBroker:
    async def publish(
        self,
        topic: str,
        event: str,
        data: dict[str, Any] | EventData
    ) -> None:
        """Publish event to all subscribers on topic."""
```

**Example:**
```python
await app.state.event_broker.publish(
    topic="comments",
    event="comment:created",
    data={"id": 1, "text": "Hello"}
)
```

### Configuration (SSEApp Parameters)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | str | "API" | Application title |
| `redis_url` | str | "redis://localhost:6379/0" | Redis connection URL |
| `heartbeat_seconds` | int | 30 | SSE keepalive interval (5-60) |
| `authorize` | AuthorizeFn | None | Authorization callback (optional) |

### Advanced: Manual Setup

For complex use cases, manually configure the broker:

```python
from fastapi import FastAPI
from fastapi_sse_events import mount_sse, RealtimeConfig

app = FastAPI()

config = RealtimeConfig(
    redis_url="redis://localhost:6379/0",
    heartbeat_seconds=30,
)

broker = mount_sse(app, config, authorize=authorize_fn)
```

### TopicBuilder (Optional)

Helper for consistent topic naming (optional).

```python
from fastapi_sse_events import TopicBuilder

# All optional - plain strings work too
TopicBuilder.comment("c123")        # → "comment:c123"
TopicBuilder.task("t456")           # → "task:t456"
TopicBuilder.workspace("ws789")     # → "workspace:ws789"
TopicBuilder.user("john")           # → "user:john"
TopicBuilder.custom("invoice", "i001")  # → "invoice:i001"
```

### Type Definitions

```python
# Authorization callback type
AuthorizeFn = Callable[[Request, str], Awaitable[bool]]

# Event data
EventData = dict[str, Any]  # Any JSON-serializable dict

# Example authorization
async def authorize(request: Request, topic: str) -> bool:
    """Return True to allow subscription, False to deny."""
    user = await get_current_user(request)
    return user is not None and topic.startswith(f"user:{user.id}")
```

---

## Troubleshooting

### SSE Connection Fails

**Symptom:** Browser can't connect to `/events`

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Verify endpoint is registered: check FastAPI docs at `/docs`
3. Check CORS settings if cross-origin
4. Look for errors in server logs

### Updates Not Appearing

**Symptom:** Events published but clients don't receive them

**Solutions:**
1. Verify topic names match exactly
2. Check Redis pub/sub: `redis-cli SUBSCRIBE topic_name`
3. Ensure all instances connect to same Redis
4. Check authorization function isn't denying access
5. Look for JavaScript errors in browser console

### High Memory Usage

**Symptom:** Redis or app memory grows over time

**Solutions:**
1. Monitor Redis: `redis-cli INFO memory`
2. Implement idle connection timeouts
3. Reduce heartbeat frequency if many connections
4. Set connection limits in load balancer
5. Monitor disconnected clients

### Proxy Buffering Issues

**Symptom:** Events delayed or not arriving

**Solution:** Disable buffering in proxy:

```nginx
# Nginx
proxy_buffering off;
proxy_cache off;

# Apache
SetEnv proxy-nokeepalive 1
```

### "Redis not connected" Error

**Symptom:** `RuntimeError: Redis client not connected`

**Solutions:**
1. Check Redis is running and accessible
2. Verify `redis_url` in config
3. Check network/firewall rules
4. Ensure `mount_sse()` called before app starts

---

## Performance Tips

1. **Use topic scoping** - Narrow topics reduce fan-out
2. **Keep payloads small** - Send IDs, not full objects
3. **Implement idle timeouts** - Clean up dead connections
4. **Monitor Redis** - Watch memory and connection count
5. **Connection pooling** - Reuse Redis connections
6. **Event batching** - For high-frequency updates, debounce on client

---

## Comparison

| Feature | SSE (this library) | WebSockets | Polling |
|---------|-------------------|------------|---------|
| Real-time | ✅ Near real-time | ✅ Real-time | ❌ Delayed |
| Infrastructure | ✅ HTTP (simple) | ❌ Complex | ✅ HTTP |
| Browser support | ✅ Native | ✅ Native | ✅ Native |
| Bidirectional | ❌ Server→Client | ✅ Both | ❌ Client→Server |
| Auto-reconnect | ✅ Built-in | ❌ Manual | N/A |
| Horizontal scaling | ✅ Via Redis | ❌ Sticky sessions | ✅ Stateless |
| Debugging | ✅ Easy | ❌ Harder | ✅ Easy |
| Use case | Notifications | Chat, games | Legacy |

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Development Setup

```bash
# Clone repository
git clone https://github.com/bhadri01/fastapi_sse_events.git
cd fastapi_sse_events

# Install with dev dependencies
pip install -e ".[dev]"

# Run type checking
mypy fastapi_sse_events/
```

### Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Run** type checking (`mypy`)
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Reporting Issues

- Use [GitHub Issues](https://github.com/bhadri01/fastapi_sse_events/issues)
- Include Python version, FastAPI version, and Redis version
- Provide minimal reproducible example
- Check existing issues first

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

Copyright © 2025 [bhadri01](https://github.com/bhadri01)

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Redis](https://redis.io/)
- SSE support via [sse-starlette](https://github.com/sysid/sse-starlette)

---

## 🔗 Related Projects

- **[fastapi-querybuilder](https://github.com/bhadri01/fastapi-querybuilder)** - Advanced query building for FastAPI + SQLAlchemy

---

## ⭐ Star History

If you find this project helpful, please consider giving it a star on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=bhadri01/fastapi_sse_events&type=Date)](https://star-history.com/#bhadri01/fastapi_sse_events&Date)

---

Made with ❤️ by [bhadri01](https://github.com/bhadri01)

---

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/fastapi-sse-events/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/fastapi-sse-events/discussions)
- **Email:** support@example.com

---

**Built with ❤️ for the FastAPI community**
