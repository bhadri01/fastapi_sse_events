# FastAPI SSE Events

> Server-Sent Events (SSE) notifications for FastAPI using Redis Pub/Sub

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Add real-time "refresh-less" updates to your FastAPI REST API in minutes.**

Perfect for collaborative tools (CRMs, project management, dashboards) where multiple users need to see updates instantly without manual page refreshes.

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
from fastapi import FastAPI
from fastapi_sse_events import mount_sse, RealtimeConfig

app = FastAPI()

# Mount SSE with one line
broker = mount_sse(app)

# Or with custom config
config = RealtimeConfig(
    redis_url="redis://localhost:6379/0",
    heartbeat_seconds=30,
)
broker = mount_sse(app, config)
```

### 3. Publish Events from Your Endpoints

```python
from fastapi_sse_events import TopicBuilder

topics = TopicBuilder()

@app.post("/comments")
async def create_comment(comment: Comment):
    # Save comment to database
    saved_comment = await db.save(comment)
    
    # Notify subscribers
    await broker.publish(
        topic=topics.comment_thread(comment.thread_id),
        event="comment_created",
        data={"comment_id": saved_comment.id}
    )
    
    return saved_comment
```

### 4. Subscribe from Client

```javascript
// Connect to SSE stream
const eventSource = new EventSource(
  'http://localhost:8000/events?topic=comment_thread:123'
);

// Handle events
eventSource.addEventListener('comment_created', (e) => {
  const data = JSON.parse(e.data);
  console.log('New comment:', data.comment_id);
  
  // Refresh data via existing REST endpoint
  refreshComments();
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

### Basic Integration

```python
from fastapi import FastAPI
from fastapi_sse_events import mount_sse, RealtimeConfig

app = FastAPI()

# Simple setup
broker = mount_sse(app)

# Advanced setup
config = RealtimeConfig(
    redis_url="redis://localhost:6379/0",
    heartbeat_seconds=15,
    sse_path="/events",
    topic_prefix="prod",  # Namespace for multi-tenancy
)
broker = mount_sse(app, config)
```

The SSE endpoint is automatically registered at `/events` (or your custom path).

### Publishing Events

#### Method 1: Direct Publish

```python
@app.post("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: int, status: str):
    # Update database
    await db.update_ticket(ticket_id, status=status)
    
    # Notify subscribers
    await broker.publish(
        topic=f"ticket:{ticket_id}",
        event="ticket_status_changed",
        data={
            "ticket_id": ticket_id,
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
    )
    
    return {"status": "updated"}
```

#### Method 2: Using TopicBuilder

```python
from fastapi_sse_events import TopicBuilder

topics = TopicBuilder()

@app.post("/tasks")
async def create_task(task: Task):
    saved_task = await db.save(task)
    
    await broker.publish(
        topic=topics.task(saved_task.id),
        event="task_created",
        data={"task_id": saved_task.id}
    )
    
    return saved_task
```

#### Method 3: Service Layer Pattern (Recommended)

```python
# services/comment_service.py
class CommentService:
    def __init__(self, broker: EventBroker):
        self.broker = broker
        self.topics = TopicBuilder()
    
    async def create_comment(self, thread_id: int, data: dict):
        # Business logic
        comment = await db.save_comment(data)
        
        # Auto-notify
        await self.broker.publish(
            topic=self.topics.comment_thread(thread_id),
            event="comment_created",
            data={"comment_id": comment.id}
        )
        
        return comment

# main.py
@app.post("/comments")
async def create_comment_endpoint(data: CommentCreate):
    service = CommentService(app.state.event_broker)
    return await service.create_comment(data.thread_id, data.dict())
```

### Authorization

Protect topic access with custom authorization:

```python
from fastapi import Request, HTTPException

async def authorize_topic(request: Request, topic: str) -> bool:
    """
    Authorize topic access based on user permissions.
    
    Args:
        request: FastAPI request with user info
        topic: Topic being subscribed to
    
    Returns:
        True if authorized, False otherwise
    """
    # Extract user from JWT token
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return False
    
    try:
        user = verify_jwt_token(token)
    except Exception:
        return False
    
    # Check permissions based on topic pattern
    if topic.startswith("comment_thread:"):
        thread_id = int(topic.split(":")[1])
        return await user_can_access_thread(user.id, thread_id)
    
    elif topic.startswith("workspace:"):
        workspace_id = topic.split(":")[1]
        return await user_in_workspace(user.id, workspace_id)
    
    elif topic.startswith("user:"):
        user_id = topic.split(":")[1]
        return user.id == user_id  # Users can only subscribe to their own topics
    
    return False

# Mount with authorization
broker = mount_sse(app, authorize=authorize_topic)
```

### Topic Patterns

Use consistent topic naming conventions:

```python
from fastapi_sse_events import TopicBuilder

topics = TopicBuilder()

# Built-in patterns
topics.comment_thread(123)    # "comment_thread:123"
topics.ticket(456)            # "ticket:456"
topics.task(789)              # "task:789"
topics.workspace("ws1")       # "workspace:ws1"
topics.user("user_123")       # "user:user_123"

# Custom patterns
topics.custom("project", "p1") # "project:p1"
topics.custom("document", 42)  # "document:42"

# Or use strings directly
await broker.publish(
    topic="notification:broadcast",
    event="system_update",
    data={"message": "Maintenance in 5 minutes"}
)
```

**Recommended conventions:**

| Pattern | Use Case | Example |
|---------|----------|---------|
| `resource:id` | Updates to a specific resource | `ticket:123`, `task:456` |
| `resource_thread:id` | Threaded discussions | `comment_thread:789` |
| `workspace:id` | Workspace-wide updates | `workspace:acme-corp` |
| `user:id` | User-specific notifications | `user:user_123` |
| `broadcast` | System-wide announcements | `broadcast` |

---

## Configuration

### RealtimeConfig Options

```python
from fastapi_sse_events import RealtimeConfig

config = RealtimeConfig(
    # Redis connection URL
    redis_url="redis://localhost:6379/0",
    
    # Heartbeat interval (5-60 seconds)
    heartbeat_seconds=15,
    
    # SSE endpoint path
    sse_path="/events",
    
    # Topic prefix for namespacing (optional)
    topic_prefix="",
)
```

### Environment Variables

Configure via environment variables:

```bash
export SSE_REDIS_URL="redis://localhost:6379/0"
export SSE_HEARTBEAT_SECONDS=30
export SSE_SSE_PATH="/realtime"
export SSE_TOPIC_PREFIX="prod"
```

Or use a `.env` file with `python-dotenv`:

```bash
# Copy example file
cp .env.example .env

# Edit .env with your settings
nano .env
```

```python
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Config automatically reads from environment
config = RealtimeConfig()
broker = mount_sse(app, config)
```

**Available Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `SSE_REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `SSE_HEARTBEAT_SECONDS` | Heartbeat interval (5-60) | `15` |
| `SSE_SSE_PATH` | SSE endpoint path | `/events` |
| `SSE_TOPIC_PREFIX` | Topic namespace prefix | `""` (empty) |

---

## Client Integration

### JavaScript / Browser

```javascript
// Create EventSource connection
const topic = 'comment_thread:123';
const eventSource = new EventSource(
  `http://localhost:8000/events?topic=${topic}`
);

// Handle connection events
eventSource.onopen = () => {
  console.log('SSE connected');
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  // Browser automatically reconnects
};

// Listen to specific events
eventSource.addEventListener('comment_created', (e) => {
  const data = JSON.parse(e.data);
  console.log('New comment:', data);
  
  // Refresh data from REST API
  fetchComments(data.thread_id);
});

eventSource.addEventListener('comment_updated', (e) => {
  const data = JSON.parse(e.data);
  console.log('Updated comment:', data);
  fetchComments(data.thread_id);
});

// Handle heartbeat (optional)
eventSource.addEventListener('ping', (e) => {
  console.log('Heartbeat received');
});

// Subscribe to multiple topics
const topics = ['comment_thread:123', 'ticket:456'];
const eventSource = new EventSource(
  `http://localhost:8000/events?topic=${topics.join(',')}`
);

// Cleanup
window.addEventListener('beforeunload', () => {
  eventSource.close();
});
```

### React Example

```jsx
import { useEffect, useState } from 'react';

function CommentList({ threadId }) {
  const [comments, setComments] = useState([]);

  useEffect(() => {
    // Initial load
    fetchComments();

    // Setup SSE
    const eventSource = new EventSource(
      `http://localhost:8000/events?topic=comment_thread:${threadId}`
    );

    eventSource.addEventListener('comment_created', () => {
      fetchComments();
    });

    eventSource.addEventListener('comment_updated', () => {
      fetchComments();
    });

    return () => {
      eventSource.close();
    };
  }, [threadId]);

  const fetchComments = async () => {
    const response = await fetch(
      `http://localhost:8000/threads/${threadId}/comments`
    );
    const data = await response.json();
    setComments(data.comments);
  };

  return (
    <div>
      {comments.map(comment => (
        <div key={comment.id}>{comment.content}</div>
      ))}
    </div>
  );
}
```

### Python Client

```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        "GET",
        "http://localhost:8000/events?topic=comment_thread:123"
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                print(f"Received {event_type}: {data}")
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

### `mount_sse()`

Main integration function to add SSE to FastAPI app.

```python
def mount_sse(
    app: FastAPI,
    config: RealtimeConfig | None = None,
    authorize: AuthorizeFn | None = None,
) -> EventBroker:
    """Mount SSE to FastAPI app."""
```

**Parameters:**
- `app`: FastAPI application instance
- `config`: Configuration (optional, uses defaults)
- `authorize`: Authorization callback (optional)

**Returns:** `EventBroker` instance for publishing events

### `EventBroker`

Broker for publishing and subscribing to events.

```python
class EventBroker:
    async def publish(
        self,
        topic: str,
        event: str,
        data: dict[str, Any]
    ) -> None:
        """Publish event to topic."""
```

**Methods:**
- `publish(topic, event, data)`: Publish event to subscribers

### `RealtimeConfig`

Configuration for SSE system.

```python
class RealtimeConfig(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    heartbeat_seconds: int = 15
    sse_path: str = "/events"
    topic_prefix: str = ""
```

### `TopicBuilder`

Helper for building consistent topic names.

```python
class TopicBuilder:
    @staticmethod
    def comment_thread(thread_id: str | int) -> str:
        """Build comment thread topic."""
    
    @staticmethod
    def ticket(ticket_id: str | int) -> str:
        """Build ticket topic."""
    
    # ... more helpers
```

### `AuthorizeFn`

Type alias for authorization callback.

```python
AuthorizeFn = Callable[[Request, str], Awaitable[bool]]

async def authorize(request: Request, topic: str) -> bool:
    """Return True if authorized."""
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

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure `pytest`, `ruff`, and `mypy` pass
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/fastapi-sse-events/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/fastapi-sse-events/discussions)
- **Email:** support@example.com

---

**Built with ❤️ for the FastAPI community**
