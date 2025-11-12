#!/bin/bash
# Start backend server with datetime-stamped logging
#
# Description:
#   Starts Deep Agent AGI FastAPI backend on http://127.0.0.1:8000 with automatic reload
#   and datetime-stamped logging.
#
# Usage:
#   ./scripts/start-backend.sh
#
# Requirements:
#   - .env file with API keys (OPENAI_API_KEY, LANGSMITH_API_KEY, etc.)
#   - Virtual environment at venv/bin/activate
#   - Python dependencies installed (poetry install)
#
# Output:
#   - Logs to: logs/backend/YYYY-MM-DD-HH-MM-SS.log
#   - Server runs on: http://127.0.0.1:8000
#
# Examples:
#   ./scripts/start-backend.sh                # Start backend
#   tail -f logs/backend/2025-11-12-*.log     # Watch logs

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Generate datetime-stamped log filename
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
LOG_FILE="logs/backend/${TIMESTAMP}.log"

echo -e "${BLUE}Starting Deep Agent AGI Backend...${NC}"
echo -e "${GREEN}Log file: ${LOG_FILE}${NC}"
echo ""

# Navigate to project root (script is in scripts/ directory)
cd "$(dirname "$0")/.."

# Source .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo -e "${GREEN}.env file loaded${NC}"
else
    echo -e "${RED}Warning: .env file not found${NC}"
fi

# Activate virtual environment
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
    echo -e "${GREEN}Virtual environment activated${NC}"
else
    echo -e "${RED}Error: Virtual environment not found at venv/bin/activate${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Starting uvicorn on http://127.0.0.1:8000${NC}"
echo -e "${BLUE}Logs: ${LOG_FILE}${NC}"
echo -e "${BLUE}To tail logs: tail -f ${LOG_FILE}${NC}"
echo ""

# Start backend with logging
cd backend && uvicorn deep_agent.main:app --reload --port 8000 2>&1 | tee ../${LOG_FILE}
