#!/bin/bash
# Finish feature branch and prepare for PR
#
# Description:
#   Syncs with integration branch, runs pre-commit checks,
#   and pushes to remote for PR creation.
#
# Usage:
#   ./scripts/feature-finish.sh [--force] [--no-push]
#
# Options:
#   --force, -f   Skip confirmation prompts
#   --no-push     Prepare locally without pushing
#   -h, --help    Show this help message
#
# Requirements:
#   - On a feature/bugfix/hotfix branch
#   - Clean working directory (all changes committed)
#
# What It Does:
#   1. Validates current branch is a feature branch
#   2. Fetches latest from origin
#   3. Rebases on integration branch
#   4. Runs pre-commit hooks
#   5. Pushes to remote
#   6. Displays PR creation instructions
#
# Exit Codes:
#   0 - Ready for PR
#   1 - Pre-commit failed or rebase conflicts
#
# Examples:
#   ./scripts/feature-finish.sh           # Full workflow
#   ./scripts/feature-finish.sh --force   # Skip confirmations
#   ./scripts/feature-finish.sh --no-push # Local only

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INTEGRATION_BRANCH="main"
# Derive REPO dynamically from git remote (supports SSH and HTTPS URLs)
REPO=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+/[^/]+)(\.git)?$|\1|')
if [[ -z "$REPO" ]]; then
    echo -e "${RED}Error: Could not determine repository from git remote${NC}"
    exit 1
fi

# Parse arguments
FORCE=false
NO_PUSH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=true
            shift
            ;;
        --no-push)
            NO_PUSH=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--force] [--no-push]"
            echo ""
            echo "Options:"
            echo "  --force, -f   Skip confirmation prompts"
            echo "  --no-push     Prepare locally without pushing"
            echo "  --help, -h    Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Validate branch type
if [[ ! "$CURRENT_BRANCH" =~ ^(feature|bugfix|hotfix)/ ]]; then
    echo -e "${RED}Error: Not on a feature/bugfix/hotfix branch${NC}"
    echo "Current branch: $CURRENT_BRANCH"
    echo ""
    echo "This script is intended for finishing feature branches."
    echo "Create a feature branch first with: ./scripts/feature-start.sh DA1-XXX description"
    exit 1
fi

echo -e "${BLUE}Finishing branch: ${CURRENT_BRANCH}${NC}"

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}Error: Uncommitted changes detected. Commit or stash first.${NC}"
    git status --short
    exit 1
fi

# Fetch latest
echo -e "${YELLOW}Fetching latest from origin...${NC}"
git fetch origin

# Count commits ahead of integration branch
COMMITS_AHEAD=$(git rev-list --count "origin/${INTEGRATION_BRANCH}..HEAD" 2>/dev/null || echo "0")
echo -e "${BLUE}Commits to merge: ${COMMITS_AHEAD}${NC}"

if [[ "$COMMITS_AHEAD" -eq 0 ]]; then
    echo -e "${YELLOW}Warning: No commits ahead of ${INTEGRATION_BRANCH}${NC}"
    if [[ "$FORCE" != true ]]; then
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Rebase on integration branch
BEHIND=$(git rev-list --count "HEAD..origin/${INTEGRATION_BRANCH}" 2>/dev/null || echo "0")
if [[ "$BEHIND" -gt 0 ]]; then
    echo -e "${YELLOW}Rebasing on ${INTEGRATION_BRANCH} (${BEHIND} commits behind)...${NC}"
    if ! git rebase "origin/${INTEGRATION_BRANCH}"; then
        echo -e "${RED}Rebase conflicts detected. Resolve conflicts and run:${NC}"
        echo "  git rebase --continue"
        echo "  ./scripts/feature-finish.sh"
        exit 1
    fi
fi

# Run pre-commit hooks
echo -e "${YELLOW}Running pre-commit checks...${NC}"
if command -v pre-commit &> /dev/null; then
    if ! pre-commit run --all-files; then
        echo -e "${RED}Pre-commit checks failed. Fix issues and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Pre-commit checks passed${NC}"
else
    echo -e "${YELLOW}Warning: pre-commit not installed, skipping checks${NC}"
fi

# Push to remote
if [[ "$NO_PUSH" != true ]]; then
    echo -e "${YELLOW}Pushing to remote...${NC}"
    git push -u origin "$CURRENT_BRANCH" --force-with-lease

    echo ""
    echo -e "${GREEN}Branch ready for PR${NC}"
    echo ""
    echo -e "${BLUE}Create PR with GitHub CLI:${NC}"

    # Extract ticket from branch name if present
    if [[ "$CURRENT_BRANCH" =~ (DA1-[0-9]+) ]]; then
        TICKET="${BASH_REMATCH[1]}"
        echo "  gh pr create --base ${INTEGRATION_BRANCH} --title \"[${TICKET}] Your PR title\" --body \"## Summary\\n\\n## JIRA Ticket\\n${TICKET}\""
    else
        echo "  gh pr create --base ${INTEGRATION_BRANCH} --title \"Your PR title\" --body \"## Summary\\n\\nDescription here\""
    fi

    echo ""
    echo -e "${BLUE}Or open in browser:${NC}"
    echo "  https://github.com/${REPO}/compare/${INTEGRATION_BRANCH}...${CURRENT_BRANCH}?expand=1"
else
    echo ""
    echo -e "${GREEN}Branch ready locally${NC}"
    echo "Run without --no-push to push to remote"
fi
