#!/bin/bash
# Run TheAuditor security scan
#
# Description:
#   Runs TheAuditor security audit tool to detect vulnerabilities, secrets,
#   and security issues in the codebase. Part of pre-commit security workflow.
#
# Usage:
#   ./scripts/security_scan.sh
#
# Requirements:
#   - TheAuditor installed in .pf/venv/
#   - Install: .pf/venv/bin/pip install -e /path/to/Auditor
#
# What It Does:
#   1. Checks if TheAuditor is installed
#   2. Initializes .auditor/reports/ directory (if first run)
#   3. Runs full security audit
#   4. Checks for CRITICAL vulnerabilities
#   5. Exits with error code if critical issues found
#
# Output:
#   - Security reports: .auditor/reports/readthis/ directory
#   - Terminal: Summary of findings
#
# Exit Codes:
#   0 - No critical vulnerabilities detected
#   1 - Critical vulnerabilities found OR TheAuditor not installed
#
# Examples:
#   ./scripts/security_scan.sh                # Run security scan
#   cat .auditor/reports/readthis/*                        # View detailed findings
#
# Integration:
#   - Run before EVERY commit (code-review-expert workflow)
#   - Blocks commit if CRITICAL issues found
#   - Part of pre-commit hook (future)

set -e

echo "🔒 Running TheAuditor security scan..."

# Use local auditor venv
AUD_BIN="./.pf/venv/bin/aud"

# Check if TheAuditor is installed in local venv
if [ ! -f "$AUD_BIN" ]; then
    echo "❌ TheAuditor not found in .pf/venv. Please install it."
    echo "Run: ./.pf/venv/bin/pip install -e /path/to/Auditor"
    exit 1
fi

# Initialize if needed
if [ ! -d ".pf/readthis" ]; then
    echo "🔧 Initializing TheAuditor..."
    $AUD_BIN init
fi

# Run full security audit
echo "🔍 Running full security audit..."
$AUD_BIN full

# Display results
echo ""
echo "📄 Security scan complete!"
echo ""
echo "Results available in .pf/readthis/ directory"
echo ""

# Check for critical vulnerabilities
if grep -r "CRITICAL" .pf/readthis/ &> /dev/null; then
    echo "⚠️  CRITICAL vulnerabilities found! Review .pf/readthis/ immediately."
    exit 1
else
    echo "✅ No critical vulnerabilities detected"
fi
