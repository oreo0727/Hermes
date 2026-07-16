Aetherion Maze Games — QA Patch Bundle

Contents:
1) narrative-movement-and-input.patch — Adds movement throttling, key-repeat guard, diagonal prevention, and overlay input lock to Narrative Prototype.
2) accessibility-overlay.patch — ARIA roles/labels + focus trap for the Narrative overlay. Restores focus on close.
3) cache-and-debug-gating.patch — Consistent DEBUG gating + cache-bust/version constant for both games.
4) cozy-theme.css — Small polish: warm palette vars, soft shadows, accessible focus states.
5) consolidate-maze-forest.sh — Safe script to dedupe nested maze-forest/maze-forest directory.

Assumptions:
- Narrative game paths: narrative-maze-prototype/index.html, js/input.js, js/ui.js (or similar). If files differ, adapt the patch hunks to your filenames.
- Maze Forest paths: maze-forest/index.html, js/*.js, css/*.css.
- These are unified patches in V4A multi-file format used by our patch tool; you can also apply manually.

How to use (recommended):
- Review diffs, then we can apply them directly to your repo after you confirm the exact paths. The consolidate script is non-destructive (rsync), but still back up or run under git.
