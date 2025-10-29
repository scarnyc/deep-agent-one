#!/bin/bash
# Development Mode: HTTP API (with hot-reload)
# Use this for developing HTTP endpoints, services, and general backend code
# WARNING: Hot-reload will break WebSocket connections. Use dev-ws.sh for WebSocket work.

set -e

echo "🚀 Starting Deep Agent AGI Backend (HTTP Development Mode)"
echo "📝 Hot-reload ENABLED - code changes will trigger restart"
echo "⚠️  WebSocket connections will be killed on reload"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Load environment variables
set -a
source ../.env
set +a

# Start uvicorn with reload
../venv/bin/uvicorn deep_agent.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level debug

echo ""
echo "✅ Server stopped"
