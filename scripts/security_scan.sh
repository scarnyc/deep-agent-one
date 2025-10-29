#!/bin/bash
# Run TheAuditor security scan

set -e

echo "🔒 Running TheAuditor security scan..."

# Use local auditor venv
AUD_BIN="./.auditor_venv/bin/aud"

# Check if TheAuditor is installed in local venv
if [ ! -f "$AUD_BIN" ]; then
    echo "❌ TheAuditor not found in .auditor_venv. Please install it."
    echo "Run: ./.auditor_venv/bin/pip install -e /path/to/Auditor"
    exit 1
fi

# Initialize if needed
if [ ! -d ".pf" ]; then
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
