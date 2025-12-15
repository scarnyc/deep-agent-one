#!/bin/bash
# Fetch LangSmith traces for terminal-based debugging
#
# Description:
#   Wrapper script for langsmith-fetch CLI tool. Provides common debugging
#   workflows for fetching and analyzing LangSmith traces directly in terminal.
#
# Usage:
#   ./scripts/fetch-traces.sh [command] [options]
#
# Commands:
#   recent              Fetch most recent trace (default)
#   last-n-minutes N    Fetch traces from last N minutes
#   export DIR          Export threads to directory for evaluation datasets
#   help                Show this help message
#
# Requirements:
#   - langsmith-fetch installed: pip install langsmith-fetch
#   - LANGSMITH_API_KEY in .env or environment
#   - LANGSMITH_PROJECT in .env (optional, defaults to "deep-agent-one")
#
# Exit Codes:
#   0 - Success
#   1 - Missing dependencies or configuration
#
# Examples:
#   ./scripts/fetch-traces.sh                           # Fetch most recent trace
#   ./scripts/fetch-traces.sh recent                    # Same as above
#   ./scripts/fetch-traces.sh last-n-minutes 30         # Last 30 minutes
#   ./scripts/fetch-traces.sh export ./trace-data 50    # Export 50 threads
#
# Integration:
#   - Use with debugging-expert agent for trace analysis
#   - Pipe JSON output to jq for filtering
#   - Export threads for building regression test suites

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for langsmith-fetch
if ! command -v langsmith-fetch &> /dev/null; then
    echo -e "${RED}Error: langsmith-fetch not found${NC}"
    echo "Install with: pip install langsmith-fetch"
    exit 1
fi

# Check for API key
if [ -z "$LANGSMITH_API_KEY" ]; then
    echo -e "${RED}Error: LANGSMITH_API_KEY not set${NC}"
    echo "Set it in .env or export LANGSMITH_API_KEY=your_key"
    exit 1
fi

# Default project
PROJECT="${LANGSMITH_PROJECT:-deep-agent-one}"

# Function to show help
show_help() {
    echo "LangSmith Trace Fetcher"
    echo ""
    echo "Usage: ./scripts/fetch-traces.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  recent                    Fetch most recent trace (default)"
    echo "  last-n-minutes N          Fetch traces from last N minutes"
    echo "  export DIR [LIMIT]        Export threads to directory (default: 50)"
    echo "  help                      Show this help message"
    echo ""
    echo "Environment:"
    echo "  LANGSMITH_API_KEY         Required: Your LangSmith API key"
    echo "  LANGSMITH_PROJECT         Optional: Project name (default: deep-agent-one)"
    echo ""
    echo "Examples:"
    echo "  ./scripts/fetch-traces.sh recent"
    echo "  ./scripts/fetch-traces.sh last-n-minutes 30"
    echo "  ./scripts/fetch-traces.sh export ./trace-data 100"
    echo ""
    echo "Pipe to jq for filtering:"
    echo "  ./scripts/fetch-traces.sh recent | jq '.runs[0].error'"
}

# Function to get project UUID
get_project_uuid() {
    # Get project UUID from project name using langsmith-fetch
    # This may need adjustment based on actual CLI behavior
    echo -e "${YELLOW}Using project: $PROJECT${NC}" >&2
    # For now, we'll pass the project name directly and let the CLI handle it
    echo "$PROJECT"
}

# Main command handling
COMMAND="${1:-recent}"

case "$COMMAND" in
    recent)
        echo -e "${GREEN}Fetching most recent trace...${NC}"
        langsmith-fetch traces --project "$PROJECT" --format json --limit 1
        ;;

    last-n-minutes)
        MINUTES="${2:-30}"
        echo -e "${GREEN}Fetching traces from last $MINUTES minutes...${NC}"
        langsmith-fetch traces --project "$PROJECT" --format json --last-n-minutes "$MINUTES"
        ;;

    export)
        DIR="${2:-.}"
        LIMIT="${3:-50}"
        echo -e "${GREEN}Exporting $LIMIT threads to $DIR...${NC}"
        mkdir -p "$DIR"
        langsmith-fetch threads "$DIR" --project "$PROJECT" --limit "$LIMIT"
        echo -e "${GREEN}Export complete: $DIR${NC}"
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
