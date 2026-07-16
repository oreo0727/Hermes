Maze Forest HUD + Canvas Layering Hotfix

Goal
Fix the regression where the HUD overlays or collapses the canvas, causing the maze not to render. This hotfix:
- Ensures canvas paints at non-zero size (CSS + DPR-aware JS sizing).
- Places HUD above the canvas without blocking input.
- Prevents global CSS from blanking the canvas.

Files to modify (in your repo)
- maze-forest/index.html
- maze-forest/styles.css
- maze-forest/src/renderer.js (or wherever your draw loop bootstraps the canvas)

How to apply
1) Update DOM structure in maze-forest/index.html
   - Wrap canvas and HUD in a positioned root.
   - Keep canvas before the HUD so z-index stacking is deterministic.

   Replace the existing game root with this block (adjust widths as you like):

   <div id="gameRoot" data-game="maze-forest">
     <canvas id="game" width="960" height="960"></canvas>
     <!-- HUD lives after canvas to sit above it -->
     <div id="hudTL" aria-hidden="false">
       <!-- existing HUD content here -->
     </div>
   </div>

2) Add/merge the CSS rules from snippets.css into maze-forest/styles.css
   - This sets the stacking order and prevents HUD from occluding the canvas.

3) Add/merge the JS from fit-canvas.js into your renderer boot (maze-forest/src/renderer.js)
   - Call fitCanvasToCSS() on load and on resize, before drawing.

4) Reload http://localhost:8000/maze-forest/
   - Expected: maze renders again, HUD is visible top-left, input unaffected.

If your project uses different IDs
- Update #gameRoot, #game, and #hudTL selectors in CSS and JS accordingly.

Notes
- If you previously set transform every frame, remove the duplicate or it will compound.
- If any global CSS sets #hudTL to position: fixed; inset: 0; or applies an opaque background, remove/override it inside maze-forest only.

Rollback
- All changes are additive/safe. Remove the inserted blocks to revert.

