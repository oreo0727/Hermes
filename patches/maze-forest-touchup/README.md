Maze Forest Touch‑Up Kit

Purpose
Make the board read bigger and clearer immediately, without new art. Improves crispness, raises entity proportions, softens the vignette, and adds HUD readability. Fully reversible. Safe with or without sprites.

What this kit does
- Pixel‑crisp rendering: disables canvas image smoothing and snaps to device pixels; adds CSS image‑rendering: pixelated.
- Bigger, clearer gameplay: larger target tile; larger player/enemy/power‑up/trap proportions; stronger exit pop.
- Gentler vignette + calmer floor: optional tint/contrast softening to stop floor noise from competing with gameplay.
- Minimal HUD framing: optional small translucent bar for immediate legibility.

How to apply (2–3 tiny edits)
1) Include the config + runtime touchups in maze-forest/index.html BEFORE your game scripts:

  <script src="patches/maze-forest-touchup/touchup-config.js?v=1"></script>
  <script src="patches/maze-forest-touchup/touchup-runtime.js?v=1"></script>
  <!-- optional HUD bar styles -->
  <link rel="stylesheet" href="patches/maze-forest-touchup/touchup-styles.css?v=1">

2) After you acquire the canvas in src/game.js (or wherever you boot):

  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  if (window.installCanvasCrisp) window.installCanvasCrisp(canvas, ctx);

  // If you use our tile sizing helper (recommended):
  // const ts = window.computeNiceTileSize(canvas.clientWidth, canvas.clientHeight, rows, cols, (window.MAZE_OPTS||{}).targetTile);

3) (Optional but recommended) If you have a vignette/end‑of‑frame pass:
   - Call window.touchupEndOfFrame(ctx, canvas.width, canvas.height, devicePixelRatio) after your normal draw. If you don’t have a post pass, you can skip this; the kit still helps via crispness + sizes.

DevTools 10‑second smoke test (no file edits)
- Paste the contents of devtools-one-liners.txt into the Console on a running page to preview crispness + sizing + softer vignette immediately. If you like it, wire in the scripts above.

Safe defaults (can be tweaked in touchup-config.js)
- Tile target: 80 px (snapped to a crisp size)
- Entity scales: player 0.96, enemy 0.86, power‑up 0.78, trap 0.68
- Vignette: strength 0.35, radius 0.90 (gentler than now)
- Exit pop: +30% brightness with soft additive glow

Notes
- This kit does not hard‑patch your renderer; it provides helpers + config you can call. If you want me to land the exact edits in your renderer.js for you, say “apply touchups directly” and I’ll patch the repo.
- If you provide @2x/@3x atlases, your existing adaptive loader will pick them; the crispness helpers keep them sharp at larger tiles.
