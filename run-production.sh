#!/bin/bash
# Run the production app (backend on 8001, frontend on 3001)
#
# PRODUCTION_DATA_DIR: where the woffieta-data clone lives. Defaults to
# ~/build/woffieta-data, falling back to ./Production for the legacy
# clone-into-Production setup. Override by exporting it before running.
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$PRODUCTION_DATA_DIR" ]; then
  if [ -d "$HOME/build/woffieta-data/CashFlow" ]; then
    PRODUCTION_DATA_DIR="$HOME/build/woffieta-data"
  elif [ -d "$HOME/woffieta-data/CashFlow" ]; then
    PRODUCTION_DATA_DIR="$HOME/woffieta-data"
  else
    PRODUCTION_DATA_DIR="$REPO_ROOT/Production"
  fi
fi
echo "Data dir: $PRODUCTION_DATA_DIR"

# uv provides a working python with the backend deps (system python3 may
# lack uvicorn); fall back to python3 if uv isn't installed.
echo "Starting production backend on port 8001..."
cd "$REPO_ROOT"
if command -v uv >/dev/null 2>&1; then
  DATA_MODE=production PRODUCTION_DATA_DIR="$PRODUCTION_DATA_DIR" \
    uv run --with-requirements backend/requirements.txt \
    python -m uvicorn app.main:app --reload --port 8001 --app-dir backend &
else
  DATA_MODE=production PRODUCTION_DATA_DIR="$PRODUCTION_DATA_DIR" \
    python3 -m uvicorn app.main:app --reload --port 8001 --app-dir backend &
fi
BACKEND_PID=$!

echo "Starting production frontend on port 3001..."
cd "$REPO_ROOT/frontend"
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
