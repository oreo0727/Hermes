# Runway Motion Pass v1 — Notes

Shots delivered: 003, 006, 012, 013, 014, 018
Builder: tools/build_animatic_with_runway.py → artifacts/animatic_v3_runway.mp4 (24 fps)
Contact sheet: artifacts/contact_sheet_runway_v1.png

Per-shot intents (from plan):
- 003: Group subtle life — blinks, small head turns, phone-hand micro-moves. No camera moves or new props.
- 006: Two-shot — Ava small breath + glance; partner tiny nod. Hands mostly still.
- 012: Argue beat — gentle gesture, head turns only; no exaggerated lip sync.
- 013: Hands flip stones minimally; fingers micro-moves.
- 014: Phones-as-light — slow screen glow pulse; micro head/eye reactions. Conservative glow.
- 018: Group resolve — micro nods, shared breath; no steps.

Guardrails applied in prompting:
- negatives: no camera drift, no new people/props, no harsh flares, no fast gestures, PG-13 tone
- guidance scale 6.5–7, seed -1 (randomized)
- aspect/size match to source frames

Next adjustments (if requested):
- If 012 and 018 feel too quiet, bump micro-motion amplitude +10–15% only.
- If any drift appears, mask faces/hands to lock BG; re-render.
