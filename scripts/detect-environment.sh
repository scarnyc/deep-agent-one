#!/bin/bash
# Detect environment and print configuration help

echo "🔍 Environment Detection"
echo "======================="

if [ -n "$REPL_SLUG" ]; then
  echo "✅ Replit environment detected"
  echo "   REPL_SLUG: $REPL_SLUG"
  echo "   REPL_OWNER: $REPL_OWNER"
  echo "   REPLIT_DEV_DOMAIN: $REPLIT_DEV_DOMAIN"
  echo ""
  echo "📝 Recommended .env settings:"
  echo "   NEXT_PUBLIC_API_URL=https://$REPLIT_DEV_DOMAIN"
  echo "   NEXT_PUBLIC_WS_URL=wss://$REPLIT_DEV_DOMAIN"
else
  echo "💻 Local development environment"
  echo ""
  echo "📝 Recommended .env settings:"
  echo "   NEXT_PUBLIC_API_URL=http://localhost:8000"
  echo "   NEXT_PUBLIC_WS_URL=ws://localhost:8000"
fi

echo ""
echo "Current .env configuration:"
grep "NEXT_PUBLIC" .env || echo "(No NEXT_PUBLIC variables found)"
