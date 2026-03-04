#!/usr/bin/env python3
"""
Load test for FastAPI SSE Events
Tests concurrent connections and message throughput
"""

import asyncio
import time
from dataclasses import dataclass

import aiohttp


@dataclass
class LoadTestConfig:
    """Configuration for load test."""

    base_url: str = "http://localhost"
    num_connections: int = 1000
    test_duration_seconds: int = 60
    publish_rate_per_second: int = 100
    topics: list[str] = None

    def __post_init__(self):
        if self.topics is None:
            self.topics = ["test_topic"]


@dataclass
class LoadTestResults:
    """Results from load test."""

    connections_established: int = 0
    connections_failed: int = 0
    messages_received: int = 0
    messages_published: int = 0
    publish_errors: int = 0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    duration_seconds: float = 0.0

    def print_summary(self):
        """Print test results."""
        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Duration: {self.duration_seconds:.1f}s")
        print("\nConnections:")
        print(f"  Established: {self.connections_established}")
        print(f"  Failed: {self.connections_failed}")
        print(f"  Success Rate: {self.connections_established / (self.connections_established + self.connections_failed) * 100:.1f}%")
        print("\nMessages:")
        print(f"  Published: {self.messages_published}")
        print(f"  Received: {self.messages_received}")
        print(f"  Publish Errors: {self.publish_errors}")
        print("\nLatency:")
        print(f"  Average: {self.avg_latency_ms:.2f}ms")
        print(f"  Maximum: {self.max_latency_ms:.2f}ms")
        print("\nThroughput:")
        print(f"  Messages/sec: {self.messages_received / self.duration_seconds:.1f}")
        print(f"  Per Connection: {self.messages_received / max(1, self.connections_established):.1f}")
        print("=" * 60)


class SSEClient:
    """SSE client for testing."""

    def __init__(
        self,
        base_url: str,
        topic: str,
        client_id: int,
        results: LoadTestResults,
    ):
        self.base_url = base_url
        self.topic = topic
        self.client_id = client_id
        self.results = results
        self.messages_received = 0

    async def connect_and_listen(self, duration: int):
        """Connect to SSE and listen for events."""
        url = f"{self.base_url}/events?topic={self.topic}"

        try:
            timeout = aiohttp.ClientTimeout(total=duration + 10)
            async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as response:
                if response.status != 200:
                    self.results.connections_failed += 1
                    return

                self.results.connections_established += 1

                start_time = time.time()
                async for line in response.content:
                    if time.time() - start_time > duration:
                        break

                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        self.messages_received += 1
                        self.results.messages_received += 1

        except asyncio.TimeoutError:
            pass  # Expected after test duration
        except Exception as e:
            self.results.connections_failed += 1
            print(f"Client {self.client_id} error: {e}")


class Publisher:
    """Publishes test messages."""

    def __init__(self, base_url: str, results: LoadTestResults):
        self.base_url = base_url
        self.results = results
        self.latencies: list[float] = []

    async def publish_loop(
        self,
        topics: list[str],
        rate_per_second: int,
        duration: int,
    ):
        """Publish messages at specified rate."""
        interval = 1.0 / rate_per_second if rate_per_second > 0 else 1.0
        url = f"{self.base_url}/data"

        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            message_id = 0

            while time.time() - start_time < duration:
                topic = topics[message_id % len(topics)]
                message_id += 1

                data = {
                    "id": message_id,
                    "topic": topic,
                    "content": f"Test message {message_id}",
                }

                publish_start = time.time()
                try:
                    async with session.post(url, json=data) as response:
                        if response.status in (200, 201):
                            self.results.messages_published += 1
                            latency = (time.time() - publish_start) * 1000
                            self.latencies.append(latency)
                        else:
                            self.results.publish_errors += 1
                except Exception as e:
                    self.results.publish_errors += 1
                    print(f"Publish error: {e}")

                await asyncio.sleep(interval)

        # Calculate latency stats
        if self.latencies:
            self.results.avg_latency_ms = sum(self.latencies) / len(self.latencies)
            self.results.max_latency_ms = max(self.latencies)


async def run_load_test(config: LoadTestConfig) -> LoadTestResults:
    """Run the load test."""
    results = LoadTestResults()

    print("\n🚀 Starting Load Test")
    print(f"   Target: {config.base_url}")
    print(f"   Connections: {config.num_connections}")
    print(f"   Duration: {config.test_duration_seconds}s")
    print(f"   Publish Rate: {config.publish_rate_per_second}/s")
    print(f"   Topics: {config.topics}")

    # Create clients
    clients = [
        SSEClient(
            base_url=config.base_url,
            topic=config.topics[i % len(config.topics)],
            client_id=i,
            results=results,
        )
        for i in range(config.num_connections)
    ]

    # Create publisher
    publisher = Publisher(config.base_url, results)

    # Start test
    test_start = time.time()

    # Create tasks for all clients and publisher
    client_tasks = [
        asyncio.create_task(
            client.connect_and_listen(config.test_duration_seconds)
        )
        for client in clients
    ]

    publisher_task = asyncio.create_task(
        publisher.publish_loop(
            config.topics,
            config.publish_rate_per_second,
            config.test_duration_seconds,
        )
    )

    # Wait for publisher to finish
    await publisher_task

    # Give clients a moment to receive final messages
    await asyncio.sleep(1)

    # Cancel remaining client tasks
    for task in client_tasks:
        if not task.done():
            task.cancel()

    # Wait for cancellation
    await asyncio.gather(*client_tasks, return_exceptions=True)

    results.duration_seconds = time.time() - test_start

    return results


async def check_health(base_url: str) -> bool:
    """Check if server is healthy."""
    try:
        async with aiohttp.ClientSession() as session, session.get(f"{base_url}/health") as response:
            return response.status == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


async def get_metrics(base_url: str) -> dict:
    """Get current metrics from server."""
    try:
        async with aiohttp.ClientSession() as session, session.get(f"{base_url}/metrics") as response:
            if response.status == 200:
                return await response.json()
    except Exception:
        pass
    return {}


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Load test FastAPI SSE Events")
    parser.add_argument(
        "--url",
        default="http://localhost",
        help="Base URL of the API (default: http://localhost)",
    )
    parser.add_argument(
        "--connections",
        type=int,
        default=100,
        help="Number of concurrent connections (default: 100)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Test duration in seconds (default: 30)",
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=10,
        help="Publish rate per second (default: 10)",
    )
    parser.add_argument(
        "--topics",
        nargs="+",
        default=["test_topic"],
        help="Topics to test (default: test_topic)",
    )

    args = parser.parse_args()

    config = LoadTestConfig(
        base_url=args.url,
        num_connections=args.connections,
        test_duration_seconds=args.duration,
        publish_rate_per_second=args.rate,
        topics=args.topics,
    )

    # Health check
    print("🏥 Checking server health...")
    if not await check_health(config.base_url):
        print("❌ Server is not healthy!")
        return

    print("✅ Server is healthy")

    # Get initial metrics
    initial_metrics = await get_metrics(config.base_url)
    if initial_metrics:
        print("\n📊 Initial Metrics:")
        print(f"   Connections: {initial_metrics.get('connections', {}).get('current', 0)}")
        print(f"   Active Topics: {initial_metrics.get('topics', {}).get('active', 0)}")

    # Run test
    results = await run_load_test(config)

    # Print results
    results.print_summary()

    # Get final metrics
    final_metrics = await get_metrics(config.base_url)
    if final_metrics:
        print("\n📊 Final Metrics:")
        print(f"   Connections: {final_metrics.get('connections', {}).get('current', 0)}")
        print(f"   Total Connections: {final_metrics.get('connections', {}).get('total', 0)}")
        print(f"   Rejected: {final_metrics.get('connections', {}).get('rejected', 0)}")
        print(f"   Messages Published: {final_metrics.get('messages', {}).get('published', 0)}")
        print(f"   Messages Delivered: {final_metrics.get('messages', {}).get('delivered', 0)}")
        print(f"   Messages Dropped: {final_metrics.get('messages', {}).get('dropped', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
