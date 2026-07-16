#!/usr/bin/env python3
"""Run a staged Hermes delivery pipeline across lead, creative, game, and app lanes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hermes_stack.orchestration import build_delivery_model, clip_text  # noqa: E402
from hermes_stack.projects import discover_projects, update_project  # noqa: E402


SPECIALIST_LANES = ("creative-dev", "game-dev", "app-dev")


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _project_context(root_dir: Path, project_id: str) -> dict[str, object]:
    for project in discover_projects(root_dir):
        if str(project.get("project_id") or "") == project_id:
            return project
    raise SystemExit(f"Unknown project id: {project_id}")


def _stage_prompt(
    *,
    lane: str,
    stage_index: int,
    total_stages: int,
    objective: str,
    project: dict[str, object],
    delivery_model: dict[str, object],
    previous_results: list[dict[str, Any]],
) -> str:
    sequence = [str(item) for item in delivery_model.get("lane_sequence") or [] if str(item)]
    prior_lines: list[str] = []
    for result in previous_results[-2:]:
        summary = str(result.get("summary") or "").strip()
        next_actions = result.get("next_actions") if isinstance(result.get("next_actions"), list) else []
        next_line = str(next_actions[0]).strip() if next_actions else ""
        if summary:
            prior_lines.append(f"- {result['lane']}: {summary}")
        if next_line:
            prior_lines.append(f"- {result['lane']} next: {next_line}")
    if not prior_lines:
        prior_lines.append("- No prior specialist output yet. Start from the project brief and live artifact tree.")

    lane_contract = {
        "creative-dev": (
            "Freeze the creative target and acceptance language for the primary artifact. "
            "Name what to preserve, what to drop, and what the implementation lanes must not drift from."
        ),
        "game-dev": (
            "Converge the playable implementation on the chosen artifact. "
            "Do not create a parallel rebuild path unless the creative handoff explicitly requires it."
        ),
        "app-dev": (
            "Tighten the tooling, packaging, portal, and review loop around the chosen implementation path. "
            "Reduce operator ambiguity and make the artifact reviewable without ceremony."
        ),
    }
    next_lane = ""
    try:
        lane_index = sequence.index(lane)
    except ValueError:
        lane_index = -1
    if lane_index != -1 and lane_index + 1 < len(sequence):
        next_lane = sequence[lane_index + 1]

    prompt_parts = [
        f"Delivery strategy: {delivery_model.get('strategy_label')}",
        f"Stage {stage_index}/{total_stages}: {lane}",
        f"Project: {project.get('project_id')} / {project.get('title')}",
        f"Primary objective: {objective}",
        f"Current project summary: {project.get('summary') or 'n/a'}",
        f"Current tracking now: {project.get('now') or 'n/a'}",
        "",
        "Stage contract:",
        lane_contract.get(lane, "Leave the project in a better, more concrete state for the next lane."),
        "",
        "Prior handoff context:",
        *prior_lines,
        "",
        "Required output:",
        "- concise human summary",
        "- machine-readable json block with summary, implemented, verified, assumed, blocked, risks, next_actions, artifacts, handoff_needed",
    ]
    if next_lane:
        prompt_parts.extend(
            [
                "",
                f"Leave {next_lane} a clean next action.",
                f"Make the first `next_actions` item the concrete handoff for {next_lane}.",
            ]
        )
    return "\n".join(prompt_parts).strip()


def _run_stage(
    *,
    root_dir: Path,
    project_id: str,
    lane: str,
    prompt: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    command = [
        "python3",
        str(root_dir / "scripts" / "hermes-specialist-bridge.py"),
        "--root-dir",
        str(root_dir),
        "--profile",
        lane,
        "--project-id",
        project_id,
        "--prompt",
        prompt,
        "--json",
    ]
    if timeout_seconds > 0:
        command.extend(["--timeout", str(timeout_seconds)])

    completed = subprocess.run(
        command,
        cwd=root_dir,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "").strip() or f"{lane} stage failed")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{lane} returned invalid JSON output") from exc
    return payload


def _artifact_path(project_root: Path) -> Path:
    target_dir = project_root / "artifacts" / "orchestration"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"lead-creative-game-app_{_utc_stamp()}.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", default=str(REPO_ROOT), help="Hermes repo root")
    parser.add_argument("--project-id", required=True, help="Hermes project id")
    parser.add_argument("--objective", required=True, help="Lead objective to orchestrate across lanes")
    parser.add_argument("--timeout", type=int, default=0, help="Optional per-stage timeout in seconds")
    parser.add_argument("--plan-only", action="store_true", help="Print the resolved pipeline without running specialist stages")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of prose")
    args = parser.parse_args()

    root_dir = REPO_ROOT if args.root_dir == str(REPO_ROOT) else Path(args.root_dir).resolve()
    project = _project_context(root_dir, args.project_id.strip())
    delivery_model = build_delivery_model(profile_key="operator", project=project, objective=args.objective.strip())
    stage_lanes = [lane for lane in delivery_model.get("lane_sequence") or [] if lane in SPECIALIST_LANES]

    if args.plan_only:
        payload = {
            "project_id": args.project_id.strip(),
            "objective": args.objective.strip(),
            "delivery_model": delivery_model,
            "stages": stage_lanes,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(
                "\n".join(
                    [
                        f"Project: {args.project_id.strip()}",
                        f"Strategy: {delivery_model.get('strategy_label')}",
                        f"Stages: {' -> '.join(stage_lanes) if stage_lanes else 'none'}",
                        f"Objective: {args.objective.strip()}",
                    ]
                )
            )
        return 0

    update_project(
        root_dir,
        project_id=args.project_id.strip(),
        owner="operator",
        status="active",
        now=f"Lead orchestration in motion: {args.objective.strip()}",
        next_value=f"Run {stage_lanes[0]}" if stage_lanes else "No specialist stages resolved.",
        blocked=(),
    )

    stage_results: list[dict[str, Any]] = []
    for index, lane in enumerate(stage_lanes, start=1):
        prompt = _stage_prompt(
            lane=lane,
            stage_index=index,
            total_stages=len(stage_lanes),
            objective=args.objective.strip(),
            project=project,
            delivery_model=delivery_model,
            previous_results=stage_results,
        )
        try:
            payload = _run_stage(
                root_dir=root_dir,
                project_id=args.project_id.strip(),
                lane=lane,
                prompt=prompt,
                timeout_seconds=max(0, args.timeout),
            )
        except Exception as exc:
            update_project(
                root_dir,
                project_id=args.project_id.strip(),
                owner=lane,
                status="blocked",
                blocked=(clip_text(str(exc), 220),),
                next_value=f"Repair or retry {lane} stage.",
            )
            raise

        structured_result = payload.get("structured_result") if isinstance(payload.get("structured_result"), dict) else {}
        stage_result = {
            "lane": lane,
            "dispatch_id": str(payload.get("dispatch_id") or ""),
            "summary": str(structured_result.get("summary") or "").strip(),
            "implemented": structured_result.get("implemented") if isinstance(structured_result.get("implemented"), list) else [],
            "verified": structured_result.get("verified") if isinstance(structured_result.get("verified"), list) else [],
            "blocked": structured_result.get("blocked") if isinstance(structured_result.get("blocked"), list) else [],
            "risks": structured_result.get("risks") if isinstance(structured_result.get("risks"), list) else [],
            "next_actions": structured_result.get("next_actions") if isinstance(structured_result.get("next_actions"), list) else [],
            "artifacts": structured_result.get("artifacts") if isinstance(structured_result.get("artifacts"), list) else [],
        }
        stage_results.append(stage_result)

        next_lane = stage_lanes[index] if index < len(stage_lanes) else "operator"
        update_project(
            root_dir,
            project_id=args.project_id.strip(),
            owner=next_lane,
            status="blocked" if stage_result["blocked"] else "active",
            now=f"{lane}: {stage_result['summary'] or 'stage completed'}",
            next_value=(stage_result["next_actions"][0] if stage_result["next_actions"] else f"Hand off to {next_lane}"),
            blocked=tuple(stage_result["blocked"][:3]),
        )

    project_root = Path(str(project.get("root") or "")).resolve()
    artifact_path = _artifact_path(project_root)
    orchestration_artifact = {
        "schema_version": "1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_id": args.project_id.strip(),
        "objective": args.objective.strip(),
        "delivery_model": delivery_model,
        "stages": stage_results,
    }
    artifact_path.write_text(json.dumps(orchestration_artifact, indent=2) + "\n", encoding="utf-8")

    done_rows = [f"Lead/creative/game/app orchestration artifact captured at {artifact_path}."]
    for result in stage_results[-2:]:
        if result["summary"]:
            done_rows.append(f"{result['lane']}: {result['summary']}")

    update_project(
        root_dir,
        project_id=args.project_id.strip(),
        owner="operator",
        status="active",
        now=f"Lead orchestration complete for: {args.objective.strip()}",
        next_value="Operator selects the next execution slice from the orchestration artifact and keeps one primary delivery target.",
        blocked=(),
        done=tuple(done_rows),
    )

    if args.json:
        print(json.dumps({"ok": True, "artifact": str(artifact_path), "stages": stage_results}, indent=2))
        return 0

    lines = [
        f"Project: {args.project_id.strip()}",
        f"Strategy: {delivery_model.get('strategy_label')}",
        f"Artifact: {artifact_path}",
        "Stages:",
    ]
    for result in stage_results:
        lines.append(f"- {result['lane']}: {result['summary'] or 'completed'}")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
