#!/bin/bash
# Run TheAuditor security scan

set -e

echo "🔒 Running TheAuditor security scan..."

# Check if TheAuditor is installed
if ! command -v aud &> /dev/null; then
    echo "❌ TheAuditor not found. Installing..."
    git clone https://github.com/TheAuditorTool/Auditor /tmp/auditor
    cd /tmp/auditor
    pip install -e .
    cd -
    echo "✅ TheAuditor installed"
fi

# Initialize if needed
if [ ! -d ".pf" ]; then
    echo "🔧 Initializing TheAuditor..."
    aud init
fi

# Run full security audit
echo "🔍 Running full security audit..."
aud full

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
