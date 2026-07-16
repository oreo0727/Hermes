Aetherion Maze — Maze Forest Cozy Mode Toggle UI

Objective
- Cozy Mode visuals are default ON (already implemented via src/flags.js: MF_COZY_MODE).
- This add-on provides a clean, accessible in-game toggle (top-right) to switch Cozy visuals On/Off and persist via localStorage (MF_COZY).
- Toggle updates take effect immediately without reload; renderer reads window.MF_COZY_MODE each frame.

Files in this bundle
- src/cozy-toggle.js — Minimal, dependency-free UI toggle that:
  - Creates/uses a #hudTR container (top-right) with a button #btnCozy.
  - Reflects current state, toggles MF_COZY in localStorage, updates window.MF_COZY_MODE.
  - Emits a window event 'mf:cozy-changed' for any future listeners.

How to integrate (non-destructive)
1) Copy the file:
   - From: /home/james/Hermes/state/workspaces/game-dev/aetherion-maze/cozy-toggle/src/cozy-toggle.js
   - To:   <project>/maze-forest/src/cozy-toggle.js

2) Add script include in maze-forest/index.html
   Place after flags.js so MF_COZY_MODE is initialized first (and before game loop is started, though dynamic change is supported):

   <script src="src/flags.js?v=REPLACE_WITH_BUILD"></script>
   <script src="src/diag.js?v=REPLACE_WITH_BUILD"></script>
   <!-- Add this new line: -->
   <script src="src/cozy-toggle.js?v=REPLACE_WITH_BUILD"></script>

   Note: If you prefer not to bump cache right now, you can omit ?v=...

3) Add minimal CSS for the control (maze-forest/styles.css)
   Paste near the HUD styles section:

   /* Cozy toggle (top-right) */
   #hudTR.ui-controls{ position:absolute; top:8px; right:8px; z-index:4; pointer-events:auto; display:flex; gap:8px; }
   #hudTR #btnCozy{
     appearance:none; border:0; border-radius:999px; padding:8px 12px; font-weight:800; letter-spacing:.2px;
     background:linear-gradient(180deg, rgba(255,255,255,0.12) 0%, rgba(0,0,0,0.35) 100%);
     color:var(--ink, #e9f3e7); box-shadow:0 2px 6px rgba(0,0,0,0.35), inset 0 0 0 2px rgba(255,255,255,0.12);
     cursor:pointer; pointer-events:auto;
   }
   #hudTR #btnCozy.off{ opacity:.8; filter:saturate(.85); }
   #hudTR #btnCozy:focus-visible{ outline: 2px solid #a6f2c1; outline-offset:2px; }

4) Verify
   - Load http://localhost:8000/maze-forest/
   - Cozy visuals should already be ON (procedural terrain; sprites only for characters/FX as applicable).
   - Click the "Cozy: On" pill — it should switch to "Cozy: Off" and terrain sprites (if available) will render accordingly.
   - Reload — the last setting persists via localStorage MF_COZY.
   - URL overrides still work: ?cozy=0 forces Off, ?cozy=1 forces On (takes precedence over localStorage for that session).

Notes
- The renderer checks window.MF_COZY_MODE every frame (no reload required).
- Decals: In renderer.js, decals are skipped in Cozy unless MF_DECALS='1' in localStorage or MF_DECALS_ON is set.
- Accessibility: The button exposes aria-pressed and a descriptive title; #hudTR uses role="region" with an aria-label.

Rollback
- To remove the UI, delete src/cozy-toggle.js and the CSS block; the default Cozy behavior remains controlled by flags.js and URL/localStorage.

Changelog stub suggestion
- Add to CHANGELOG_maze-forest_YYYYMMDD.md:
  "Enabled Cozy visuals by default with an in-game toggle (top-right). Toggle persists to localStorage and remains overridable via ?cozy=0/1."
