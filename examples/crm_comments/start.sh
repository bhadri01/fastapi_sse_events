#!/bin/bash

# Quick Start Script for CRM Comments Example
# This script helps verify your environment setup

set -e

echo "🚀 FastAPI SSE Events - CRM Comments Quick Start"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the examples/crm_comments directory"
    echo "   cd examples/crm_comments && ./start.sh"
    exit 1
fi

# Check if .env exists, if not copy from example
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Edit it to customize your configuration."
    echo ""
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli -u "${REDIS_URL:-redis://localhost:6379/0}" ping > /dev/null 2>&1; then
        echo "✅ Redis is running and accessible"
    else
        echo "⚠️  Warning: Cannot connect to Redis at ${REDIS_URL:-redis://localhost:6379/0}"
        echo "   Start Redis with: docker run -d -p 6379:6379 redis:alpine"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "⚠️  redis-cli not found. Skipping Redis check."
    echo "   Make sure Redis is running at ${REDIS_URL:-redis://localhost:6379/0}"
    echo ""
fi

# Check if Python packages are installed
echo "🔍 Checking Python dependencies..."
if python3 -c "import fastapi_sse_events" 2>/dev/null; then
    echo "✅ fastapi-sse-events package installed"
else
    echo "❌ Error: fastapi-sse-events not installed"
    echo "   Run: pip install -e ../.."
    exit 1
fi

# Display configuration
echo ""
echo "📋 Configuration:"
echo "   Redis URL: ${REDIS_URL:-redis://localhost:6379/0}"
echo "   API Host: ${API_HOST:-0.0.0.0}"
echo "   API Port: ${API_PORT:-8000}"
echo "   SSE Path: ${SSE_PATH:-/events}"
echo "   Heartbeat: ${SSE_HEARTBEAT_SECONDS:-15}s"
echo "   Log Level: ${LOG_LEVEL:-INFO}"
echo ""
echo "🌐 URLs:"
echo "   API Docs: http://localhost:${API_PORT:-8000}/docs"
echo "   SSE Stream: http://localhost:${API_PORT:-8000}${SSE_PATH:-/events}?topic=comment_thread:1"
echo "   Client: Open client.html in your browser"
echo ""
echo "🎯 Starting application..."
echo ""

# Start the application
if [ "${API_RELOAD:-true}" = "true" ]; then
    python3 -m uvicorn app:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}" --reload
else
    python3 -m uvicorn app:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}"
fi
