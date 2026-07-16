#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${HERMES_OPERATOR_PORTAL_PORT:-${OPENCLAW_OPERATOR_PORTAL_PORT:-8799}}"
HOST="${HERMES_OPERATOR_PORTAL_HOST:-${OPENCLAW_OPERATOR_PORTAL_HOST:-0.0.0.0}}"
cd "$ROOT_DIR"

exec python3 -m hermes_stack.operator_portal.server --root-dir "$ROOT_DIR" --host "$HOST" --port "$PORT"
