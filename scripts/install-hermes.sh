#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${HERMES_STACK_VENV:-${OPENCLAW_HERMES_VENV:-$ROOT_DIR/state/hermes/venv}}"

mkdir -p "$ROOT_DIR/state/hermes"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install "hermes-agent[web,pty]" "psycopg[binary]" croniter "discord.py>=2,<3"
"$VENV_DIR/bin/python" "$ROOT_DIR/scripts/patch-hermes-browser-tool.py"

echo "Hermes installed in: $VENV_DIR"
echo "Binary: $VENV_DIR/bin/hermes"
