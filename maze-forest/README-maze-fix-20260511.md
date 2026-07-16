Maze Forest: generator + renderer stabilization (2026-05-11)

Changes included in this patch set
- src/generator.js (v5):
  - Replaced all for…of with classic indexed loops (no reliance on Symbol.iterator)
  - Strict in-bounds mid-cell guard during carving to prevent -1/undefined writes
  - Defensive addLoops() and BFS logic
  - Lightweight console markers: `MazeGen: generator.js v5 loaded` and a size/loops debug line
- src/renderer.js:
  - High-contrast fallback theme and CSS var fallbacks
  - Safe guards for missing grid or zero tile size; min tile size = 8px
  - Centering with ox/oy and subtle gridlines for readability
  - Draw order: cells -> gridlines -> exit/start -> traps/powerups/enemies -> player
  - Debug probe + console.debug gated by ?debug=1 or localStorage.mf_debug = '1'
- src/diag.js:
  - Debug-only overlay (badge + error capture). Hidden by default; enable with ?debug=1

How to integrate (1–2 minutes)
1) Replace your files with the ones in src/ (generator.js, renderer.js, diag.js).
2) In index.html, ensure the following script order near the end of <body> (or after the canvas):
   <script src="src/generator.js?v=5"></script>
   <script src="src/renderer.js?v=1"></script>
   <script src="src/diag.js?v=1"></script>
   <script src="src/game.js"></script>
   Notes:
   - Put generator.js before game.js so game init sees MazeGen.
   - diag.js is optional and only shows when ?debug=1 or localStorage.mf_debug='1'.
3) Hard-refresh (Ctrl/Cmd+Shift+R) to bypass cache.

Verification
- Open DevTools → Console. You should see: MazeGen: generator.js v5 loaded
- With ?debug=1 in the URL, you should see a small magenta badge (Renderer probe) and a console line: Renderer debug: { rows, cols, ts, ... }
- The canvas should display a visible maze with centered layout, legible tiles, exit (gold), player (salmon), walls (deep green).

Toggles
- Enable debug: add ?debug=1 to URL or run localStorage.setItem('mf_debug','1') in console.
- Disable debug: remove query or run localStorage.removeItem('mf_debug').

Notes
- The patch avoids engine-specific iterator quirks and transient zero-sized tiles.
- If you theme via CSS variables (e.g., :root { --mf-wall: #... }), the renderer will use them; otherwise, it falls back to safe defaults.
