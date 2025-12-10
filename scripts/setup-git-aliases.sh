#!/bin/bash
# Set up project-local git aliases for common workflows
#
# Description:
#   Configures git aliases in local .git/config for feature branch
#   workflows and parallel development.
#
# Usage:
#   ./scripts/setup-git-aliases.sh
#
# What It Does:
#   1. Sets up aliases for feature workflow (feature, bugfix, hotfix)
#   2. Configures sync and finish shortcuts
#   3. Adds helpful status and log shortcuts
#   4. Adds WIP commit helpers
#
# Aliases Created:
#   git feature <ticket> <desc>  - Start new feature branch
#   git bugfix <ticket> <desc>   - Start new bugfix branch
#   git hotfix <desc>            - Start new hotfix branch
#   git sync                     - Sync with integration branch
#   git finish                   - Prepare branch for PR
#   git branches                 - List feature/bugfix/hotfix branches
#   git cleanup                  - Delete merged branches
#   git wip                      - Quick work-in-progress commit
#   git unwip                    - Undo last WIP commit
#   git st                       - Short status with branch
#   git lg                       - Graph log (15 commits)
#   git last                     - Show last commit details
#   git staged                   - Show staged changes
#   git unstage                  - Unstage files
#
# Examples:
#   ./scripts/setup-git-aliases.sh
#   git feature DA1-123 "add user auth"
#   git sync
#   git finish

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Setting up git aliases for Deep Agent One...${NC}"

# Feature workflow aliases (use scripts)
git config --local alias.feature '!./scripts/feature-start.sh'
git config --local alias.bugfix '!./scripts/feature-start.sh --bugfix'
git config --local alias.hotfix '!./scripts/feature-start.sh --hotfix'
git config --local alias.sync '!./scripts/sync-develop.sh'
git config --local alias.finish '!./scripts/feature-finish.sh'

# Branch management
git config --local alias.branches "branch -a --list 'feature/*' 'bugfix/*' 'hotfix/*'"
git config --local alias.cleanup "!git branch --merged origin/main | grep -E '^\\s*(feature|bugfix)/' | xargs -r git branch -d"

# Quick WIP commits
git config --local alias.wip "commit -am 'WIP: work in progress [skip ci]'"
git config --local alias.unwip "reset HEAD~1"

# Status shortcuts
git config --local alias.st "status --short --branch"
git config --local alias.lg "log --oneline --graph --decorate -15"
git config --local alias.last "log -1 HEAD --stat"

# Diff shortcuts
git config --local alias.staged "diff --cached"
git config --local alias.unstage "reset HEAD --"

# Stash shortcuts
git config --local alias.stash-save "stash push -m"
git config --local alias.stash-list "stash list"

echo -e "${GREEN}Git aliases configured${NC}"
echo ""
echo -e "${BLUE}Available aliases:${NC}"
echo ""
echo "  Feature Workflow:"
echo "    git feature DA1-123 \"description\"  - Start feature branch"
echo "    git bugfix DA1-123 \"description\"   - Start bugfix branch"
echo "    git hotfix \"description\"           - Start hotfix branch"
echo "    git sync                           - Sync with main branch"
echo "    git finish                         - Prepare for PR"
echo ""
echo "  Branch Management:"
echo "    git branches                       - List feature branches"
echo "    git cleanup                        - Delete merged branches"
echo ""
echo "  Quick Commits:"
echo "    git wip                            - Quick WIP commit"
echo "    git unwip                          - Undo WIP commit"
echo ""
echo "  Status & Logs:"
echo "    git st                             - Short status"
echo "    git lg                             - Graph log"
echo "    git last                           - Last commit details"
echo "    git staged                         - Show staged diff"
echo "    git unstage <file>                 - Unstage file"
echo ""
