#!/bin/bash
# Start frontend server with datetime-stamped logging
#
# Description:
#   Starts Deep Agent AGI Next.js frontend on http://localhost:3000 with automatic reload
#   and datetime-stamped logging.
#
# Usage:
#   ./scripts/start-frontend.sh
#
# Requirements:
#   - Node.js 18+ installed
#   - Node.js dependencies installed (pnpm install in frontend/)
#   - Backend server running (or NEXT_PUBLIC_BACKEND_URL configured)
#
# Output:
#   - Logs to: logs/frontend/YYYY-MM-DD-HH-MM-SS.log
#   - Server runs on: http://localhost:3000
#
# Examples:
#   ./scripts/start-frontend.sh               # Start frontend
#   tail -f logs/frontend/2025-11-*.log       # Watch logs

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Generate datetime-stamped log filename
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
LOG_FILE="logs/frontend/${TIMESTAMP}.log"

# Ensure log directory exists
mkdir -p logs/frontend

echo -e "${BLUE}Starting Deep Agent AGI Frontend...${NC}"
echo -e "${GREEN}Log file: ${LOG_FILE}${NC}"
echo ""

# Navigate to project root (script is in scripts/ directory)
cd "$(dirname "$0")/.."

# Load environment variables from root .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo -e "${GREEN}Loaded environment variables from .env${NC}"
else
    echo -e "${BLUE}No .env file found, using defaults${NC}"
fi

echo -e "${BLUE}Starting Next.js dev server${NC}"
echo -e "${BLUE}Logs: ${LOG_FILE}${NC}"
echo -e "${BLUE}To tail logs: tail -f ${LOG_FILE}${NC}"
echo ""

# Start frontend with logging
cd frontend && CI=true pnpm run dev 2>&1 | tee ../${LOG_FILE}
