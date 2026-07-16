#!/usr/bin/env python3
"""Summarize live Hermes lane health and portal background runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hermes_stack.scaffold import build_snapshot, repo_root  # noqa: E402
from hermes_stack.state_store import list_portal_runs as store_list_portal_runs  # noqa: E402


LANE_ORDER = ("operator", "app-dev", "game-dev", "creative-dev")


def _load_runs(root_dir: Path) -> list[dict[str, object]]:
    rows = list(store_list_portal_runs(root_dir))
    rows.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return rows


def _format_lane(profile: dict[str, object]) -> str:
    runtime = profile.get("runtime") if isinstance(profile.get("runtime"), dict) else {}
    gateway_state = str((runtime or {}).get("gateway_state") or "unknown")
    platforms_raw = (runtime or {}).get("platforms")
    platforms: dict[str, dict[str, object]] = {}
    if isinstance(platforms_raw, list):
        for row in platforms_raw:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if name:
                platforms[name] = row
    discord_state = "n/a"
    if profile.get("discord_token_present"):
        discord_state = str((platforms.get("discord") or {}).get("state") or "disconnected")
    api_live = "up" if profile.get("api_server_live") else "down"
    return (
        f"- {profile.get('key')}: gateway={gateway_state}, api={api_live}, "
        f"discord={discord_state}, workspace={profile.get('workspace_root')}"
    )


def _format_run(run: dict[str, object]) -> str:
    project_id = str(run.get("project_id") or "-")
    checkpoint = str(run.get("latest_checkpoint") or "").strip() or "No checkpoint yet."
    return (
        f"- {run.get('run_id')}: {run.get('status')} / {run.get('phase')} "
        f"[profile={run.get('profile_key')}, project={project_id}] {checkpoint}"
    )


def _json_summary(root_dir: Path, *, project_id: str, run_id: str, limit: int) -> dict[str, object]:
    snapshot = build_snapshot(root_dir)
    profiles = [row for row in snapshot.get("profiles", []) if isinstance(row, dict)]
    profile_map = {str(row.get("key")): row for row in profiles}
    runs = _load_runs(root_dir)
    if project_id:
        runs = [row for row in runs if str(row.get("project_id") or "") == project_id]
    if run_id:
        runs = [row for row in runs if str(row.get("run_id") or "") == run_id]
    runs = runs[: max(1, limit)]
    return {
        "root_dir": str(root_dir),
        "project_id": project_id,
        "run_id": run_id,
        "portfolio": snapshot.get("portfolio") if isinstance(snapshot.get("portfolio"), dict) else {},
        "profiles": [profile_map[key] for key in LANE_ORDER if key in profile_map],
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", default=str(REPO_ROOT), help="Hermes repo root")
    parser.add_argument("--project-id", default="", help="Filter runs by project id")
    parser.add_argument("--run-id", default="", help="Show one specific run id")
    parser.add_argument("--limit", type=int, default=8, help="Maximum number of runs to show")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args()

    root_dir = repo_root(args.root_dir)
    payload = _json_summary(
        root_dir,
        project_id=args.project_id.strip(),
        run_id=args.run_id.strip(),
        limit=args.limit,
    )

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    lines = ["Hermes status", "", "Lanes:"]
    for profile in payload["profiles"]:
        lines.append(_format_lane(profile))
    lines.append("")
    portfolio = payload.get("portfolio") if isinstance(payload.get("portfolio"), dict) else {}
    queue_rows = portfolio.get("project_queue") if isinstance(portfolio.get("project_queue"), list) else []
    active_project_id = str(portfolio.get("active_project_id") or "").strip()
    lines.append("Portfolio:")
    if not queue_rows:
        lines.append("- No active portfolio queue yet.")
    else:
        for row in queue_rows:
            if not isinstance(row, dict):
                continue
            project_label = str(row.get("project_id") or "-")
            state = str(row.get("state") or "queued")
            focus_marker = " (focused)" if project_label == active_project_id else ""
            lines.append(f"- {project_label}: {state}{focus_marker}")
    lines.append("")
    lines.append("Background runs:")
    runs = payload["runs"]
    if not runs:
        lines.append("- No matching runs found.")
    else:
        for run in runs:
            lines.append(_format_run(run))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
