# Sheldon / Hermes Gap Closure — 2026-05-16

## Top 5 Gaps

1. Project cards were undercounting real work because they only looked at `state/projects/<id>/runs` and the empty `app/`, `game/`, `creative/` folders.
2. Project `updated_at` in the portal reflected only `project.json`, so active exports and recent runs still looked stale.
3. Specialist dispatch history existed, but the project snapshots and portal cards did not surface it.
4. A stale `running` dispatch could survive after the operator bridge exited, which made Sheldon’s specialist picture less trustworthy.
5. Operator-facing docs still pointed reviewers at `/maze-forest/` even though the current served review build lives at `/godot-web/`.

## Closure

- Project snapshots now include linked Hermes portal runs, linked specialist dispatches, derived last activity, and alias-based track counts for real project folders like `godot-maze/`, `godot-web/`, `tools/`, and `docs/ui/`.
- Portal project cards now show dispatch counts and include the game track in the stat row.
- Portal startup now marks stale `running` specialist dispatches as failed after a timeout window instead of leaving them silently active forever.
- Aetherion run docs and Sheldon troubleshooting notes now point at `http://127.0.0.1:8000/godot-web/` as the current review URL, while keeping older prototype paths explicitly labeled as legacy.
- Historical Aetherion portal runs were backfilled into `state/projects/aetherion-maze/runs/` so the project-local run history matches the live Hermes control-plane record.
