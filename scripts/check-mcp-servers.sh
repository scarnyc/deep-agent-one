#!/bin/bash

# MCP Server Health Check Script
# Validates MCP server executables, permissions, and environment variables

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=== MCP Server Health Check ==="
echo ""

ISSUES_FOUND=0

# Check JIRA MCP
echo -n "Checking JIRA MCP server... "
JIRA_MCP_PATH="/home/runner/workspace/.pythonlibs/bin/jira-mcp"

if [ ! -f "$JIRA_MCP_PATH" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "  - Executable not found at $JIRA_MCP_PATH"
    ISSUES_FOUND=1
else
    # Check if executable
    if [ ! -x "$JIRA_MCP_PATH" ]; then
        echo -e "${YELLOW}WARN${NC}"
        echo "  - File exists but not executable, attempting to fix..."
        chmod +x "$JIRA_MCP_PATH"
        if [ -x "$JIRA_MCP_PATH" ]; then
            echo -e "  - ${GREEN}Fixed permissions${NC}"
        else
            echo -e "  - ${RED}Failed to fix permissions${NC}"
            ISSUES_FOUND=1
        fi
    else
        # Test invocation
        if "$JIRA_MCP_PATH" --help &> /dev/null; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${YELLOW}WARN${NC}"
            echo "  - Executable exists but --help failed"
            ISSUES_FOUND=1
        fi
    fi

    # Check environment variables
    if [ -z "$JIRA_URL" ] || [ -z "$JIRA_USERNAME" ] || [ -z "$JIRA_API_TOKEN" ]; then
        echo -e "  - ${YELLOW}WARN${NC}: Missing JIRA environment variables"
        [ -z "$JIRA_URL" ] && echo "    - JIRA_URL not set"
        [ -z "$JIRA_USERNAME" ] && echo "    - JIRA_USERNAME not set"
        [ -z "$JIRA_API_TOKEN" ] && echo "    - JIRA_API_TOKEN not set"
        ISSUES_FOUND=1
    fi
fi

# Check Markitdown MCP
echo -n "Checking Markitdown MCP server... "
MARKITDOWN_MCP_PATH="/home/runner/workspace/.pythonlibs/bin/markitdown-mcp"

if [ ! -f "$MARKITDOWN_MCP_PATH" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "  - Executable not found at $MARKITDOWN_MCP_PATH"
    ISSUES_FOUND=1
else
    # Check if executable
    if [ ! -x "$MARKITDOWN_MCP_PATH" ]; then
        echo -e "${YELLOW}WARN${NC}"
        echo "  - File exists but not executable, attempting to fix..."
        chmod +x "$MARKITDOWN_MCP_PATH"
        if [ -x "$MARKITDOWN_MCP_PATH" ]; then
            echo -e "  - ${GREEN}Fixed permissions${NC}"
        else
            echo -e "  - ${RED}Failed to fix permissions${NC}"
            ISSUES_FOUND=1
        fi
    else
        # Test invocation
        if "$MARKITDOWN_MCP_PATH" --help &> /dev/null; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${YELLOW}WARN${NC}"
            echo "  - Executable exists but --help failed"
            ISSUES_FOUND=1
        fi
    fi
fi

# Check Perplexity MCP (npx-based)
echo -n "Checking Perplexity MCP server... "

if ! command -v npx &> /dev/null; then
    echo -e "${RED}FAIL${NC}"
    echo "  - npx command not found (Node.js not installed)"
    ISSUES_FOUND=1
else
    if [ -z "$PERPLEXITY_API_KEY" ]; then
        echo -e "${YELLOW}WARN${NC}"
        echo "  - PERPLEXITY_API_KEY not set"
        ISSUES_FOUND=1
    else
        echo -e "${GREEN}OK${NC}"
    fi
fi

echo ""
echo "=== Health Check Complete ==="

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}All MCP servers healthy${NC}"
    exit 0
else
    echo -e "${YELLOW}Issues detected - see warnings above${NC}"
    exit 1
fi
