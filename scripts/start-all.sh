#!/bin/bash
# Start both backend and frontend servers with datetime-stamped logging
#
# Description:
#   Starts Deep Agent AGI backend (FastAPI on port 8000) and frontend (Next.js on port 3000)
#   servers concurrently with automatic log file generation.
#
# Usage:
#   ./scripts/start-all.sh
#
# Requirements:
#   - .env file with API keys (OPENAI_API_KEY, etc.)
#   - Virtual environment at venv/bin/activate
#   - Node.js dependencies installed (npm install in frontend/)
#   - Python dependencies installed (poetry install)
#
# Output:
#   - Backend logs: logs/backend/YYYY-MM-DD-HH-MM-SS.log
#   - Frontend logs: logs/frontend/YYYY-MM-DD-HH-MM-SS.log
#   - Both servers run in background, Ctrl+C stops both
#
# Examples:
#   ./scripts/start-all.sh                    # Start both servers
#   tail -f logs/backend/2025-11-12-*.log     # Watch backend logs
#   tail -f logs/frontend/2025-11-12-*.log    # Watch frontend logs

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to project root (script is in scripts/ directory)
cd "$(dirname "$0")/.."

# Generate datetime-stamped log filenames
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
BACKEND_LOG="logs/backend/${TIMESTAMP}.log"
FRONTEND_LOG="logs/frontend/${TIMESTAMP}.log"

echo -e "${BLUE}Starting Deep Agent AGI (Backend + Frontend)...${NC}"
echo ""
echo -e "${GREEN}Backend log: ${BACKEND_LOG}${NC}"
echo -e "${GREEN}Frontend log: ${FRONTEND_LOG}${NC}"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}Servers stopped${NC}"
    exit 0
}

# Register cleanup function for Ctrl+C
trap cleanup SIGINT SIGTERM

# Start backend in background
echo -e "${BLUE}Starting backend server on http://127.0.0.1:8000${NC}"
(
    # Source .env file
    if [ -f .env ]; then
        set -a
        source .env
        set +a
    fi

    # Activate virtual environment
    if [ -f venv/bin/activate ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: Virtual environment not found at venv/bin/activate${NC}"
        exit 1
    fi

    # Start backend with logging
    cd backend && uvicorn deep_agent.main:app --reload --port 8000 2>&1 | tee ../${BACKEND_LOG}
) &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend in background
echo -e "${BLUE}Starting frontend server on http://localhost:3000${NC}"
(
    cd frontend && npm run dev 2>&1 | tee ../${FRONTEND_LOG}
) &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✓ Both servers started${NC}"
echo ""
echo -e "${BLUE}Backend:${NC}  http://127.0.0.1:8000"
echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  Backend:  tail -f ${BACKEND_LOG}"
echo -e "  Frontend: tail -f ${FRONTEND_LOG}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both background processes
wait $BACKEND_PID $FRONTEND_PID
