#!/bin/bash
# Run complete test suite with coverage reporting
# Usage: ./scripts/run_all_tests.sh

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
    --html=reports/test_report.html \
    --self-contained-html \
    -v

echo ""
echo "📊 Test Reports Generated:"
echo "  - Coverage Report (HTML): htmlcov/index.html"
echo "  - Coverage Report (JSON): coverage.json"
echo "  - Test Report (HTML): reports/test_report.html"
echo ""
echo "✅ Test suite complete!"
