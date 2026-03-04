"""Metrics and monitoring for SSE event system."""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects metrics for monitoring SSE system health and performance.

    Essential for production deployments with 10K+ concurrent connections.
    Integrates with Prometheus, StatsD, or custom monitoring solutions.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._start_time = time.time()

        # Connection metrics
        self._total_connections = 0
        self._current_connections = 0
        self._failed_connections = 0
        self._rejected_connections = 0  # Due to rate limiting

        # Message metrics
        self._messages_published = 0
        self._messages_delivered = 0
        self._messages_dropped = 0  # Slow consumer drops
        self._publish_errors = 0

        # Topic metrics
        self._active_topics = 0
        self._topic_subscribers: dict[str, int] = defaultdict(int)

        # Performance metrics
        self._publish_latencies: list[float] = []
        self._max_latencies = 100  # Keep last 100 measurements

        # Redis metrics
        self._redis_reconnects = 0
        self._redis_errors = 0

        # Lock for thread-safe updates
        self._lock = asyncio.Lock()

    async def record_connection_opened(self) -> None:
        """Record a new SSE connection."""
        async with self._lock:
            self._total_connections += 1
            self._current_connections += 1

    async def record_connection_closed(self) -> None:
        """Record an SSE connection closed."""
        async with self._lock:
            self._current_connections = max(0, self._current_connections - 1)

    async def record_connection_failed(self) -> None:
        """Record a failed connection attempt."""
        async with self._lock:
            self._failed_connections += 1

    async def record_connection_rejected(self) -> None:
        """Record a connection rejected due to limits."""
        async with self._lock:
            self._rejected_connections += 1

    async def record_message_published(self, latency_ms: float = 0) -> None:
        """Record a message published."""
        async with self._lock:
            self._messages_published += 1
            if latency_ms > 0:
                self._publish_latencies.append(latency_ms)
                if len(self._publish_latencies) > self._max_latencies:
                    self._publish_latencies.pop(0)

    async def record_message_delivered(self) -> None:
        """Record a message delivered to a client."""
        async with self._lock:
            self._messages_delivered += 1

    async def record_message_dropped(self) -> None:
        """Record a message dropped (slow consumer)."""
        async with self._lock:
            self._messages_dropped += 1

    async def record_publish_error(self) -> None:
        """Record a publish error."""
        async with self._lock:
            self._publish_errors += 1

    async def record_topic_subscribed(self, topic: str) -> None:
        """Record a new topic subscription."""
        async with self._lock:
            self._topic_subscribers[topic] += 1

    async def record_topic_unsubscribed(self, topic: str) -> None:
        """Record a topic unsubscription."""
        async with self._lock:
            if topic in self._topic_subscribers:
                self._topic_subscribers[topic] = max(0, self._topic_subscribers[topic] - 1)
                if self._topic_subscribers[topic] == 0:
                    del self._topic_subscribers[topic]

    async def record_redis_reconnect(self) -> None:
        """Record a Redis reconnection."""
        async with self._lock:
            self._redis_reconnects += 1

    async def record_redis_error(self) -> None:
        """Record a Redis error."""
        async with self._lock:
            self._redis_errors += 1

    async def get_metrics(self) -> dict[str, Any]:
        """
        Get current metrics snapshot.

        Returns:
            Dictionary with all current metrics
        """
        async with self._lock:
            uptime_seconds = time.time() - self._start_time

            # Calculate average latency
            avg_latency = (
                sum(self._publish_latencies) / len(self._publish_latencies)
                if self._publish_latencies
                else 0
            )

            # Calculate P95 latency
            p95_latency = 0
            if self._publish_latencies:
                sorted_latencies = sorted(self._publish_latencies)
                p95_index = int(len(sorted_latencies) * 0.95)
                p95_latency = (
                    sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else 0
                )

            return {
                "uptime_seconds": uptime_seconds,
                "connections": {
                    "current": self._current_connections,
                    "total": self._total_connections,
                    "failed": self._failed_connections,
                    "rejected": self._rejected_connections,
                },
                "messages": {
                    "published": self._messages_published,
                    "delivered": self._messages_delivered,
                    "dropped": self._messages_dropped,
                    "publish_errors": self._publish_errors,
                },
                "topics": {
                    "active": len(self._topic_subscribers),
                    "subscribers_by_topic": dict(self._topic_subscribers),
                },
                "performance": {
                    "avg_publish_latency_ms": round(avg_latency, 2),
                    "p95_publish_latency_ms": round(p95_latency, 2),
                },
                "redis": {
                    "reconnects": self._redis_reconnects,
                    "errors": self._redis_errors,
                },
                "health": self._calculate_health_status(),
            }

    def _calculate_health_status(self) -> str:
        """
        Calculate overall health status.

        Returns:
            Health status: "healthy", "degraded", or "unhealthy"
        """
        # Check for critical issues
        if self._current_connections == 0 and self._failed_connections > 10:
            return "unhealthy"

        # Check for degraded performance
        if self._messages_dropped > self._messages_delivered * 0.1:  # >10% drop rate
            return "degraded"

        if self._redis_errors > 10:
            return "degraded"

        if self._publish_errors > self._messages_published * 0.05:  # >5% error rate
            return "degraded"

        return "healthy"

    async def get_prometheus_format(self) -> str:
        """
        Get metrics in Prometheus format.

        Returns:
            String with Prometheus-formatted metrics
        """
        metrics = await self.get_metrics()

        lines = [
            "# HELP sse_connections_current Current number of SSE connections",
            "# TYPE sse_connections_current gauge",
            f"sse_connections_current {metrics['connections']['current']}",
            "",
            "# HELP sse_connections_total Total number of SSE connections",
            "# TYPE sse_connections_total counter",
            f"sse_connections_total {metrics['connections']['total']}",
            "",
            "# HELP sse_connections_rejected Total rejected connections",
            "# TYPE sse_connections_rejected counter",
            f"sse_connections_rejected {metrics['connections']['rejected']}",
            "",
            "# HELP sse_messages_published Total messages published",
            "# TYPE sse_messages_published counter",
            f"sse_messages_published {metrics['messages']['published']}",
            "",
            "# HELP sse_messages_dropped Total messages dropped",
            "# TYPE sse_messages_dropped counter",
            f"sse_messages_dropped {metrics['messages']['dropped']}",
            "",
            "# HELP sse_topics_active Current number of active topics",
            "# TYPE sse_topics_active gauge",
            f"sse_topics_active {metrics['topics']['active']}",
            "",
            "# HELP sse_publish_latency_ms Average publish latency in milliseconds",
            "# TYPE sse_publish_latency_ms gauge",
            f"sse_publish_latency_ms {metrics['performance']['avg_publish_latency_ms']}",
            "",
        ]

        return "\n".join(lines)


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
