#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-operator}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

exec "$ROOT_DIR/scripts/run-hermes.sh" "$PROFILE" gateway
