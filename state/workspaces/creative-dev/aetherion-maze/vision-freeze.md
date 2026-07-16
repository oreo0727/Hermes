Aetherion Maze — Vision Freeze (Creative Target)

Primary delivery target
- Canonical artifact: Godot 4 web export under /home/james/Hermes/state/projects/aetherion-maze/godot-web/ (index.html + index.js/wasm/pck).
- Source of truth for implementation: /home/james/Hermes/state/projects/aetherion-maze/godot-maze/ (project.godot).
- Review loop: served via COI dev server at http://localhost:8000/godot-web/.

Tone and aesthetic
- Cozy-ethereal forest maze: warm soil, friendly moss stone, soft vignette; no harsh contrast spikes.
- HUD is friendly and readable: Nunito Sans (regular/bold), subtle 2 px outline, soft shadow, crisp 18–20 px SVG icons (coin, key, heart), gold portrait ring.
- Ambient feel: gentle dapple optional; vignette subtly frames playfield (edge_opacity ~0.25–0.35).

Play experience
- Movement: grid-based, 4-directional; no diagonals. Pace is steady and contemplative, not twitch.
- Readability above all: exits glow; hazards and enemies are discernible against the cozy palette.
- Mobile is first-class: swipe/D-pad with ≥44 px targets and centered controls.

Creative pillars to PRESERVE (must not drift)
- Single canon: Godot project as the only implementation path (no parallel HTML/Canvas engines for primary delivery).
- Cozy HUD theme pack: res://res/HUD.tres + res/assets/ui/* (Nunito Sans variable TTF, SVG icons, portrait ring) applied consistently to all UI.
- Vignette layer below HUD: res/ui/Vignette.tscn with shader res/assets/ui/shaders/vignette.gdshader tuned for subtle edges.
- Palette tokens per docs: docs/ui/ui/palette-cozy.md — warm soil, friendly moss stone. Keep numerals ultra-legible (bold, 2 px outline).
- Version label placement: top-right within safe margin with extra 8–12 px inset; readable on all backdrops.
- Integer snapping for HUD and icons; no half-pixel haloing; image filtering off for icon vectors/PNGs.

What to DROP (from primary path)
- Legacy HTML5 prototypes (maze-groundup, maze-canvas) as shipping targets. Keep as reference only.
- CSS-only HUD polish path as a primary mechanism; Godot theme (.tres) and resources are the authority.
- Terrain sprite packs as default visuals; procedural/tiles remain primary unless an approved atlas is integrated without readability regressions.

Constraints and Do-NOT-drift guardrails
- Input: WASD/Arrows + Mobile swipe/D-pad; no diagonals; restart/mute shortcuts retained (R/M).
- Camera/Canvas: web export at comfortable base size (e.g., 960×960 viewport equivalence) with DPR-safe scaling; never double-apply DPR.
- Diagnostics are gated and off by default; no console errors in non-debug.
- Performance target: 60 fps on modest laptops; prefer graceful tile-size degrade over feature removal.

References (live in repo)
- Godot project: godot-maze/project.godot
- Web export (review): godot-web/index.html
- HUD pack + palette: docs/ui/ui/hud-pack.md, docs/ui/ui/palette-cozy.md
- HUD resources: godot-maze/res/HUD.tres, godot-maze/res/assets/ui/*, godot-maze/res/ui/Vignette.tscn

Acceptance linkage
- See acceptance-guardrails.md for checkable acceptance language aligned to this vision.

Status
- This document freezes the creative target for Aetherion Maze across all lanes. All downstream work must conform to these pillars and guardrails.
