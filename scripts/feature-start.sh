#!/bin/bash
# Create a new feature, bugfix, or hotfix branch from the integration branch
#
# Description:
#   Creates a properly named branch from main with JIRA ticket integration,
#   validates ticket format, and sets up remote tracking.
#
# Usage:
#   ./scripts/feature-start.sh DA1-123 "add user authentication"
#   ./scripts/feature-start.sh DA1-456 "fix websocket timeout" --bugfix
#   ./scripts/feature-start.sh "security patch" --hotfix
#
# Arguments:
#   $1 - JIRA ticket number (required for feature/bugfix, format: DA1-NNN)
#   $2+ - Short description (required, will be kebab-cased)
#   --bugfix - Create bugfix/ branch instead of feature/
#   --hotfix - Create hotfix/ branch (no ticket required)
#
# Requirements:
#   - Clean working directory (no uncommitted changes)
#   - Git repository with origin remote configured
#
# Output:
#   - New branch created and checked out
#   - Branch set to track origin/main
#
# Exit Codes:
#   0 - Branch created successfully
#   1 - Invalid arguments or dirty working directory
#
# Examples:
#   ./scripts/feature-start.sh DA1-15 "git workflow setup"
#   ./scripts/feature-start.sh DA1-42 "fix timeout bug" --bugfix
#   ./scripts/feature-start.sh "critical security patch" --hotfix

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INTEGRATION_BRANCH="main"
JIRA_PROJECT="DA1"

# Parse arguments
BRANCH_TYPE="feature"
TICKET=""
DESCRIPTION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --bugfix)
            BRANCH_TYPE="bugfix"
            shift
            ;;
        --hotfix)
            BRANCH_TYPE="hotfix"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 <ticket> <description> [--bugfix|--hotfix]"
            echo ""
            echo "Examples:"
            echo "  $0 DA1-123 'add user auth'        # feature/DA1-123-add-user-auth"
            echo "  $0 DA1-456 'fix timeout' --bugfix # bugfix/DA1-456-fix-timeout"
            echo "  $0 'security patch' --hotfix      # hotfix/security-patch"
            exit 0
            ;;
        *)
            if [[ -z "$TICKET" ]]; then
                TICKET="$1"
            elif [[ -z "$DESCRIPTION" ]]; then
                DESCRIPTION="$1"
            else
                DESCRIPTION="$DESCRIPTION $1"
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [[ "$BRANCH_TYPE" != "hotfix" ]]; then
    if [[ ! "$TICKET" =~ ^${JIRA_PROJECT}-[0-9]+$ ]]; then
        echo -e "${RED}Error: Invalid ticket format. Expected ${JIRA_PROJECT}-NNN (e.g., DA1-123)${NC}"
        echo "Usage: $0 DA1-123 \"description\" [--bugfix]"
        exit 1
    fi

    if [[ -z "$DESCRIPTION" ]]; then
        echo -e "${RED}Error: Description is required${NC}"
        echo "Usage: $0 DA1-123 \"description\" [--bugfix]"
        exit 1
    fi
else
    # For hotfix, first arg is description
    DESCRIPTION="$TICKET"
    TICKET=""
    if [[ -z "$DESCRIPTION" ]]; then
        echo -e "${RED}Error: Hotfix description is required${NC}"
        echo "Usage: $0 \"description\" --hotfix"
        exit 1
    fi
fi

# Convert description to kebab-case
DESCRIPTION=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')

# Build branch name
if [[ "$BRANCH_TYPE" == "hotfix" ]]; then
    BRANCH_NAME="hotfix/${DESCRIPTION}"
else
    BRANCH_NAME="${BRANCH_TYPE}/${TICKET}-${DESCRIPTION}"
fi

echo -e "${BLUE}Creating ${BRANCH_TYPE} branch: ${BRANCH_NAME}${NC}"

# Check for clean working directory
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}Error: Working directory is not clean. Commit or stash changes first.${NC}"
    git status --short
    exit 1
fi

# Fetch latest from remote
echo -e "${YELLOW}Fetching latest from origin...${NC}"
git fetch origin

# Create branch from integration branch
echo -e "${YELLOW}Creating branch from ${INTEGRATION_BRANCH}...${NC}"
git checkout -b "$BRANCH_NAME" "origin/${INTEGRATION_BRANCH}"

# Set upstream tracking
git branch --set-upstream-to="origin/${INTEGRATION_BRANCH}" "$BRANCH_NAME"

echo ""
echo -e "${GREEN}Branch created successfully: ${BRANCH_NAME}${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Make your changes"
if [[ -n "$TICKET" ]]; then
    echo "  2. Commit with: git commit -m \"feat(phase-0): your message [${TICKET}]\""
else
    echo "  2. Commit with: git commit -m \"fix(phase-0): your message\""
fi
echo "  3. Push with: git push -u origin ${BRANCH_NAME}"
echo "  4. Sync regularly: ./scripts/sync-develop.sh"
echo ""
