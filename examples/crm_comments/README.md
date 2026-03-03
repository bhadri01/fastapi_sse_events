# CRM Comment System Example

This example demonstrates a complete CRM comment system with real-time updates using FastAPI SSE Events.

## Features

- ✅ REST API for comment CRUD operations
- ✅ Real-time updates via Server-Sent Events (SSE)
- ✅ Multi-client synchronization via Redis Pub/Sub
- ✅ Topic-based subscriptions (per comment thread)
- ✅ Authorization hooks (demo implementation)
- ✅ Beautiful, responsive web interface
- ✅ Visual feedback for real-time updates

## Prerequisites

1. **Python 3.10+**
2. **Redis server**

## Setup

### 1. Install Dependencies

From the project root:

```bash
# Install the fastapi-sse-events package in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

**Using Poetry:**
```bash
poetry install
```

Or install just the example dependencies:

```bash
cd examples/crm_comments
pip install -r requirements.txt
pip install -e ../..  # Install the main package
```

### 2. Configure Environment

Copy the example environment file and customize if needed:

```bash
cd examples/crm_comments
cp .env.example .env
```

Edit `.env` to configure your setup:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# SSE Configuration
SSE_HEARTBEAT_SECONDS=15
SSE_PATH=/events

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Configuration (comma-separated origins, or * for all)
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
```

**Configuration Options:**

- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379/0`)
- `SSE_HEARTBEAT_SECONDS`: Interval for heartbeat/ping events (default: `15`)
- `SSE_PATH`: HTTP path for SSE endpoint (default: `/events`)
- `API_HOST`: Host to bind the server (default: `0.0.0.0`)
- `API_PORT`: Port to run the server (default: `8000`)
- `API_RELOAD`: Enable auto-reload on code changes (default: `true`)
- `CORS_ORIGINS`: Allowed CORS origins, comma-separated or `*` for all (default: `*`)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: `INFO`)

### 3. Start Redis

Using Docker (recommended):

```bash
docker run -d -p 6379:6379 redis:alpine
```

Or using local Redis:

```bash
redis-server
```

### 4. Run the Application

**Quick Start (Recommended):**

```bash
cd examples/crm_comments
./start.sh
```

The `start.sh` script will:
- Create `.env` from `.env.example` if it doesn't exist
- Check Redis connection
- Verify dependencies
- Display configuration
- Start the application

**Manual Start:**

```bash
cd examples/crm_comments
uvicorn app:app --reload
```

The API will be available at: http://localhost:8000

**Note:** The application automatically loads configuration from `.env` file.

To run with custom port:

```bash
# Option 1: Edit .env file
# API_PORT=8080

# Option 2: Set environment variable
API_PORT=8080 uvicorn app:app --reload

# Option 3: Run directly with uvicorn options
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### 5. Open the Client

Open `client.html` in your web browser:

```bash
# On Linux/macOS
open client.html

# On Windows
start client.html

# Or simply drag the file into your browser
```

## Usage

### Testing Real-time Updates

1. **Open multiple browser tabs** with `client.html`
2. **Post a comment** in one tab
3. **Watch it appear instantly** in all other tabs!
4. **Try editing or deleting** comments
5. **Switch between threads** to see isolated updates

### API Endpoints

#### Get All Threads
```bash
curl http://localhost:8000/threads
```

#### Get Comments for Thread
```bash
curl http://localhost:8000/threads/1/comments
```

#### Create Comment
```bash
curl -X POST http://localhost:8000/threads/1/comments \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": 1,
    "author": "Alice",
    "content": "This is a test comment"
  }'
```

#### Update Comment
```bash
curl -X PUT http://localhost:8000/comments/1 \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated comment text"
  }'
```

#### Delete Comment
```bash
curl -X DELETE http://localhost:8000/comments/1
```

#### Subscribe to SSE Stream
```bash
curl -N http://localhost:8000/events?topic=comment_thread:1
```

Or use a browser EventSource:
```javascript
const eventSource = new EventSource('http://localhost:8000/events?topic=comment_thread:1');

eventSource.addEventListener('comment_created', (e) => {
  console.log('New comment:', JSON.parse(e.data));
});

eventSource.addEventListener('comment_updated', (e) => {
  console.log('Updated comment:', JSON.parse(e.data));
});

eventSource.addEventListener('comment_deleted', (e) => {
  console.log('Deleted comment:', JSON.parse(e.data));
});
```

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Browser 1  │         │  Browser 2  │         │  Browser N  │
│             │         │             │         │             │
│ EventSource │         │ EventSource │         │ EventSource │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │          SSE (/events?topic=...)             │
       └───────────────────────┼───────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   FastAPI Server    │
                    │                     │
                    │  • REST Endpoints   │
                    │  • SSE Handler      │
                    │  • EventBroker      │
                    └──────────┬──────────┘
                               │
                               │ Redis Pub/Sub
                               │
                    ┌──────────▼──────────┐
                    │    Redis Server     │
                    │                     │
                    │  • Pub/Sub channels │
                    │  • Topic routing    │
                    └─────────────────────┘
```

### Flow:

1. **Client** opens SSE connection to `/events?topic=comment_thread:1`
2. **Server** subscribes to Redis channel `comment_thread:1`
3. **User** posts comment via REST API
4. **Server** saves comment and publishes event to Redis
5. **Redis** broadcasts event to all subscribers
6. **All connected clients** receive SSE event
7. **Clients** automatically refresh data via REST API

## Event Types

### `comment_created`
Sent when a new comment is posted.

```json
{
  "comment_id": "1",
  "thread_id": 1,
  "author": "Alice",
  "timestamp": "2026-03-02T10:30:00Z"
}
```

### `comment_updated`
Sent when a comment is edited.

```json
{
  "comment_id": "1",
  "thread_id": 1,
  "timestamp": "2026-03-02T10:35:00Z"
}
```

### `comment_deleted`
Sent when a comment is deleted.

```json
{
  "comment_id": "1",
  "thread_id": 1,
  "timestamp": "2026-03-02T10:40:00Z"
}
```

### `ping`
Heartbeat event sent every 15 seconds to keep connection alive.

```json
{
  "timestamp": 1709377200
}
```

## Production Considerations

### Environment Configuration

Always use environment variables for sensitive configuration:

```python
# Good - Use environment variables
config = RealtimeConfig(
    redis_url=os.getenv("REDIS_URL"),
    heartbeat_seconds=int(os.getenv("SSE_HEARTBEAT_SECONDS", "15")),
)

# Bad - Hardcoded values
config = RealtimeConfig(
    redis_url="redis://localhost:6379/0",  # Don't hardcode in production!
)
```

Store sensitive values in:
- `.env` files (development, not committed)
- Environment variables (production)
- Secret management services (AWS Secrets Manager, HashiCorp Vault, etc.)

### Authorization

The demo uses a permissive authorization function. In production:

```python
async def authorize_topic(request: Request, topic: str) -> bool:
    # Extract user from JWT token
    token = request.headers.get("Authorization")
    user = verify_jwt(token)
    
    # Extract thread_id from topic
    if topic.startswith("comment_thread:"):
        thread_id = int(topic.split(":")[1])
        
        # Check if user has access to this thread
        return await user_can_access_thread(user.id, thread_id)
    
    return False
```

### Database

Replace in-memory storage with a real database:

```python
# Instead of:
comments_db: dict[str, dict] = {}

# Use:
from sqlalchemy import select
comment = await session.execute(select(Comment).where(Comment.id == comment_id))
```

### Error Handling

Add proper error handling and logging:

```python
try:
    await broker.publish(...)
except Exception as e:
    logger.error(f"Failed to publish event: {e}")
    # Don't fail the request if SSE publish fails
```

### Scaling

For production deployments:

1. **Use Redis Cluster** for high availability
2. **Load balance FastAPI instances** (events propagate via Redis)
3. **Set connection limits** on the SSE endpoint
4. **Implement reconnection logic** in the client
5. **Monitor Redis memory usage** for pub/sub backlog

### Nginx Configuration

Disable buffering for SSE endpoints:

```nginx
location /events {
    proxy_pass http://fastapi_backend;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;
}
```

## Troubleshooting

### SSE connection fails
- Check if Redis is running: `redis-cli ping`
- Check CORS settings if accessing from different origin
- Check browser console for errors

### Updates not appearing
- Verify Redis Pub/Sub: `redis-cli SUBSCRIBE comment_thread:1`
- Check FastAPI logs for errors
- Ensure multiple clients connect to same Redis instance

### High memory usage
- Monitor Redis memory: `redis-cli INFO memory`
- Reduce heartbeat frequency if needed
- Implement connection timeouts

## License

This example is part of the FastAPI SSE Events package (MIT License).
