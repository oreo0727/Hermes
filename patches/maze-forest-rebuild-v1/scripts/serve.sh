#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-8000}"
cd "$(dirname "$0")/.."
python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
PID=$!
echo "Serving Maze Forest at: http://localhost:$PORT/maze-forest/ (PID $PID)"
echo "Press Ctrl+C to stop in this terminal, or kill $PID"
wait $PID
