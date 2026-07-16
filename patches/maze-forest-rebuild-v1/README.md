Maze Forest — Clean Rebuild (v1)

Purpose
- Provide a stable, DPR-safe, dependency-free Maze Forest that always renders, never throws in generator, and uses crisp procedural visuals by default. Sprites can be reintroduced behind a flag later.

What’s included
- index.html — minimal shell with gameRoot, canvas, and HUD.
- styles.css — cozy theme, safe stacking, readable focus.
- src/
  - diag.js — dev-only overlay + error capture (visible; gate/remove for ship).
  - generator.js — hardened recursive backtracker + BFS farthest exit + guarded addLoops (no-throw).
  - input.js — WASD/Arrows, tile-step with cooldown, no diagonals.
  - renderer.js — procedural cozy forest (walls/floors/exit/player/enemy/trap/powerup) with crisp pixels.
  - game.js — boot/loop/state, DPR-fit canvas once, version log, HUD binding.
- scripts/serve.sh — run a local server easily.

How to install (safe replace)
1) Backup your current Maze Forest directory served at /maze-forest/.
   - Example: mv maze-forest maze-forest.bak-$(date +%Y%m%d-%H%M%S)
2) Copy this rebuild in its place:
   - mkdir -p maze-forest; cp -R patches/maze-forest-rebuild-v1/* maze-forest/
3) Serve and test:
   - cd maze-forest && bash scripts/serve.sh 8000
   - Open http://localhost:8000/maze-forest/
4) Verify checklist:
   - You see a small purple "Renderer probe" badge (dev-only).
   - The maze renders immediately, no errors.
   - Player moves one tile per key; enemies/traps/powerups behave.
   - HUD updates level/hearts/counters.

Ship mode toggle
- To hide diagnostics: comment out the diag.js include in index.html and set MF_DEBUG=0.
- Defensive guards in generator/renderer remain permanently.

Notes
- This rebuild is procedural-only by default; sprite support can be layered on after stability is confirmed.
- If you wish, keep your previous project as maze-forest-legacy/ for reference.
