#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <profile> [hermes args...]" >&2
  exit 1
fi

PROFILE="$1"
shift || true

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE_HOME="$ROOT_DIR/state/hermes/profiles/$PROFILE"
REPO_VENV_BIN="$ROOT_DIR/state/hermes/venv/bin/hermes"

if [[ ! -d "$PROFILE_HOME" ]]; then
  echo "Missing profile home: $PROFILE_HOME" >&2
  echo "Run ./scripts/bootstrap-hermes.sh first." >&2
  exit 1
fi

if [[ -x "$REPO_VENV_BIN" ]]; then
  HERMES_BIN="$REPO_VENV_BIN"
elif command -v hermes >/dev/null 2>&1; then
  HERMES_BIN="$(command -v hermes)"
else
  echo "Hermes binary not found. Run ./scripts/install-hermes.sh first." >&2
  exit 1
fi

export HERMES_HOME="$PROFILE_HOME"
exec "$HERMES_BIN" "$@"
