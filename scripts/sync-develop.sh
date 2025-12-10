#!/bin/bash
# Sync current branch with the integration branch (main)
#
# Description:
#   Fetches latest changes from origin and rebases (or merges) current branch
#   on the integration branch. Handles uncommitted changes gracefully.
#
# Usage:
#   ./scripts/sync-develop.sh [--merge] [--stash]
#
# Options:
#   --merge    Use merge instead of rebase (preserves branch history)
#   --stash    Automatically stash and restore uncommitted changes
#   -h, --help Show this help message
#
# Requirements:
#   - Git repository with origin remote
#
# What It Does:
#   1. Fetches latest from origin
#   2. Shows commits behind integration branch
#   3. Rebases (or merges) with integration branch
#   4. Reports sync status
#
# Exit Codes:
#   0 - Sync successful
#   1 - Conflicts detected (manual resolution required)
#
# Examples:
#   ./scripts/sync-develop.sh           # Rebase on main
#   ./scripts/sync-develop.sh --merge   # Merge instead of rebase
#   ./scripts/sync-develop.sh --stash   # Auto-stash changes

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INTEGRATION_BRANCH="main"

# Parse arguments
USE_MERGE=false
AUTO_STASH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --merge|-m)
            USE_MERGE=true
            shift
            ;;
        --stash|-s)
            AUTO_STASH=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--merge] [--stash]"
            echo ""
            echo "Options:"
            echo "  --merge, -m   Use merge instead of rebase"
            echo "  --stash, -s   Auto-stash uncommitted changes"
            echo "  --help, -h    Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}Syncing ${CURRENT_BRANCH} with ${INTEGRATION_BRANCH}...${NC}"

# Handle uncommitted changes
HAS_CHANGES=false
if [[ -n $(git status --porcelain) ]]; then
    HAS_CHANGES=true
    if [[ "$AUTO_STASH" == true ]]; then
        echo -e "${YELLOW}Stashing uncommitted changes...${NC}"
        git stash push -m "sync-develop auto-stash $(date +%Y-%m-%d-%H%M%S)"
    else
        echo -e "${RED}Error: Uncommitted changes detected.${NC}"
        echo "Use --stash to automatically stash changes, or commit/stash manually."
        git status --short
        exit 1
    fi
fi

# Fetch latest
echo -e "${YELLOW}Fetching latest from origin...${NC}"
git fetch origin

# Show status
BEHIND=$(git rev-list --count "HEAD..origin/${INTEGRATION_BRANCH}" 2>/dev/null || echo "0")
AHEAD=$(git rev-list --count "origin/${INTEGRATION_BRANCH}..HEAD" 2>/dev/null || echo "0")

echo -e "${BLUE}Status: ${AHEAD} ahead, ${BEHIND} behind ${INTEGRATION_BRANCH}${NC}"

if [[ "$BEHIND" -eq 0 ]]; then
    echo -e "${GREEN}Already up to date${NC}"
else
    # Sync with integration branch
    if [[ "$USE_MERGE" == true ]]; then
        echo -e "${YELLOW}Merging ${INTEGRATION_BRANCH}...${NC}"
        if ! git merge "origin/${INTEGRATION_BRANCH}" --no-edit; then
            echo -e "${RED}Merge conflicts detected. Resolve and commit.${NC}"
            if [[ "$HAS_CHANGES" == true && "$AUTO_STASH" == true ]]; then
                echo -e "${YELLOW}Note: Your changes are stashed. Run 'git stash pop' after resolving.${NC}"
            fi
            exit 1
        fi
    else
        echo -e "${YELLOW}Rebasing on ${INTEGRATION_BRANCH}...${NC}"
        if ! git rebase "origin/${INTEGRATION_BRANCH}"; then
            echo -e "${RED}Rebase conflicts detected. Resolve with:${NC}"
            echo "  1. Fix conflicts in listed files"
            echo "  2. git add <resolved-files>"
            echo "  3. git rebase --continue"
            echo "  (Or 'git rebase --abort' to cancel)"
            if [[ "$HAS_CHANGES" == true && "$AUTO_STASH" == true ]]; then
                echo -e "${YELLOW}Note: Your changes are stashed. Run 'git stash pop' after resolving.${NC}"
            fi
            exit 1
        fi
    fi

    echo -e "${GREEN}Sync complete${NC}"
fi

# Restore stashed changes
if [[ "$HAS_CHANGES" == true && "$AUTO_STASH" == true ]]; then
    echo -e "${YELLOW}Restoring stashed changes...${NC}"
    git stash pop
fi

# Show final status
echo ""
echo -e "${BLUE}Recent commits on ${CURRENT_BRANCH}:${NC}"
git log --oneline -5
