#!/bin/bash
# Start frontend server with datetime-stamped logging

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Generate datetime-stamped log filename
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
LOG_FILE="logs/frontend/${TIMESTAMP}.log"

echo -e "${BLUE}Starting Deep Agent AGI Frontend...${NC}"
echo -e "${GREEN}Log file: ${LOG_FILE}${NC}"
echo ""

# Navigate to project root (script is in scripts/ directory)
cd "$(dirname "$0")/.."

echo -e "${BLUE}Starting Next.js dev server${NC}"
echo -e "${BLUE}Logs: ${LOG_FILE}${NC}"
echo -e "${BLUE}To tail logs: tail -f ${LOG_FILE}${NC}"
echo ""

# Start frontend with logging
cd frontend && npm run dev 2>&1 | tee ../${LOG_FILE}
