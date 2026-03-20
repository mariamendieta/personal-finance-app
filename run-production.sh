#!/bin/bash
# Run the production app (backend on 8001, frontend on 3001)
echo "Starting production backend on port 8001..."
cd "$(dirname "$0")/backend"
DATA_MODE=production python3 -m uvicorn app.main:app --reload --port 8001 &
BACKEND_PID=$!

echo "Starting production frontend on port 3001..."
cd "$(dirname "$0")/frontend"
NEXT_PUBLIC_API_URL=http://localhost:8001 npx next dev --port 3001 &
FRONTEND_PID=$!

echo ""
echo "Production app running:"
echo "  Frontend: http://localhost:3001"
echo "  Backend:  http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
