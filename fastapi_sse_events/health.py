"""Health check endpoints for load balancers and monitoring."""

import logging
from typing import Any

from fastapi import APIRouter, Response, status

from fastapi_sse_events.metrics import get_metrics_collector

logger = logging.getLogger(__name__)


def create_health_router() -> APIRouter:
    """
    Create health check router for monitoring and load balancing.

    Essential for production deployments with multiple instances.

    Returns:
        FastAPI router with health check endpoints

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_sse_events.health import create_health_router

        app = FastAPI()
        app.include_router(create_health_router())
        ```
    """
    router = APIRouter(tags=["Health"])

    @router.get("/health")
    async def health_check() -> dict[str, str]:
        """
        Basic health check endpoint.

        Returns 200 OK if service is running.
        Used by load balancers for basic availability checks.
        """
        return {"status": "healthy"}

    @router.get("/health/ready")
    async def readiness_check() -> Response:
        """
        Readiness check for Kubernetes/load balancers.

        Returns 200 if ready to accept traffic, 503 otherwise.
        Checks if service can handle new connections.
        """
        metrics = await get_metrics_collector().get_metrics()

        # Check if system is healthy and not overloaded
        health_status = metrics["health"]

        if health_status == "unhealthy":
            return Response(
                content='{"status": "not ready", "reason": "system unhealthy"}',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                media_type="application/json",
            )

        return Response(
            content='{"status": "ready"}',
            status_code=status.HTTP_200_OK,
            media_type="application/json",
        )

    @router.get("/health/live")
    async def liveness_check() -> dict[str, str]:
        """
        Liveness check for Kubernetes.

        Returns 200 OK if service is alive (not deadlocked).
        If this fails, container should be restarted.
        """
        return {"status": "alive"}

    @router.get("/metrics")
    async def metrics_endpoint() -> dict[str, Any]:
        """
        Get detailed metrics in JSON format.

        Returns comprehensive metrics for monitoring dashboards.
        """
        metrics = await get_metrics_collector().get_metrics()
        return metrics

    @router.get("/metrics/prometheus")
    async def prometheus_metrics() -> Response:
        """
        Get metrics in Prometheus format.

        Scrape this endpoint with Prometheus for monitoring.
        """
        prometheus_text = await get_metrics_collector().get_prometheus_format()
        return Response(
            content=prometheus_text,
            media_type="text/plain",
        )

    return router
