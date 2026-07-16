Aetherion Maze — Acceptance Guardrails (Creative → Game-Dev)

Scope: Godot 4 web export served from /godot-web/; source in /godot-maze/
Purpose: Concrete, checkable language that enforces the frozen creative target.

A. Visual + HUD
1) Theme application
- Root GUI Theme uses res://res/HUD.tres (Nunito Sans regular/bold). Default Label has 2 px dark outline and soft shadow.
- Count labels (e.g., coins/keys) render in bold with outline; numerals readable on both warm soil and moss stone.
- VERIFY: Open title/main scenes → labels render with outline and shadow; no fallback font.

2) Icons and portrait
- Coin/key/heart icons are vector-crisp at 18–20 px with no haloing; filtering disabled where vectors are rasterized.
- Portrait ring renders at ~56 px nominal with gold conic and inner bloom; sits cleanly behind portrait art.
- VERIFY: Inspect godot-maze/res/assets/ui/icons/*.svg in-scene at DPR 1–3.

3) Vignette and dapple
- Vignette (res/ui/Vignette.tscn) sits below HUD; edge_opacity in 0.25–0.35; center ~0.5, softness ~0.6.
- Optional dapple layer (scripts/Dapple.gd) is faint (opacity ≤ 0.08), below vignette; must not obscure HUD.
- VERIFY: Toggle layer visibility; HUD remains full-bright; vignette subtly darkens edges only.

4) Palette
- Cozy tokens present and honored: warm soil, friendly moss stone per docs/ui/ui/palette-cozy.md.
- No harsh contrast spikes; exits maintain readable glow.
- VERIFY: Visual compare against docs/ui/refs/target-ui-20260514.png.

B. Interaction + Readability
5) Input and pacing
- 4-way movement only; no diagonals. Pacing steady (cooldown ~100–140 ms baseline; haste halved) matching contemplative tone.
- Desktop: WASD/Arrows/R/M; Mobile: swipe + on-screen D-pad; D-pad targets ≥44 px and centered via integer math.
- VERIFY: Manual check on desktop + mobile simulator; D-pad hitboxes in debug overlay ≥44 px.

6) UI placement
- Version label sits inside the top-right global margin with 8–12 px additional inset; remains legible across scenes.
- HUD chips (if used) are faint (alpha ≤ 0.35) and never impede input.
- VERIFY: Resize viewport; placement remains within margin; pointer-events correct.

C. Packaging + Diagnostics
7) Export integrity
- Web export builds with export_presets.cfg → /godot-web/; index.{html,js,wasm,pck} present.
- No console errors in non-debug; build-version token surfaces in-game.
- VERIFY: Load http://localhost:8000/godot-web/ on COI server; console clean.

8) Diagnostics off by default
- Debug overlays, camera logs, and probes behind a flag; off in review build.
- VERIFY: No debug UI unless ?debug=1.

D. Performance
9) Frame-rate target
- 60 fps on modest laptops at comfortable viewport; graceful degrade (tile-size/FX) before readability regresses.
- VERIFY: Built-in FPS monitor or simple on-screen counter stays ~60 on main scene without large mazes.

Non-drift clauses (enforced)
- No parallel HTML5/Canvas engines as primary targets; legacy prototypes remain reference-only.
- Do not remove HUD theme, swap fonts, or alter icon sizing outside the documented ranges without Creative sign-off.
- Keep vignette below HUD; do not raise its opacity above 0.35.

References
- HUD pack docs: /home/james/Hermes/state/projects/aetherion-maze/docs/ui/ui/hud-pack.md
- Palette: /home/james/Hermes/state/projects/aetherion-maze/docs/ui/ui/palette-cozy.md
- Godot sources: /home/james/Hermes/state/projects/aetherion-maze/godot-maze/
- Web export: /home/james/Hermes/state/projects/aetherion-maze/godot-web/
