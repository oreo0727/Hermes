Maze Forest — addLoops crash hotfix

Problem
- The generator can crash inside addLoops with errors like:
  - TypeError: Cannot read properties of undefined (reading 'z')
  - or similar when grid shape/values aren’t as expected.
- When addLoops throws, the maze never completes generation, leaving only the vignette/HUD visible.
- Inconsistencies were amplified by mixed script versions (e.g., generator.js?v=8 with game.js?v=9) and possibly duplicate directories.

Immediate unbreak (no file edits)
1) Open your running page (e.g., http://localhost:8000/maze-forest/)
2) Open DevTools → Console
3) Paste the contents of devtools-one-liners.txt and press Enter
   - This safely overrides addLoops with a guarded version and restarts the level.
   - You should see the maze render within a second.

Permanent fix (file edit)
1) Open your repo and locate the generator implementation used by Maze Forest, commonly:
   - maze-forest/src/generator.js (and also any nested duplicate copy, if present)
2) Replace the existing addLoops function with the implementation from addloops-safe.js
3) Bump cache-bust query params in maze-forest/index.html to force browsers to pull the new file, e.g., change ?v=9 → ?v=10 for all related scripts.
4) Hard refresh (Cmd/Ctrl+Shift+R) and confirm the maze renders. You can then hide dev overlays.

Why this is safe
- The new addLoops checks grid bounds, verifies floor/wall values, and no-ops if the grid shape is unexpected.
- It only opens walls between two valid floor cells two steps apart, preserving maze structure.

Suggested cleanup to prevent future inconsistencies
- If you have both maze-forest/ and maze-forest/maze-forest/ directories, update both or consolidate to one canonical copy. Mixed versions cause hard‑to‑reproduce bugs.

Verification
- After applying the devtools one-liner, you should see the maze reappear immediately.
- After the permanent patch and cache-bust, reload: there should be no generator errors, and addLoops will be stable across levels.
