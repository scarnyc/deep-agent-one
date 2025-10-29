#!/bin/bash
# Development Mode: WebSocket (no hot-reload)
# Use this for developing WebSocket functionality, streaming responses, and real-time features
# Trade-off: Manual restart required for code changes, but WebSocket connections remain stable

set -e

echo "🚀 Starting Deep Agent AGI Backend (WebSocket Development Mode)"
echo "📝 Hot-reload DISABLED - manual restart needed for code changes"
echo "✅ WebSocket connections will remain stable"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Load environment variables
set -a
source ../.env
set +a

# Start uvicorn WITHOUT reload
../venv/bin/uvicorn deep_agent.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level debug

echo ""
echo "✅ Server stopped"
