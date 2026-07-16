Maze Forest — Stabilize v11

Goal
- Stop generator crashes (addLoops), remove chopped/mosaic sprites, and make the canvas crisp and aligned on all DPRs. This gives you a reliable, playable build now.

Contents
- addloops-safe.js — a bounds-checked, non-throwing addLoops replacement
- runtime-stability-shim.js — DPR-fit + smoothing-off; optional guarded draw wrapper
- devtools-one-liners.txt — paste into DevTools to unbreak in 10 seconds (no file edits)

Quick path (10 seconds, no edits)
1) Open http://localhost:8000/maze-forest/
2) DevTools → Console → paste the entire contents of devtools-one-liners.txt
3) Expect: no in-page error, maze renders, sprites gated off (procedural visuals), crisp tiles

Permanent patch (2–3 minutes)
1) Replace addLoops in maze-forest/src/generator.js with the function from addloops-safe.js.
   - Add at file top: console.log('MazeGen: generator.js v11 loaded')
   - Wrap the addLoops invocation in a try/catch if it isn’t already.

   Example around your generation:
     let grid = carveMaze(w,h,rng);
     try { addLoops(grid, levelParams(level).loopAttempts, rng); }
     catch(e) { console.warn('addLoops failed; continuing without loops:', e); }

2) Fit canvas to CSS×DPR once at boot and disable smoothing
   - In maze-forest/src/game.js (or your boot), after creating ctx:
       function fitCanvasToCSS(canvas, ctx){
         const dpr = Math.max(1, window.devicePixelRatio||1);
         const cssW = Math.floor(canvas.clientWidth||720);
         const cssH = Math.floor(canvas.clientHeight||720);
         if(!cssW || !cssH) return;
         canvas.width = Math.max(1, cssW*dpr);
         canvas.height = Math.max(1, cssH*dpr);
         ctx.setTransform(dpr,0,0,dpr,0,0);
         ctx.imageSmoothingEnabled = false;
       }
       fitCanvasToCSS(canvas, ctx);
       window.addEventListener('resize', ()=>setTimeout(()=>fitCanvasToCSS(canvas, ctx), 0));

3) Temporarily gate sprites until atlas mapping is verified
   - In maze-forest/index.html (inside <head> or before your scripts):
       <script>try{localStorage.setItem('mf_no_sprites','1'); localStorage.setItem('mf_debug','1');}catch(e){}</script>
   - In your renderer, prefer procedural path if localStorage.mf_no_sprites === '1'.

4) Unify cache-bust to v=11 on all <script src="...?."> tags in maze-forest/index.html
   - This kills version skew so you don’t run a mix of v9/v10 files.

5) Hard refresh (Cmd/Ctrl+Shift+R) and confirm in Console: MazeGen: generator.js v11 loaded

After stability
- Correct the atlas UVs (cell size, padding, DPR) and then set mf_no_sprites='0' to re-enable sprites cleanly.
- Optionally consolidate any duplicate directories (e.g., maze-forest/maze-forest/) to prevent future skew.
