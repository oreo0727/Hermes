Maze UI Activation Kit

Purpose
Ensure the Maze Forest game UI (HUD and overlay) is actively visible, layered above the canvas without blocking input, and verified at runtime with a visible badge + console log. This is non-destructive and reversible.

What this gives you
- UI ACTIVE badge (top-left) so you can instantly confirm the UI system mounted.
- Safe layering: canvas paints; HUD sits above; HUD doesn’t intercept input unless a control needs it.
- Keyboard toggles: H to toggle HUD visibility; ? to show a short help panel; Esc to close help.
- Pointer-events rules that keep HUD non-blocking by default, but allow buttons/links to work.
- DevTools one‑liners to prove it without editing files.

Files
- patches/maze-ui-activation/ui-activate.js — runtime installer that activates HUD, layering, and toggles.
- patches/maze-ui-activation/hud-sanity.css — CSS to contain + layer HUD safely.
- patches/maze-ui-activation/hud-snippet.html — minimal HUD block to paste if you don’t have one.
- patches/maze-ui-activation/devtools-one-liners.txt — quick verification without editing.

How to integrate (2 small steps)
1) index.html — include before your game scripts:
   <link rel="stylesheet" href="patches/maze-ui-activation/hud-sanity.css?v=1">
   <script src="patches/maze-ui-activation/ui-activate.js?v=1"></script>

2) Ensure your DOM has a canvas followed by HUD inside a positioned root (example):
   <div id="gameRoot" data-game="maze-forest">
     <canvas id="game" width="720" height="720"></canvas>
     <div id="hudTL" aria-hidden="false"><!-- your HUD goes here --></div>
   </div>
   If you don’t have HUD markup, paste patches/maze-ui-activation/hud-snippet.html inside gameRoot.

3) Hard refresh (Cmd/Ctrl+Shift+R). Expect to see a small "UI ACTIVE" badge at top-left; HUD visible; keyboard works.

Optional: DevTools verification (no file edits)
- Open your running page and paste the contents of devtools-one-liners.txt into the Console. You should immediately see the UI ACTIVE badge, HUD unblocked, and help toggle on ?.

Removal
- Remove the <link> and <script> from index.html to disable; your original HUD remains.
