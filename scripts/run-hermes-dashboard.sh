#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-operator}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

case "$PROFILE" in
  operator) PORT=9119 ;;
  app-dev) PORT=9120 ;;
  game-dev) PORT=9121 ;;
  creative-dev) PORT=9122 ;;
  *)
    echo "Unknown profile: $PROFILE" >&2
    exit 1
    ;;
esac

exec "$ROOT_DIR/scripts/run-hermes.sh" "$PROFILE" dashboard --host 127.0.0.1 --port "$PORT" --no-open
