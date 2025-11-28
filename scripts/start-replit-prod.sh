#!/bin/bash
# =============================================================================
# Deep Agent AGI - Production Startup Script for Replit Deployments
# =============================================================================
# This script starts both backend and frontend services in production mode.
# Used by Replit Deployments (autoscale target).
#
# Services:
#   - Backend:  FastAPI with multiple workers (no reload)
#   - Frontend: Next.js production build
# =============================================================================

set -e

echo "=== Deep Agent AGI (Production Mode) ==="
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
    echo "Installing dependencies..."
    poetry install --no-interaction --only main
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

# Start backend with multiple workers for production (with logging)
echo "[2/3] Starting backend on port 8000 (production)..."
echo "       Backend log: ${BACKEND_LOG}"
poetry run uvicorn backend.deep_agent.main:app --host 0.0.0.0 --port 8000 --workers 2 2>&1 | tee "${BACKEND_LOG}" &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 5

# Start frontend in production mode (with logging)
echo "[3/3] Starting frontend on port 5000 (production)..."
echo "       Frontend log: ${FRONTEND_LOG}"
cd frontend && pnpm start --port 5000 --hostname 0.0.0.0 2>&1 | tee "../${FRONTEND_LOG}" &
FRONTEND_PID=$!

echo ""
echo "=== Production Services Started ==="
echo "Frontend: http://0.0.0.0:5000 (Chat UI - open in browser)"
echo "Backend:  http://0.0.0.0:8000 (API only - not for browser)"
echo ""
echo ">>> Access via main Replit URL or port 5000 <<<"
echo ""

# Handle graceful shutdown
cleanup() {
    echo ""
    echo "Graceful shutdown initiated..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "Services stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
