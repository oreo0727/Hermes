# Midnight Signals — Previz v1 Brief (Character Motion)

Goal
- Replace static storyboard frames in Animatic v3 with a low-fidelity animated previz so character motion and beats read clearly before final look.

Scope (shots)
- f02 First strike — 2.5s: One teen leans in, strikes; others react subtly (head turns, eye-lines). Small flare at ignition.
- f05 All together — 2.5s: Five teens shift weight, glance, one gestures with stick; micro head/shoulder motion.
- f07 Live Photo find — 2.5s OTS: Foreground teen raises/tilts phone; background heads turn toward screen; slight camera up-tilt.
- f08 Phones only — 2.5s: Phones raise/lower slightly; faces catch pulsing screen light; minimal body motion, no fire.
- f09 Almost ignition — 2.5s: Macro tinder/embers only (no characters); tiny handheld drift and sparks.
- f10 Dawn pocket glow — 2.5s: Subtle head turns, one hand to pocket; ambient dawn lift.

Environment anchors (must match boards v3)
- Tent back-center; lantern left foreground; right-side wooden sign; central fire ring; moonlit forest palette.

Previz approach (two viable routes)
1) NPR 3D blocking (preferred for motion truth)
   - Simple rigged mannequins (5 teens) with idle/turn/gesture cycles
   - Static camp set (rocks ring, tent, sign, lantern) with cool moon rig + warm practicals
   - Camera moves per motion_v1.csv (push-ins/pans) mapped to Blender keyframes
   - Output: 6 shot renders @1920x1080 H.264, then assemble into animatic_v3_previz.mp4

2) Layered 2.5D puppet (fallback if 3D not available)
   - Styleframe or board-derived character cutouts (alpha) separated from BG
   - Head/hand puppet transforms, phone beam glow, embers overlay
   - Output: 6 shot renders @1920x1080, assemble into animatic_v3_previz.mp4

Acceptance (must be visible in the preview renders)
- Each shot shows readable character motion (not just camera moves): head turns, phone raises/tilts, hand/gesture, weight shifts
- Environment anchors present and consistent with boards v3
- Lighting beats match: f02 flare, f08 phones-only, f10 pocket glow

Deliverables
- Video: /home/james/Hermes/state/projects/spooky-teen-shortfilm/artifacts/animatic_v3_previz.mp4 (15–20s total)
- Per-shot MP4s under /previs/renders/v1/f02.mp4 … f10.mp4
- A short note stating what is visibly on screen in one frame (evidence clause)

Notes
- Tone: PG-13; suspense not gore
- If 3D route is used, NPR/Eevee is fine (no photoreal required)
- If layered 2.5D route is used, provide the PNG cutouts under /previs/assets/cutouts/ with clear naming
