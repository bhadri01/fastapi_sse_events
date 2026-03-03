#!/bin/bash

# Production Scale Startup Script
# This script starts the complete production stack for 100K users

set -e

echo "========================================="
echo "FastAPI SSE Events - Production Setup"
echo "Target: 100,000 concurrent connections"
echo "========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Load environment variables
if [ -f "../../.env.100k_users" ]; then
    export $(cat ../../.env.100k_users | grep -v '^#' | xargs)
    echo "✅ Loaded .env.100k_users"
else
    echo "⚠️  Warning: .env.100k_users not found, using defaults"
fi

echo ""
echo "Starting services..."
echo "-------------------"

# Start the stack
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service health
echo ""
echo "Service Status:"
echo "---------------"

# Check Redis
if docker-compose exec -T redis-1 redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis Cluster: Healthy"
else
    echo "⚠️  Redis Cluster: Not ready yet"
fi

# Check FastAPI instances
HEALTHY_INSTANCES=0
for i in {1..3}; do
    if curl -s -f http://localhost:800$i/health > /dev/null 2>&1; then
        HEALTHY_INSTANCES=$((HEALTHY_INSTANCES + 1))
    fi
done
echo "✅ FastAPI Instances: $HEALTHY_INSTANCES/3 healthy"

# Check Nginx
if curl -s -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Nginx Load Balancer: Healthy"
else
    echo "⚠️  Nginx Load Balancer: Not ready yet"
fi

# Check Prometheus
if curl -s -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus: Healthy"
else
    echo "⚠️  Prometheus: Not ready yet"
fi

echo ""
echo "================================================="
echo "🚀 Production Stack Started!"
echo "================================================="
echo ""
echo "Access Points:"
echo "  - API (via Load Balancer): http://localhost"
echo "  - Direct FastAPI Instance:  http://localhost:8001"
echo "  - Prometheus Metrics:       http://localhost:9090"
echo "  - Grafana Dashboards:       http://localhost:3000"
echo ""
echo "Next Steps:"
echo "  1. Initialize Redis Cluster (if first run):"
echo "     docker-compose exec redis-1 redis-cli --cluster create \\"
echo "       redis-1:7001 redis-2:7002 redis-3:7003 \\"
echo "       --cluster-replicas 0 --cluster-yes"
echo ""
echo "  2. Test SSE connection:"
echo "     curl -N http://localhost/events?topic=test"
echo ""
echo "  3. Publish test message:"
echo "     curl -X POST http://localhost/data \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"id\": 1, \"topic\": \"test\", \"content\": \"Hello\"}'"
echo ""
echo "  4. View metrics:"
echo "     curl http://localhost/metrics | jq"
echo ""
echo "  5. Scale to 10 instances (for 100K users):"
echo "     docker-compose up -d --scale fastapi=10"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop stack: docker-compose down"
echo ""
