Handoff to Game-Dev — Implement to Vision Freeze

Primary task (start here)
- Re-export Godot web build conforming to Acceptance Guardrails and place in /godot-web/. Verify HUD theme, icons, vignette ordering, and input pacing. Deliver a short QA note listing which guardrails were verified.

Checklist
1) Project setup
- Open godot-maze/project.godot in Godot 4.x.
- Ensure HUD.tres is applied at Project Settings > GUI > Theme or root Controls in title/main scenes.
- Confirm res/assets/ui/fonts NunitoSans variable TTF is referenced via FontFile .tres with variation_opentype weights (400/800).

2) Scene verification
- Title.tscn/main.tscn: labels show 2 px outline + soft shadow. CountLabel/Bold for numerals.
- Vignette.tscn present as CanvasLayer below HUD; edge_opacity ~0.3, softness ~0.6.
- (Optional) Dapple.gd layer present but faint; below vignette.
- VersionLabel.gd positioned within top-right safe area + 8–12 px inset.

3) Input and D-pad
- Desktop: WASD/Arrows/R/M work; no diagonals.
- Mobile: Swipe and MobileDPad.tscn in-scene; buttons ≥44 px; integer-centering.

4) Export
- Use export_presets.cfg target Web; export to /godot-web/.
- Bump cache-buster query param or build token to prevent stale JS/wasm.

5) Verify (COI server)
- Run scripts/devserver_coi.py on :8000; open /godot-web/.
- Console: no errors; ?debug=1 reveals overlays when needed; default is clean.
- Visual: HUD legible, icons crisp at DPR 1–3; vignette below HUD; palette matches docs.
- Performance: ~60 fps at comfortable viewport; no GC spikes in hot loops.

Acceptance references
- Vision freeze: /home/james/Hermes/state/workspaces/creative-dev/aetherion-maze/vision-freeze.md
- Acceptance guardrails: /home/james/Hermes/state/workspaces/creative-dev/aetherion-maze/acceptance-guardrails.md
- HUD/palette docs: /home/james/Hermes/state/projects/aetherion-maze/docs/ui/ui/hud-pack.md, palette-cozy.md

Deliverable
- Updated /godot-web/ build
- QA verification note (bulleted) listing which guardrails you validated and any deviations to flag back to Creative.
