# Quick Start Example - Simplified API (Recommended)

This is the **RECOMMENDED** way to use **FastAPI SSE Events** - using the simplified decorator-based API.

## What's Included

- **app.py**: Minimal FastAPI application with simplified SSE using `SSEApp` and decorators
- Task management API (create, read, update, delete)
- Real-time browser client built into the app
- Redis Pub/Sub for multi-instance support
- **Zero boilerplate** - 75% less code than traditional approach

## Key Differences from Traditional Approach

| Feature | Simplified API (This) | Traditional API |
|---------|----------------------|-----------------|
| App Setup | `SSEApp()` | `FastAPI()` + `mount_sse()` |
| Event Publishing | `@publish_event` decorator | Manual `broker.publish()` calls |
| SSE Endpoint | `@subscribe_to_events` decorator | Manual streaming code |
| Code Lines | ~60 | ~150+ |
| Configuration | Automatic | Manual setup |
| CORS | Built-in | Manual setup |

## Prerequisites

- Python 3.10+
- Redis server running on `localhost:6379`

## Installation

```bash
pip install fastapi uvicorn fastapi-sse-events redis
```

## Running the Example

### 1. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or local Redis
redis-server
```

### 2. Run the FastAPI Application

```bash
uvicorn app:app --reload
```

The server will start at `http://localhost:8000`

### 3. Open in Browser

Visit: **http://localhost:8000**

You'll see a simple interface where you can:
- Create, update, and delete tasks
- See real-time SSE updates instantly
- View live event logs

## How It Works (3 Steps)

### Step 1: Create SSEApp (Auto-configuration)

```python
from fastapi_sse_events import SSEApp

app = SSEApp(
    title="My App",
    redis_url="redis://localhost:6379"
)
# That's it! Broker, Redis, and CORS are auto-configured
```

### Step 2: Use @publish_event Decorator

```python
from fastapi_sse_events import publish_event

@app.post("/tasks")
@publish_event(topic="tasks", event="task:created")
async def create_task(request: Request, task: Task):
    # Just return your data - decorator publishes automatically!
    return task
```

### Step 3: Use @subscribe_to_events Decorator

```python
from fastapi_sse_events import subscribe_to_events

@app.get("/events")
@subscribe_to_events()
async def events(request: Request):
    pass  # Decorator handles all SSE streaming!
```

## Code Comparison

### 🚀 Simplified Way (This Example)

```python
from fastapi_sse_events import SSEApp, publish_event, subscribe_to_events

app = SSEApp(redis_url="redis://localhost:6379")

@app.post("/comments")
@publish_event(topic="comments", event="created")
async def create_comment(request: Request, comment: dict):
    return comment

@app.get("/events")
@subscribe_to_events()
async def events(request: Request):
    pass
```

### 📚 Traditional Way (For Reference)

```python
from fastapi import FastAPI
from fastapi_sse_events import mount_sse, RealtimeConfig, TopicBuilder

app = FastAPI()
config = RealtimeConfig(redis_url="redis://localhost:6379")
mount_sse(app, config)

@app.post("/comments")
async def create_comment(comment: dict):
    await app.state.event_broker.publish(
        topic="comments",
        event="created",
        data=comment
    )
    return comment

@app.get("/events")
async def events(request: Request):
    # ... manual SSE setup code ...
```

## Testing with Multiple Browsers

1. Open the app in multiple tabs
2. Create a task in one tab
3. **Watch it appear instantly in all other tabs!**

Real-time sync without WebSockets or polling - just pure Server-Sent Events!

## Next Steps

- **Compare Approaches**: See `../crm_comments/app_simple.py` for traditional approach
- **Complex Example**: Check `../crm_comments/app.py` for authorization and advanced patterns
- **Production**: Review `../production_scale/` for Docker, Nginx, and performance tuning
- **Full Docs**: Read the [HTML documentation](../../docs/index.html) for all features

## API Reference

### Query Parameters for `/events`

```javascript
// Subscribe to single topic
const es = new EventSource('/events?topic=tasks');

// Subscribe to multiple topics (comma-separated)
const es = new EventSource('/events?topic=tasks,users');

// Use wildcards (if implementing custom topic routing)
const es = new EventSource('/events?topic=task:*');
```

### Available Decorators

- `@SSEApp()` - Auto-configured FastAPI with SSE support
- `@publish_event(topic, event, extract_data)` - Auto-publish endpoint responses
- `@subscribe_to_events(topics, authorize)` - SSE streaming endpoint

## Troubleshooting

### "Connection refused" - Redis not running?

```bash
redis-cli ping
# Should return: PONG
```

### Events not appearing in browser?

1. Open DevTools (F12) → Console tab
2. Check for JavaScript errors
3. Check Network tab → filter for `events` requests
4. Look at server logs for Python exceptions

### Want to see SSE in Network tab?

Open DevTools → Network → Create a task → You'll see `/events` connection stream updates!

## Learn More

- **Simplified API Decorators**: See [app.py](app.py) comments
- **Traditional Approach**: See `examples/crm_comments/app_simple.py`
- **Production Setup**: See `examples/production_scale/`
- **Full Documentation**: Open `docs/index.html` in browser
