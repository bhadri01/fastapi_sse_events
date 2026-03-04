# Examples

This directory contains example applications demonstrating various use cases for `fastapi-sse-events`.

## Available Examples

### 1. Quickstart (`quickstart/`)
**Simple task management with real-time updates**

The simplest possible example using the decorator API. Perfect for learning the basics.

**Features:**
- Create, read, update, and delete tasks
- Real-time notifications when tasks change
- Single-file implementation
- In-memory storage (no database required)

**Run it:**
```bash
cd quickstart
uvicorn app:app --reload
# Open http://localhost:8000
```

Or use Make:
```bash
make example-quickstart
```

---

### 2. CRM Comments (`crm_comments/`)
**Collaborative comment threads with real-time updates**

A realistic CRM-style application with multiple threads and user permissions.

**Features:**
- Multiple comment threads (like tickets/deals)
- Real-time comment updates
- User-specific authorization
- Topic-based subscriptions per thread
- Professional UI with dark mode
- Multiple implementation variants (simple vs. full-featured)

**Run it:**
```bash
cd crm_comments
./start.sh
# Open http://localhost:8000
```

**Variants:**
- `app.py` - Full-featured with authorization
- `app_simple.py` - Simplified version without auth
- `app_simple_new.py` - Latest simplified version

---

### 3. Production Scale (`production_scale/`)
**Production-ready deployment with monitoring**

Complete production setup with horizontal scaling, load balancing, and monitoring.

**Features:**
- Docker Compose orchestration
- Multiple FastAPI instances (horizontal scaling)
- Nginx load balancing
- Prometheus metrics
- Redis Pub/Sub for cross-instance messaging
- Load testing with Locust
- Health check endpoints

**Run it:**
```bash
cd production_scale
docker-compose up
# Open http://localhost (Nginx)
# Prometheus: http://localhost:9090
```

**Load Testing:**
```bash
# Install locust
pip install -r load_test_requirements.txt

# Run load test
locust -f load_test.py --host http://localhost
# Open http://localhost:8089
```

---

## Quick Reference

### Architecture Pattern

All examples follow the same pattern:

```python
# 1. Setup SSE
from fastapi_sse_events import SSEApp

app = SSEApp(redis_url="redis://localhost:6379")

# 2. Publish events from endpoints
@app.post("/items")
@publish_event(topic="items", event="created")
async def create_item(request: Request, item: Item):
    saved_item = save_item(item)
    return saved_item  # Auto-published to subscribers

# 3. Client subscribes to SSE stream
# GET /events?topic=items
```

### Frontend Integration

All examples include JavaScript clients using `EventSource`:

```javascript
const eventSource = new EventSource('/events?topic=items');

eventSource.addEventListener('created', (e) => {
    const data = JSON.parse(e.data);
    // Fetch updated data via REST
    refreshItems();
});
```

---

## Requirements

### All Examples
- Python 3.10+
- FastAPI
- Redis server

### Production Example
- Docker & Docker Compose
- (Optional) Prometheus for monitoring

---

## Running Examples

### Option 1: Direct execution
```bash
cd <example-directory>
uvicorn app:app --reload
```

### Option 2: Using Make
```bash
# From project root
make example-quickstart
make example-crm
```

### Option 3: Docker (production example only)
```bash
cd production_scale
docker-compose up
```

---

## Learning Path

**Recommended order:**

1. **Quickstart** - Learn the basics (5 minutes)
2. **CRM Comments** - See a realistic application (15 minutes)
3. **Production Scale** - Understand deployment (30 minutes)

---

## Creating Your Own Example

Want to add a new example? Follow this structure:

```
your_example/
├── app.py                 # Main application
├── README.md             # Example-specific docs
├── requirements.txt      # Dependencies
├── start.sh             # Startup script
└── client.html          # (Optional) Frontend client
```

Then submit a PR!

---

## Need Help?

- **Documentation:** https://bhadri01.github.io/fastapi_sse_events
- **Issues:** https://github.com/bhadri01/fastapi_sse_events/issues
- **Discussions:** https://github.com/bhadri01/fastapi_sse_events/discussions

---

Happy coding! 🚀
