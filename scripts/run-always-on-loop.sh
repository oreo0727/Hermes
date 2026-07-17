#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT_DIR/state/hermes"
PID_FILE="$STATE_DIR/always-on-loop.pid"
ENV_FILE="$STATE_DIR/always-on-loop.env"
LOG_FILE="$STATE_DIR/always-on-loop.log"
INTERVAL="${INTERVAL:-60}"
ACTION="${1:-start}"

mkdir -p "$STATE_DIR"

is_running() {
  [[ -f "$PID_FILE" ]] || return 1
  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

case "$ACTION" in
  start)
    if is_running; then
      echo "Always-on loop already running (PID $(cat "$PID_FILE"))."
      exit 0
    fi
    nohup python3 -m hermes_stack.scaffold \
      --root-dir "$ROOT_DIR" \
      --interval "$INTERVAL" \
      --cycles 0 \
      always-on-loop > "$LOG_FILE" 2>&1 &
    echo "$!" > "$PID_FILE"
    echo "INTERVAL=$INTERVAL" > "$ENV_FILE"
    echo "Started always-on loop (PID $(cat "$PID_FILE"), interval ${INTERVAL}s)."
    ;;
  stop)
    if is_running; then
      kill "$(cat "$PID_FILE")"
      rm -f "$PID_FILE"
      rm -f "$ENV_FILE"
      echo "Stopped always-on loop."
    else
      rm -f "$PID_FILE"
      rm -f "$ENV_FILE"
      echo "Always-on loop is not running."
    fi
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    if is_running; then
      # shellcheck disable=SC1090
      [[ -f "$ENV_FILE" ]] && source "$ENV_FILE"
      echo "Always-on loop running (PID $(cat "$PID_FILE"), interval ${INTERVAL}s)."
      exit 0
    fi
    echo "Always-on loop is not running."
    exit 1
    ;;
  log)
    tail -n "${LINES:-80}" "$LOG_FILE"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|status|log}" >&2
    exit 2
    ;;
esac
