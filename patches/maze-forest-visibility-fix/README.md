Maze Forest visibility hotfix

Goal
Restore the maze canvas rendering under the HUD by fixing stacking (z-index) and canvas sizing, without changing game logic.

How to apply (quick)
1) Open maze-forest/index.html
   - Wrap the canvas and HUD in a positioned root using the snippet below.
   - Ensure the canvas comes before the HUD in the DOM.

2) Open maze-forest/styles.css
   - Append the CSS from snippets.css. It:
     - Positions the root, sizes the canvas area, and ensures the HUD cannot occlude the canvas.
     - Raises the canvas above any decorative overlays.

3) Open maze-forest/src/renderer.js (or src/game.js where you initialize the canvas)
   - Import or paste the fitCanvasToCSS/installCanvasFit helpers from runtime-fix.js.
   - Call installCanvasFit(document.getElementById('game')) early in your boot path.

Verify
- Hard refresh http://localhost:8000/maze-forest/
- Expect: maze visible, HUD top-left, keyboard works, no overlay blocking.

Emergency DevTools test (no file edits)
- See devtools-one-liners.txt for a 10-second test to confirm stacking is the issue.

Notes
- If your HUD is intentionally interactive, keep pointer-events enabled only on the specific controls (we already scope that in CSS).
- If you have a custom overlay element (e.g., .vignette/.frame), keep it but let the canvas sit above by z-index.
