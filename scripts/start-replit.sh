#!/bin/bash
# =============================================================================
# Deep Agent AGI - Development Startup Script for Replit
# =============================================================================
# This script starts both backend and frontend services for development.
# Used by Replit's Run button via .replit configuration.
#
# Services:
#   - Backend:  FastAPI on port 8000 (with auto-reload)
#   - Frontend: Next.js on port 5000 (Replit webview)
# =============================================================================

set -e

echo "=== Deep Agent AGI (Development Mode) ==="
echo ""

# Generate datetime-stamped log filenames
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
BACKEND_LOG="logs/backend/${TIMESTAMP}.log"
FRONTEND_LOG="logs/frontend/${TIMESTAMP}.log"

# Ensure log and database directories exist
mkdir -p logs/backend logs/frontend db/data

# Install dependencies if not present (checks if uvicorn is importable)
echo "[0/3] Checking dependencies..."
if ! poetry run python -c "import uvicorn" 2>/dev/null; then
    echo "Installing dependencies (this may take a few minutes on first run)..."
    poetry install --no-interaction
fi
echo "Dependencies OK"

# Clean up any existing processes on our ports
echo "[1/3] Cleaning up existing processes..."
pkill -f "uvicorn.*--port 8000" 2>/dev/null || true
pkill -f "next.*--port 5000" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true
sleep 2

# Start backend in background with logging
echo "[2/3] Starting backend on port 8000..."
echo "       Backend log: ${BACKEND_LOG}"
poetry run uvicorn backend.deep_agent.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 | tee "${BACKEND_LOG}" &
BACKEND_PID=$!

# Wait for backend to initialize before starting frontend
sleep 5

# Start frontend with logging
echo "[3/3] Starting frontend on port 5000..."
echo "       Frontend log: ${FRONTEND_LOG}"
cd frontend && pnpm run dev --port 5000 --hostname 0.0.0.0 2>&1 | tee "../${FRONTEND_LOG}" &
FRONTEND_PID=$!

echo ""
echo "=== Services Started ==="
echo "Frontend: http://localhost:5000 (Chat UI - open in browser)"
echo "Backend:  http://localhost:8000 (API only - not for browser)"
echo ""
echo ">>> Open the Replit Webview or port 5000 to access the app <<<"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Handle graceful shutdown
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "Services stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for both processes (script stays alive)
wait $BACKEND_PID $FRONTEND_PID
