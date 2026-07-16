Maze Forest — Visual Polish v2 (Cozy, Crisp, Readable)

Goal
Make the existing reliable build look cozy and high-contrast: beveled mossy walls, warm soil floors with subtle variation and decals, brighter exit glow, chunkier entities, and a softer vignette. No sprites required; works purely procedural. Optional: add the Google font for HUD.

What’s included
- renderer.js — drop-in upgraded procedural renderer (cozy forest aesthetic). Replace your maze-forest/src/renderer.js with this.
- styles-tokens.css — CSS tokens for colors and HUD friendliness. Append into maze-forest/styles.css (or import).
- index-snippet.html — Google font preconnect/import lines. Paste near the top of <head> (optional).
- devtools-one-liners.txt — paste into DevTools to preview crispness + vignette tuning immediately (no file edits) while you line up the patch.

Install (2–3 minutes)
1) Replace renderer
- Copy patches/maze-forest-polish-v2/renderer.js to maze-forest/src/renderer.js (overwrite existing).

2) Add/merge CSS tokens
- Append the contents of patches/maze-forest-polish-v2/styles-tokens.css to maze-forest/styles.css (end of file is fine).

3) Optional: HUD font
- Paste the contents of patches/maze-forest-polish-v2/index-snippet.html into your <head> block in maze-forest/index.html.

4) Bump cache-bust
- In maze-forest/index.html, increment all ?v= to ?v=12 (or a higher number) to ensure the browser fetches the new JS/CSS.

5) Hard refresh
- Cmd/Ctrl+Shift+R on http://localhost:8000/maze-forest/
- Expect: rounded mossy walls with bevel, warm soil floors with slight variation, brighter exit glow, chunkier player/enemy/traps/powerups, and a softer vignette. Edges are crisp.

Quick preview (no edits)
- While the page is running, open DevTools → Console → paste everything from patches/maze-forest-polish-v2/devtools-one-liners.txt to see crisper draw and gentler vignette immediately. Proceed with file changes to make it permanent.

Notes
- This renderer is fully procedural and tolerant to grid semantics (0/1 or 1/0 for wall/floor). If your build uses level.exit, it will draw a glow there; if it has a tile value 2 for exit, it will also honor that.
- Performance: shadows and glows scale with tile size. If you push tiles very large (>96px), you can tune the shadow/blur multipliers in the code comments.

Verification
- No white/blank canvas on load.
- Player/enemies/traps/powerups visually chunkier and readable at a glance.
- Exit glow draws and is easy to spot.
- Soft vignette is visible but not crushing the edges.

Ship gating
- Keep defensive guards in renderer.js.
- Remove any magenta “probe” calls you may have in your local renderer once you’re satisfied.
