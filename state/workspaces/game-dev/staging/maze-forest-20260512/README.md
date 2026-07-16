Maze Forest
===========
A cozy, procedural top-down maze that guarantees a solvable path each level, adds gentle loops for variety, and layers in enemies, traps, and power-ups. Difficulty scales as you progress.

Play
- Controls: WASD/Arrows to move, R to restart, M to mute.
- Goal: Reach the softly glowing exit. Each level gets larger and a bit busier.
- Hazards: Enemies roam and chase if they see you in a straight line. Traps toggle on a cycle.
- Power-ups: Heal (+2 hearts), Shield (block 1 hit), Speed (short haste).

Run locally (recommended)
1) From the directory above maze-forest/, run a simple server:
   python3 -m http.server 8000
2) Open in a browser:
   http://localhost:8000/maze-forest/

Remote-friendly options
- GitHub Pages (best for sharing): push this folder to a repo, enable Pages, and set the site root to / (or /maze-forest subdir).
- Netlify/Vercel: drag-drop the folder in their UI for instant static hosting.
- SSH port forward: if you have shell on the box that runs the server, tunnel 8000 and open the forwarded port in your browser.

Notes on guarantees
- Solvable path: Maze is carved as a perfect maze; exit is placed at the farthest reachable tile from start (via BFS), ensuring a meaningful route.
- Difficulty curve: Slightly increases size, enemy count, trap density, and reduces power-up frequency. Levels are capped for performance.

Next steps (optional)
- Tileset pass (trees, grass variants, exit rune), light fog-of-war glow, soft SFX.
- Smarter enemies (A* bursts) with telegraphed behavior; separate archetypes.
- Seeded runs and share codes, mobile touch controls, accessibility toggles.
