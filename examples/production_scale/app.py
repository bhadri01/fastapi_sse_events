"""
Example FastAPI application optimized for 100K concurrent users.

This example shows production-ready configuration with:
- Health checks for load balancers
- Metrics endpoints for monitoring
- Optimized settings for high scale

Deploy 10-15 instances behind a load balancer for 100K users.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi_sse_events import RealtimeConfig, mount_sse, publish_event

# Create FastAPI app
app = FastAPI(
    title="SSE Events - Production Scale",
    description="Optimized for 100K+ concurrent users",
    version="2.0.0",
)

# CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Production-optimized configuration
config = RealtimeConfig(
    redis_url="redis://redis-cluster:7001,redis-cluster:7002,redis-cluster:7003/0",
    heartbeat_seconds=30,  # Longer heartbeat for efficiency
    max_connections=10000,  # 10K per instance
    max_queue_size=50,      # Lower memory per client
    max_message_size=32768, # 32KB max
)

# Mount SSE with health checks enabled
broker = mount_sse(
    app,
    config=config,
    include_health_checks=True,  # Adds /health, /metrics endpoints
)

# In-memory storage (use database in production)
data_store = {}
counter = 0


class DataItem(BaseModel):
    """Data item model."""
    id: int
    topic: str
    content: str


@app.get("/")
async def root():
    """API information with monitoring endpoints."""
    return {
        "message": "SSE Events - Production Scale",
        "capacity": "10,000 concurrent connections per instance",
        "endpoints": {
            "sse_stream": "/events?topic=your-topic",
            "create_data": "POST /data",
            "health_check": "/health",
            "readiness": "/health/ready",
            "liveness": "/health/live",
            "metrics_json": "/metrics",
            "metrics_prometheus": "/metrics/prometheus",
        },
        "deployment": {
            "for_100k_users": "Deploy 10-15 instances behind load balancer",
            "redis": "Use Redis Cluster with 3-5 nodes",
            "monitoring": "Scrape /metrics/prometheus with Prometheus",
        }
    }


@app.post("/data")
@publish_event(topic="data_updates", event="created")
async def create_data(_request: Request, item: DataItem) -> DataItem:
    """
    Create data item and automatically publish SSE event.

    The @publish_event decorator handles everything automatically.
    """
    global counter
    counter += 1

    new_item = DataItem(
        id=counter,
        topic=item.topic,
        content=item.content,
    )

    data_store[counter] = new_item

    # Decorator automatically publishes SSE event to "data_updates" topic
    return new_item


@app.get("/data")
async def list_data():
    """List all data items."""
    return {"items": list(data_store.values())}


# Health check endpoints are automatically added by mount_sse():
# - GET /health -> Basic health check
# - GET /health/ready -> Readiness probe (for load balancers)
# - GET /health/live -> Liveness probe (for container orchestration)
# - GET /metrics -> Detailed metrics in JSON
# - GET /metrics/prometheus -> Metrics in Prometheus format


if __name__ == "__main__":
    import uvicorn

    # Production configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for SSE (use multiple instances instead)
        log_level="warning",  # Less verbose in production
        access_log=False,  # Disable for performance
    )
