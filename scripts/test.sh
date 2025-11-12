#!/bin/bash
# Run comprehensive test suite with reporting
#
# Description:
#   Runs complete test suite (unit, integration, UI tests) with coverage reporting
#   and generates HTML/JSON reports for analysis.
#
# Usage:
#   ./scripts/test.sh [options]
#
# Options:
#   No options currently supported (runs all tests)
#
# Requirements:
#   - Virtual environment activated (source venv/bin/activate)
#   - All dependencies installed (poetry install)
#   - Playwright browsers installed (npx playwright install)
#
# Output:
#   - HTML Report: reports/test_report.html
#   - Coverage Report: reports/coverage/index.html
#   - JSON Report: reports/report.json
#   - Playwright Report: playwright-report/index.html
#   - Terminal: Coverage summary and test results
#
# Exit Codes:
#   0 - All tests passed
#   1 - One or more tests failed
#
# Examples:
#   ./scripts/test.sh                         # Run all tests
#   open reports/test_report.html             # View HTML report
#   open reports/coverage/index.html          # View coverage report

set -e

echo "🧪 Running Deep Agent AGI test suite..."

# Activate virtual environment
source venv/bin/activate

# Create reports directory
mkdir -p reports

# Run pytest with coverage and HTML report
echo "📊 Running unit and integration tests..."
pytest \
    --cov=backend/deep_agent \
    --cov-report=html:reports/coverage \
    --cov-report=term-missing \
    --html=reports/test_report.html \
    --self-contained-html \
    --json-report \
    --json-report-file=reports/report.json \
    -v

# Run Playwright UI tests
echo "🎭 Running UI tests with Playwright..."
npm run test:ui

# Display summary
echo ""
echo "✅ Test suite complete!"
echo ""
echo "📄 Reports generated:"
echo "  - HTML Report: reports/test_report.html"
echo "  - Coverage Report: reports/coverage/index.html"
echo "  - JSON Report: reports/report.json"
echo "  - Playwright Report: playwright-report/index.html"
echo ""
