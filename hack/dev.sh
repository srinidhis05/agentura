#!/usr/bin/env bash
# Start Agentura dev environment (backend + frontend)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT="${PORT:-3001}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  echo "Done."
}
trap cleanup EXIT INT TERM

# Start backend (FastAPI executor)
echo "Starting backend on :${BACKEND_PORT}..."
SKILLS_DIR="$ROOT/skills" PORT="$BACKEND_PORT" \
  "$ROOT/sdk/.venv/bin/agentura-server" &
BACKEND_PID=$!

# Wait for backend to be ready
for i in $(seq 1 15); do
  if curl -sf "http://localhost:${BACKEND_PORT}/healthz" > /dev/null 2>&1; then
    echo "Backend ready."
    break
  fi
  if [ "$i" -eq 15 ]; then
    echo "ERROR: Backend failed to start on :${BACKEND_PORT}" >&2
    exit 1
  fi
  sleep 1
done

# Start frontend (Next.js)
echo "Starting frontend on :${FRONTEND_PORT}..."
cd "$ROOT/web"
API_TARGET="http://localhost:${BACKEND_PORT}" npx next dev -p "$FRONTEND_PORT" &
FRONTEND_PID=$!

echo ""
echo "Agentura dev environment running:"
echo "  Frontend: http://localhost:${FRONTEND_PORT}"
echo "  Backend:  http://localhost:${BACKEND_PORT}"
echo "  Press Ctrl+C to stop."
echo ""

wait
