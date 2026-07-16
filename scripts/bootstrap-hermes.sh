#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p \
  "$ROOT_DIR/state/hermes" \
  "$ROOT_DIR/state/hermes/profiles" \
  "$ROOT_DIR/state/hermes/logs"

python3 -m hermes_stack.scaffold --root-dir "$ROOT_DIR" bootstrap >/dev/null

echo "Hermes profile homes generated under: $ROOT_DIR/state/hermes/profiles"
echo "Next:"
echo "  1. Run ./scripts/install-hermes.sh"
echo "  2. Start a profile gateway, e.g. ./scripts/run-hermes-gateway.sh operator"
echo "  3. Start the operator portal with ./scripts/run-operator-portal.sh"
