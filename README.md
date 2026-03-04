# FastAPI SSE Events

> Server-Sent Events (SSE) notifications for FastAPI using Redis Pub/Sub

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/fastapi-sse-events.svg)](https://pypi.org/project/fastapi-sse-events/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/bhadri01/fastapi_sse_events/workflows/Tests/badge.svg)](https://github.com/bhadri01/fastapi_sse_events/actions)
[![codecov](https://codecov.io/gh/bhadri01/fastapi_sse_events/branch/main/graph/badge.svg)](https://codecov.io/gh/bhadri01/fastapi_sse_events)

**Add real-time "refresh-less" updates to your FastAPI REST API in minutes.**

Perfect for collaborative tools (CRMs, project management, dashboards) where multiple users need to see updates instantly without manual page refreshes.

---

## 📚 Documentation

- **[Full Documentation](https://bhadri01.github.io/fastapi_sse_events)** - Complete guide with examples
- **[PyPI Package](https://pypi.org/project/fastapi-sse-events/)** - Installation and releases
- **[GitHub Repository](https://github.com/bhadri01/fastapi_sse_events)** - Source code and issues
- **[Changelog](https://github.com/bhadri01/fastapi_sse_events/blob/main/CHANGELOG.md)** - Version history

---

## Table of Contents

- [Overview](#overview)
- [Why SSE?](#why-sse)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Usage Guide](#usage-guide)
  - [Basic Integration](#basic-integration)
  - [Publishing Events](#publishing-events)
  - [Authorization](#authorization)
  - [Topic Patterns](#topic-patterns)
- [Configuration](#configuration)
- [Client Integration](#client-integration)
- [Deployment](#deployment)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

**FastAPI SSE Events** enables near real-time notifications for REST-based applications without the complexity of WebSockets. Clients subscribe to Server-Sent Event streams for specific topics, receive lightweight notifications when data changes, then refresh data via existing REST endpoints.

### Key Features

- 🚀 **Simple Integration** - Add SSE with 3 lines of code, minimal changes to existing endpoints
- 📡 **Server-Sent Events** - Lightweight, one-way communication (server → client)
- 🔄 **Redis Pub/Sub** - Horizontal scaling across multiple API instances
- 🔐 **Authorization Hooks** - Secure topic subscriptions with custom auth logic
- 💓 **Heartbeat Support** - Automatic connection keepalive (configurable interval)
- 🎯 **Topic-based Routing** - Fine-grained subscription control per resource
- 🔧 **Type Safe** - Full type hints and mypy compliance
- ✅ **Well Tested** - Comprehensive test suite with 80%+ coverage

---

## Why SSE?

**Problem:** Traditional REST APIs require manual refresh to see updates from other users. This creates poor collaboration experiences and inefficient workflows.

**Why not WebSockets?** WebSockets are powerful but complex:
- Require separate infrastructure
- More difficult to debug
- Overkill for one-way notifications
- Don't work well with existing REST patterns

**SSE Solution:**
- Built on HTTP (works with existing infrastructure)
- Native browser support (`EventSource`)
- Automatic reconnection
- Perfect for "notify then fetch" pattern
- Keeps REST as source of truth

---

## Installation

```bash
pip install fastapi-sse-events
```

**Requirements:**
- Python 3.10+
- FastAPI
- Redis server

---

## Quick Start

### 1. Install and Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or use local Redis
redis-server
```

### 2. Add to Your FastAPI App

```python
from fastapi import Request
from fastapi_sse_events import SSEApp, publish_event, subscribe_to_events

app = SSEApp(
  title="My API",
  redis_url="redis://localhost:6379/0",
)

@app.get("/events")
@subscribe_to_events()
async def events(request: Request):
  pass
```

### 3. Publish Events from Your Endpoints

```python
@app.post("/comments")
@publish_event(topic="comments", event="comment_created")
async def create_comment(request: Request, comment: Comment):
  # Save comment to database
  saved_comment = await db.save(comment)
  return saved_comment  # Auto-published to SSE clients
```

### 4. Subscribe from Client

```javascript
// Connect to SSE stream
const eventSource = new EventSource('http://localhost:8000/events?topic=comments');

// Handle events
eventSource.addEventListener('comment_created', (e) => {
  const data = JSON.parse(e.data);
  console.log('Comment event:', data);

  // Notify-then-fetch pattern (recommended)
  fetch(`http://localhost:8000/comments/${data.id}`)
    .then(r => r.json())
    .then(renderComment);
});
```

**That's it!** Your app now has real-time updates.

---

## Core Concepts

### Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Client 1   │         │  Client 2   │         │  Client N   │
│ EventSource │         │ EventSource │         │ EventSource │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │        SSE Stream (/events?topic=...)        │
       └───────────────────────┼───────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  FastAPI Instance   │
                    │                     │
                    │  REST API + SSE     │
                    └──────────┬──────────┘
                               │
                               │ Pub/Sub
                    ┌──────────▼──────────┐
                    │   Redis Server      │
                    │                     │
                    │  Topic Channels     │
                    └─────────────────────┘
                               ▲
                               │ Pub/Sub
                    ┌──────────┴──────────┐
                    │  FastAPI Instance   │
                    │                     │
                    │  REST API + SSE     │
                    └─────────────────────┘
```

### How It Works

1. **Client** opens SSE connection: `GET /events?topic=comment_thread:123`
2. **Server** subscribes to Redis channel for that topic
3. **Another client** posts data via REST API
4. **Server** saves data and publishes event to Redis
5. **Redis** broadcasts to all subscribed FastAPI instances
6. **All clients** receive lightweight notification
7. **Clients** fetch fresh data via existing REST endpoints

### Event Flow

```
User Action → REST Endpoint → Save to DB → Publish Event → Redis Pub/Sub
                                                                ↓
Client ← SSE Stream ← FastAPI ← Redis Subscribe ← Redis Pub/Sub
  ↓
Fetch Updated Data ← REST Endpoint
```

---

## Usage Guide

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

# Run tests
pytest tests/ -v

# Run linting
ruff check fastapi_sse_events/ tests/ examples/
ruff format fastapi_sse_events/ tests/ examples/

# Run type checking
mypy fastapi_sse_events/
```

### Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Add tests** for new features
4. **Ensure** all tests pass (`pytest`)
5. **Run** linting and formatting (`ruff`)
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to the branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

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
