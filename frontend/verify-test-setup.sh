#!/bin/bash

# Test Infrastructure Verification Script
# This script verifies that all testing components are properly configured

set -e

echo "==========================================="
echo "Frontend Test Infrastructure Verification"
echo "==========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Must run from frontend directory${NC}"
    exit 1
fi

echo -e "${YELLOW}1. Checking configuration files...${NC}"
files=(
    "jest.config.js"
    "jest.setup.js"
    "playwright.config.ts"
    ".env.test"
    ".gitignore"
    "TESTING.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file exists"
    else
        echo -e "  ${RED}✗${NC} $file missing"
        exit 1
    fi
done

echo ""
echo -e "${YELLOW}2. Checking test dependencies...${NC}"
dependencies=(
    "jest"
    "@testing-library/react"
    "@testing-library/jest-dom"
    "@testing-library/user-event"
    "@playwright/test"
    "jest-environment-jsdom"
)

for dep in "${dependencies[@]}"; do
    if npm list "$dep" --depth=0 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $dep installed"
    else
        echo -e "  ${RED}✗${NC} $dep not installed"
        exit 1
    fi
done

echo ""
echo -e "${YELLOW}3. Checking test directories...${NC}"
directories=(
    "__tests__"
    "e2e"
)

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "  ${GREEN}✓${NC} $dir/ exists"
    else
        echo -e "  ${RED}✗${NC} $dir/ missing"
        exit 1
    fi
done

echo ""
echo -e "${YELLOW}4. Verifying package.json scripts...${NC}"
scripts=(
    "test"
    "test:watch"
    "test:coverage"
    "test:ui"
    "test:ui:headed"
    "test:ui:debug"
)

for script in "${scripts[@]}"; do
    if grep -q "\"$script\":" package.json; then
        echo -e "  ${GREEN}✓${NC} npm run $script configured"
    else
        echo -e "  ${RED}✗${NC} npm run $script not configured"
        exit 1
    fi
done

echo ""
echo -e "${YELLOW}5. Running Jest tests...${NC}"
if npm test -- --no-coverage --passWithNoTests 2>&1 | grep -q "PASS"; then
    echo -e "  ${GREEN}✓${NC} Jest can run successfully"
else
    echo -e "  ${RED}✗${NC} Jest tests failed"
    exit 1
fi

echo ""
echo -e "${YELLOW}6. Checking Playwright installation...${NC}"
if npx playwright --version >/dev/null 2>&1; then
    version=$(npx playwright --version)
    echo -e "  ${GREEN}✓${NC} Playwright installed: $version"
else
    echo -e "  ${RED}✗${NC} Playwright not installed"
    exit 1
fi

echo ""
echo "==========================================="
echo -e "${GREEN}✓ All checks passed!${NC}"
echo "==========================================="
echo ""
echo "Test infrastructure is ready. You can now:"
echo "  - Run unit tests:     npm test"
echo "  - Run with coverage:  npm run test:coverage"
echo "  - Run E2E tests:      npm run test:ui"
echo "  - Read testing guide: cat TESTING.md"
echo ""
