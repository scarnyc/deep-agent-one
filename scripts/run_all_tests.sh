#!/bin/bash
# Run complete test suite with coverage reporting
#
# Description:
#   Legacy test runner - runs unit and integration tests with coverage reporting.
#   For full test suite including UI tests, use ./scripts/test.sh instead.
#
# Usage:
#   ./scripts/run_all_tests.sh
#
# Requirements:
#   - Python 3.11+ (uses hardcoded Python path)
#   - All dependencies installed (poetry install)
#
# Output:
#   - Coverage Report (HTML): out/coverage/index.html
#   - Coverage Report (JSON): coverage.json
#   - Test Report (HTML): out/reports/test_report.html
#   - Terminal: Coverage summary
#
# Exit Codes:
#   0 - All tests passed
#   1 - One or more tests failed
#
# Examples:
#   ./scripts/run_all_tests.sh                # Run unit + integration tests
#   open out/coverage/index.html                   # View coverage report
#
# Note:
#   This script is being phased out in favor of ./scripts/test.sh which includes
#   UI tests and uses the virtual environment Python instead of hardcoded path.

set -e

echo "🧪 Running Deep Agent AGI Test Suite"
echo "===================================="
echo ""

# Clean up any cached bytecode
echo "🧹 Cleaning Python bytecode cache..."
find tests -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "✓ Cache cleaned"
echo ""

# Run tests with coverage
echo "🚀 Running tests..."
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest \
    tests/unit \
    tests/integration \
    --cov=backend/deep_agent \
    --cov-report=term \
    --cov-report=html \
    --cov-report=json \
    --html=out/reports/test_report.html \
    --self-contained-html \
    -v

echo ""
echo "📊 Test Reports Generated:"
echo "  - Coverage Report (HTML): out/coverage/index.html"
echo "  - Coverage Report (JSON): coverage.json"
echo "  - Test Report (HTML): out/reports/test_report.html"
echo ""
echo "✅ Test suite complete!"
