Maze Forest — Render Stability Fix

Goal
Stop the “all over the place” mosaic by stabilizing canvas DPR and guarding sprite sampling.

Two ways to use it

A) 10‑second live hotfix (no file edits)
1) Open your running game (e.g., http://localhost:8000/maze-forest/)
2) DevTools → Console → paste the contents of:
   patches/maze-render-stability-fix/devtools-one-liners.txt
3) Expected immediately:
   - Canvas fits to devicePixelRatio and disables smoothing.
   - drawImage() wrapper rounds/clamps source rects to avoid atlas edge bleed and out-of-bounds.
   - The board stops showing random sprite fragments.

B) Permanent one‑line include (recommended)
1) In maze-forest/index.html, before your other game scripts, add:
   <script src="patches/maze-render-stability-fix/runtime-stability-shim.js?v=10"></script>
2) Hard refresh (Cmd/Ctrl+Shift+R).

What the shim does
- Fits the canvas backing store to CSS size × DPR, sets ctx.setTransform(DPR,…), and turns off image smoothing.
- Wraps CanvasRenderingContext2D.drawImage so 9‑arg calls (sx,sy,sw,sh,dx,dy,dw,dh):
  - Round and clamp sx/sy/sw/sh to integer in‑bounds pixels.
  - Nudge 1px inward to reduce atlas edge bleed when there’s no extrusion.
  - Round destination dx/dy/dw/dh for crisp placement.
  - If a call is invalid (NaN, negative, zero sizes, or out of bounds), it draws a readable block instead of sampling random atlas garbage.

Why this works
- Your screenshot shows a uniform destination grid but wrong source sampling from a big spritesheet (hero/door/villager bits in wall tiles) and occasional 1px seams. That’s classic UV mismatch + DPR rounding. This shim addresses both without touching your source files.

Next hardening (after you confirm stability)
- Source‑level fixes I can land next (cleaner and faster than a shim):
  - In src/game.js: set canvas width/height = client × DPR once; setTransform once; don’t re‑multiply later.
  - In src/renderer.js: snap tile sizes to “nice” device‑pixel integers; draw at integer coords; keep smoothing off.
  - In src/assets*.js: ensure drawSprite uses natural image pixels for sx/sy/sw/sh, not tileSize‑scaled math; correctly handle @2x/@3x atlases without double‑applying DPR.

If you want me to patch files directly
- Tell me the on‑disk path to the served maze‑forest/index.html. I’ll add the script include, unify cache‑bust to v=10, and prepare targeted diffs for the source files so we can remove the shim later.
