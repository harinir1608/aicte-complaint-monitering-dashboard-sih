#!/bin/bash
# verify_setup.sh — quick sanity check that both services are running.
set -e

echo "=== AICTE Complaint Dashboard — Setup Verification ==="
echo ""

# Check backend health
echo "Checking backend health..."
BACKEND_STATUS=$(curl -s -o /tmp/backend_health.json -w "%{http_code}" http://localhost:8000/health)
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "  Backend: OK (HTTP $BACKEND_STATUS)"
    cat /tmp/backend_health.json
    echo ""
else
    echo "  Backend: FAILED (HTTP $BACKEND_STATUS)"
    echo "  Is the backend running? Try: uvicorn app.main:app --reload --port 8000"
    exit 1
fi

# Check frontend
echo "Checking frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173)
if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
    echo "  Frontend: OK (HTTP $FRONTEND_STATUS)"
else
    echo "  Frontend: FAILED or not running (HTTP $FRONTEND_STATUS)"
    echo "  Is the frontend running? Try: cd frontend && npm run dev"
fi

echo ""
echo "=== Verification complete ==="
