#!/usr/bin/env bash
set -euo pipefail

# Apply Cozy Toggle UI to Maze Forest
# Usage: ./apply_cozy_toggle.sh /home/james/Hermes/state/projects/aetherion-maze

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <PROJECT_ROOT>" >&2
  exit 1
fi
PRJ="$1"
MF_DIR="$PRJ/maze-forest"

if [[ ! -d "$MF_DIR" ]]; then
  echo "Error: Maze Forest dir not found: $MF_DIR" >&2
  exit 1
fi

# Copy JS file
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$MF_DIR/src"
cp -f "$SRC_DIR/src/cozy-toggle.js" "$MF_DIR/src/cozy-toggle.js"

# Apply patch (paths are relative to project root)
PATCH_FILE="$SRC_DIR/maze-forest-cozy-toggle.patch"
if command -v git >/dev/null 2>&1; then
  (cd "$PRJ" && git apply --index "$PATCH_FILE" || git apply "$PATCH_FILE") || {
    echo "git apply failed; trying patch(1)" >&2
    (cd "$PRJ" && patch -p0 -i "$PATCH_FILE")
  }
else
  (cd "$PRJ" && patch -p0 -i "$PATCH_FILE")
fi

echo "Cozy toggle applied. Verify at http://localhost:8000/maze-forest/"
