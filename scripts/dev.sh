#!/usr/bin/env bash
# Dev launcher: starts backend + TUI concurrently
# Usage: ./dev.sh          (starts both)
#        ./dev.sh backend  (backend only)
#        ./dev.sh tui      (tui only)

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_CMD="python -m uvicorn foundry_app.main:app --host 0.0.0.0 --port 8000 --reload"
TUI_CMD="bun run src/index.tsx"

TARGET="${1:-all}"

cleanup() {
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID 2>/dev/null; fi
    if [ -n "$TUI_PID" ]; then kill $TUI_PID 2>/dev/null; fi
    wait 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "Dream Foundry Dev"
echo ""

if [ "$TARGET" = "all" ] || [ "$TARGET" = "backend" ]; then
    echo "Starting backend..."
    (cd "$ROOT_DIR/foundry" && $BACKEND_CMD) &
    BACKEND_PID=$!
fi

if [ "$TARGET" = "all" ]; then
    echo "Waiting for backend..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
            echo "Backend ready!"
            break
        fi
        sleep 1
    done
fi

if [ "$TARGET" = "all" ] || [ "$TARGET" = "tui" ]; then
    echo "Starting TUI..."
    (cd "$ROOT_DIR/tui" && bun install && $TUI_CMD)
fi

wait
