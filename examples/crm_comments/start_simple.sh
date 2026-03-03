#!/bin/bash

# Quick start script for the simplified CRM Comments example
# This demonstrates the new decorator-based SSE API

echo "🚀 Starting Simplified CRM Comments Example"
echo ""

# Check if Redis is running
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  redis-cli not found. Make sure Redis is installed and running."
    echo "   Install: sudo apt install redis (Ubuntu) or brew install redis (macOS)"
    echo "   Start: redis-server"
    echo ""
else
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is not running. Starting Redis..."
        echo "   Run in another terminal: redis-server"
        echo ""
    fi
fi

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ] && [ ! -d "../../.venv" ]; then
    echo "⚠️  No virtual environment detected. Installing dependencies..."
    cd ../.. && poetry install && cd examples/crm_comments
fi

echo ""
echo "📝 Running simplified app (app_simple.py)"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - SSE: http://localhost:8000/events"
echo ""
echo "💡 Open client.html in your browser to see real-time updates!"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the simplified app
poetry run uvicorn app_simple:app --reload
