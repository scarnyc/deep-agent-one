#!/bin/bash
# Run comprehensive test suite with reporting

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
