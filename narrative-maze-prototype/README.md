# Narrative Maze Prototype

A browser-native, dependency-free prototype: a procedural maze with a narrative layer. Move tile-by-tile through a cozy forest labyrinth, encounter short story moments, and reach the glowing exit.

- Tech: HTML5 Canvas, vanilla JS (no bundler), defensive renderer guards, dev diagnostics overlay.
- Gameplay: recursive-backtracker maze, farthest exit via BFS, spaced narrative nodes along the main path.
- Controls: WASD/Arrows to move, R to restart.

## Run

- Easiest: open `index.html` in a modern browser.
- Recommended (crisper scaling + no local file restrictions):
  - `cd narrative-maze-prototype`
  - `python3 -m http.server 8000`
  - Visit http://localhost:8000

## Structure

- index.html — canvas + HUD + narrative overlay
- styles.css — cozy forest theme
- src/
  - diag.js — dev-only diagnostics badge and error capture (remove before shipping)
  - generator.js — maze generation (recursive backtracker), BFS farthest exit, primary path
  - input.js — WASD/Arrows, no diagonals
  - renderer.js — tiles, player, exit glow, story-node markers, defensive guards (no-op when level missing, `ts` clamp)
  - systems/narrative.js — story data + placement along primary path
  - game.js — state, loop, movement, narrative overlay orchestration, level transitions

## Notes

- Maze size scales with level: 15x15 base, grows by +2 per level (odd dimensions), clamped safeguards.
- Narrative nodes are placed at ~25%, 60%, and 85% along the main path.
- CSS variables color the scene; renderer uses safe fallbacks.

## Next Increments (planned)

- Seeded runs for reproducible layouts and shareable seeds.
- Simple audio chimes for story nodes and exit, with a mute toggle.
- Optional hazards/enemies (scaffold exists in our skill playbook) if desired by design.
- Narrative authoring format (JSON or lightweight DSL) with content loading.
