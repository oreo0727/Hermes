# Lighting Rigs v0 — Campfire Repeat

Rig A — Embers Establishing (sf01)
- World: Moon HDRI 0.15 intensity, color temp ~9000K; rotation to rim trees.
- Fire: Point light at ring center (animated flicker 0.6–1.0x), warm (#FF9860), radius 0.4m.
- Fog: 3–4 planes (Z-stacked), alpha 0.15–0.25, noise texture panned slowly.
- God Rays: Fake with angled fog card near right treeline.

Rig B — Time Pop (sf02)
- As Rig A plus: match emissive sprite (burst 200ms), screen glare; ripple FX in comp.
- Extra spec highlight on faces (small area light 5% intensity) timed to flare.

Rig C — Missing Chair (sf03)
- Fire rim emphasized: increase fire light radius to 0.6m, intensity +20%.
- Practical negative fill: dark planes behind camera to keep BG down.
- DOF rack to empty chair.

Rig D — Phones-Only (sf04)
- Turn fire light off; coals emissive only (very low).
- 3–4 phone emissive quads (cool #AEE7FF), each ~2–4 cd, positioned near hands/faces.
- Minimal world light (0.02) to keep treeline barely present; add noise/grain in comp.

Rig E — Inserts (sf05–sf09)
- Phone OTS: add UI glow reflection; pull backworld to 0.08.
- Birch/marker: small cool kicker from camera left.
- Near-ignition: isolate with black flags; micro emissive pulse 100ms.

Rig F — Dawn (sf10)
- World gradient: sky ramp from cool to warm; add subtle volumetric bloom.
- Fire off; pocket ember emissive small.
