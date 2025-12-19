#!/bin/bash
# WebSocket connection health check

echo "🔌 WebSocket Health Check"
echo "========================="

# Check backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ Backend is running (port 8000)"
else
  echo "❌ Backend is NOT running (port 8000)"
  exit 1
fi

# Check frontend is running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "✅ Frontend is running (port 3000)"
else
  echo "❌ Frontend is NOT running (port 3000)"
  exit 1
fi

# Check config endpoint
echo ""
echo "Fetching public config..."
CONFIG=$(curl -s http://localhost:8000/api/v1/config/public)
IS_REPLIT=$(echo $CONFIG | jq -r '.is_replit')
WS_PATH=$(echo $CONFIG | jq -r '.websocket_path')

echo "   is_replit: $IS_REPLIT"
echo "   websocket_path: $WS_PATH"

if [ "$IS_REPLIT" = "true" ]; then
  echo "✅ Replit mode enabled - frontend should connect to port 8000"
else
  echo "⚠️  Replit mode disabled - may cause issues in Replit environment"
fi

# Check recent logs for WebSocket errors
echo ""
echo "Recent WebSocket errors:"
grep -i "websocket\|upgrade" logs/frontend/*.log 2>/dev/null | tail -5 || echo "(none)"

echo ""
echo "✅ Health check complete"
