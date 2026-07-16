#!/usr/bin/env bash
set -euo pipefail

PRJ_ROOT="${1:-$(pwd)}"
INNER="$PRJ_ROOT/maze-forest/maze-forest"
OUTER="$PRJ_ROOT/maze-forest"

if [[ ! -d "$OUTER" ]]; then
  echo "[error] $OUTER does not exist. Run from project root or pass path as arg." >&2
  exit 1
fi

if [[ ! -d "$INNER" ]]; then
  echo "[ok] No nested maze-forest/maze-forest directory; nothing to consolidate."
  exit 0
fi

echo "[info] Consolidating nested $INNER into $OUTER ..."
# Safety: ensure git is clean if repo
if command -v git >/dev/null 2>&1 && [[ -d "$PRJ_ROOT/.git" ]]; then
  if [[ -n "$(git -C "$PRJ_ROOT" status --porcelain)" ]]; then
    echo "[warn] Uncommitted changes detected. Consider committing/stashing before proceeding." >&2
  fi
fi

# Move all inner contents up one level
rsync -a --remove-source-files "$INNER/" "$OUTER/"

# Remove now-empty inner dir
rmdir "$INNER"

# Attempt to fix index.html/link/script href/src paths that double-include maze-forest/
fix_paths() {
  local file="$1"
  if [[ -f "$file" ]]; then
    sed -i.bak -E 's#(src|href)=("|\')((\.?/)*maze-forest/)#\1=\2#g' "$file"
  fi
}

export -f fix_paths
find "$OUTER" -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) -exec bash -c 'fix_paths "$0"' {} \;

echo "[done] Consolidation complete. Backups (*.bak) created for modified files. Review diffs before deleting backups."
