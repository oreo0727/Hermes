Project Aetherion — Game Runbook (Local)

Current canonical review build
- Godot web export: `./state/projects/aetherion-maze/godot-web/index.html`

Legacy prototype references
- Maze Forest prototype: `./maze-forest/index.html`
- Narrative Maze prototype: `./narrative-maze-prototype/index.html`

Quick run (current review path)
1) `python3 state/projects/aetherion-maze/scripts/devserver_coi.py --dir state/projects/aetherion-maze --port 8000`
2) Open `http://localhost:8000/godot-web/`
3) Hard refresh with Ctrl/Cmd+Shift+R after any code change to bypass cache.

Quick run (legacy prototypes)
1) `./scripts/serve-games.sh 8000`
2) Open `http://localhost:8000/maze-forest/index.html`
   or `http://localhost:8000/narrative-maze-prototype/index.html`

Diagnostics
- A small magenta square at the top-left of the canvas confirms the renderer executed.
- An on-page black error box appears for any uncaught errors / unhandled promise rejections.

Shipping checklist
- Remove or gate diag overlay (src/diag.js) and the localStorage debug enable snippet in index.html.
- Remove cache-bust query params (e.g., ?v=1) or bump to a real version tag.
- Keep the defensive guards (grid presence, CSS var fallbacks, min tile size).

Known caveats
- There are duplicate Maze Forest sources under maze-forest/maze-forest. Canonical version is maze-forest/ (top-level). Consolidation recommended prior to release.
- The operator-facing review build has moved to `state/projects/aetherion-maze/godot-web/`; older `/maze-forest/` notes are now reference-only.
