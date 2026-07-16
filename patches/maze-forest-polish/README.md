Maze Forest — Bigger, better-looking tiles and entities (scale-up kit)

Goal
Make the player, enemies, traps, and power-ups larger and more readable without blurring, while keeping the cozy aesthetic and crisp edges.

Overview
This kit adds a configurable scale for tile size and entity proportions. It works for both purely procedural rendering and sprite-based rendering (with automatic 1x/2x/3x asset selection if you later add bigger spritesheets).

What you get
- config.js — runtime knobs: targetTile, entityScale, shadowScale, vignetteStrength
- runtime-fit-canvas.js — DPR-aware canvas sizing helper (safe to include even if you already size)
- renderer-scale-snippet.js — drop-in functions to compute tile size and consistent entity scaling
- assets-adapter.js — optional: pick spritesheet resolution bucket (1x/2x/3x) if you add larger assets later

Integration (5 minutes)
1) Include the config and canvas-fit before your game/renderer scripts (index.html):
   <script src="patches/maze-forest-polish/config.js?v=1"></script>
   <script src="patches/maze-forest-polish/runtime-fit-canvas.js?v=1"></script>
   <!-- your existing scripts after these -->

2) In your game boot (e.g., src/game.js), install DPR fit once the canvas exists:
   // after const canvas = document.getElementById('game')
   if (window.installCanvasFit) { window.installCanvasFit(canvas); }

3) In your renderer (e.g., src/renderer.js), use computeTileSize and scale constants:
   // near the top of your render() or init
   const opts = (window.MAZE_OPTS||{});
   const ts = window.computeTileSize(W, H, rows, cols, opts.targetTile||72);
   const SCALE = opts.entityScale || 1.2;          // bigger entities
   const SHADOW = (opts.shadowScale||1.2);         // slightly stronger shadows on bigger tiles
   const VIGNETTE = (opts.vignetteStrength||0.5);  // 0..1

   // Examples:
   // player rect: roundedRect(ctx, x+2, y+2, ts-4, ts-4, Math.max(4, ts*0.2)*SCALE_PAD)
   // enemy size: let side = ts*0.7*SCALE; draw at (x + ts*0.15 - extra, y + ts*0.15 - extra)

4) If you draw shadows/glow, multiply blur/offset by SHADOW:
   ctx.shadowBlur = Math.max(4, ts*0.2) * SHADOW;
   ctx.shadowOffsetY = Math.max(2, ts*0.1) * (0.75 + 0.25*SHADOW);

5) Optional (sprites later): include assets-adapter.js before your atlas loader and let it choose the best spritesheet size if you add @2x/@3x.

Runtime knobs (config.js)
- targetTile (default 72): approximate on-screen tile size in CSS pixels. Renderer snaps to a “nice” size close to this for crispness.
- entityScale (default 1.2): scales player/enemies/power-ups so they read stronger inside larger tiles.
- shadowScale (default 1.2): increases blur/offset a bit so objects stay grounded when bigger.
- vignetteStrength (default 0.5): balances the soft frame as tiles grow.

Why bigger source assets help
- If you render with sprites: larger source atlas (@2x or @3x) preserves detail when tiles grow, especially on high-DPR screens. The adapter picks the tightest sheet that is >= the required pixel size to avoid upscale blur.
- If you render procedurally (no sprites): not required. Bigger visuals come purely from ts and SCALE; Canvas draws remain crisp.

Rollback
- Delete the three script tags and remove calls to window.computeTileSize/installCanvasFit. Rendering falls back to your original setup.

Verification checklist
- Player/enemies/power-ups are visibly larger and sharper.
- No blur: edges remain crisp; text/HUD unaffected.
- Performance steady: shadows/glows aren’t overblown.
- Resizing the window keeps tiles near the target size without jitter.
