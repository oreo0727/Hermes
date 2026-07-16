# Midnight Signals — Runway Micro‑Motion Slice Status (2026‑05‑28)

Active slice: Animatic v3 with micro character motion (Runway pass)
Owner lane: creative-dev
Status: BLOCKED pending Runway Gen‑3 access or fallback approval

## What advanced since v2
- Upgraded six previously-blocked shots (003/006/012/013/014/018) from text slates to image‑grounded stills.
- Rebuilt placeholder Runway pack and animatic against upgraded sources.

## Current reviewables
- Contact sheet (sources v2): artifacts/contact_sheet_runway_sources_v2.png
- Contact sheet (runway v1): artifacts/contact_sheet_runway_v1.png
- Placeholder animatic (Runway composite): artifacts/animatic_v3_runway.mp4
- Per‑shot placeholder clips: artifacts/runway/shot_003_v1.mp4 … shot_018_v1.mp4

## Why blocked
- True Runway Gen‑3 micro‑motion generation requires authentication; not available inside current lane.
- animatic_v3_runway.mp4 uses placeholder composites for timing; not final Gen‑3 motion.

## Decision needed (pick one)
1) Grant Runway Gen‑3 access to creative‑dev for shots 003/006/012/013/014/018 and proceed.
2) Approve fallback micro‑motion pass (subtle parallax/optical‑flow/warp variants) using existing upgraded stills; deliver animatic_v3_micromotion_fallback.mp4 in 24–48h.

## If fallback is approved (plan)
- Generate per‑shot micro‑motion variants (003/006/012/013/014/018); create contact_sheet_micromotion_v1.png.
- Assemble animatic_v3_micromotion_fallback.mp4; verify dims/audio/subs with tools/verify_animatic*.py.
- Leave creative handoff with exact presets so future Runway Gen‑3 can replace fallback one‑for‑one.

## Acceptance (unchanged)
- Five teens are visibly rendered as characters (not placeholders or abstract geometry).
- Boards mirror camp reference (tent back‑center, lantern LF, sign right, central fire, moonlit forest palette).
- Lighting: warm fire key + cool moon rim; phones‑only darkness where called for.

— Prepared by Operator lane, 2026‑05‑28.
