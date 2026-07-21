"""Local operator portal for the standalone Hermes stack."""

from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import json
import mimetypes
import os
import re
import socket
import sqlite3
import subprocess
import time
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from hermes_stack.brain_graph import brain_graph
from hermes_stack.fast_router import fast_route_chat
from hermes_stack.mission_control import (
    build_briefing,
    create_handoff,
    list_handoffs,
    mission_cards,
    run_truth_loop,
    self_improvement_proposal,
    self_improvement_snapshot,
    truth_loop_snapshot,
    update_self_improvement_status,
    update_handoff_status,
    watch_digest,
)
from hermes_stack.orchestration import (
    clip_text,
    closure_gate_review,
    contains_any,
    execution_quality_issues,
    extract_structured_result,
    infer_project_id,
    latest_user_message,
    minutes_since,
    monitor_recommendation,
    parse_assistant_output,
    parse_timestamp,
    project_context_message,
    result_contract_review,
    runtime_contract_message,
    summarize_result_for_tracking,
    utc_now,
    work_order_message,
    build_work_order,
)
from hermes_stack.projects import activate_project, archive_project, discover_projects, update_project
from hermes_stack.scaffold import (
    PROFILE_SPECS,
    build_snapshot,
    hermes_state_dir,
    profiles_dir,
    repo_root,
)
from hermes_stack.state_store import (
    list_dispatches as store_list_dispatches,
    list_portal_runs as store_list_portal_runs,
    load_dispatch as store_load_dispatch,
    load_portal_run as store_load_portal_run,
    upsert_dispatch as store_upsert_dispatch,
    upsert_portal_run as store_upsert_portal_run,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_ATTACHMENTS_PER_MESSAGE = 4
MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024
RUN_LIST_LIMIT = 24
DISPATCH_LIST_LIMIT = 24
MONITOR_ALERT_LIMIT = 24
RUN_MAX_CHECKPOINTS = 12
RUN_HEARTBEAT_SECONDS = 45
RUN_REQUEST_TIMEOUT_SECONDS = 3900
STALE_DISPATCH_MINUTES = 30
VISION_PROFILE_KEY = "operator"
VISION_ANALYSIS_PROMPT = (
    "Describe everything visible in this image in thorough detail. "
    "Include any text, code, UI, objects, people, layout, colors, and any "
    "other notable visual information."
)
VISION_RUNNER = """
import asyncio
import sys
from tools.vision_tools import vision_analyze_tool

async def _main() -> None:
    result = await vision_analyze_tool(image_url=sys.argv[1], user_prompt=sys.argv[2])
    sys.stdout.write(result)

asyncio.run(_main())
"""


def _utc_now() -> str:
    return utc_now()


def _profile_record(root_dir: Path, profile_key: str) -> dict[str, object]:
    snapshot = build_snapshot(root_dir)
    return next((row for row in snapshot["profiles"] if row["key"] == profile_key), {})


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _profile_api_credentials(root_dir: Path, profile_key: str) -> tuple[int, str]:
    values = _read_env_file(profiles_dir(root_dir) / profile_key / ".env")
    return int(values.get("API_SERVER_PORT", "0") or 0), values.get("API_SERVER_KEY", "")


def _project_snapshot(root_dir: Path, project_id: str) -> dict[str, object] | None:
    normalized_id = str(project_id or "").strip()
    if not normalized_id:
        return None
    return next(
        (row for row in discover_projects(root_dir) if str(row.get("project_id") or "") == normalized_id),
        None,
    )


def _project_action_payload(root_dir: Path, project_id: str) -> dict[str, object]:
    project = _project_snapshot(root_dir, project_id)
    return {
        "ok": bool(project),
        "project": project or {},
        "portfolio": build_snapshot(root_dir).get("portfolio") if project else {},
    }


def _portal_upload_dir(root_dir: Path) -> Path:
    upload_dir = hermes_state_dir(root_dir) / "portal_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _portal_runs_dir(root_dir: Path) -> Path:
    runs_dir = hermes_state_dir(root_dir) / "portal_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    return runs_dir


def _specialist_dispatch_dir(root_dir: Path) -> Path:
    dispatch_dir = hermes_state_dir(root_dir) / "specialist_dispatches"
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    return dispatch_dir


def _run_path(root_dir: Path, run_id: str) -> Path:
    return _portal_runs_dir(root_dir) / f"{run_id}.json"


def _project_run_path(root_dir: Path, project_id: str, run_id: str) -> Path | None:
    for project in discover_projects(root_dir):
        if str(project.get("project_id") or "") != project_id:
            continue
        project_root = Path(str(project.get("root") or "")).resolve()
        runs_dir = project_root / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        return runs_dir / f"{run_id}.json"
    return None


def _write_json(path: Path, payload: object) -> None:
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _clip_text(value: object, limit: int = 320) -> str:
    return clip_text(value, limit)


def _extract_named_section(text: str, names: tuple[str, ...]) -> tuple[str, bool]:
    if not text.strip():
        return "", False

    all_headers = (
        "Objective",
        "Tracks",
        "Moves happening now",
        "Approvals needed",
        "Next checkpoint",
        "Operator update",
        "What changed",
        "Current risk",
        "Risks",
        "Next",
        "Blocked",
        "Done",
    )
    for name in names:
        pattern = re.compile(
            rf"(?ims)^\s*(?:[#>*-]+\s*)?{re.escape(name)}\s*:?\s*(.*?)"
            rf"(?=^\s*(?:[#>*-]+\s*)?(?:{'|'.join(re.escape(item) for item in all_headers)})\b|\Z)"
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip(), True
    return "", False


def _section_items(section_text: str) -> list[str]:
    items: list[str] = []
    for raw_line in section_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")):
            items.append(stripped[2:].strip())
            continue
        if re.match(r"^\d+\.\s+", stripped):
            items.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
    if items:
        return [item for item in items if item]

    compact = " ".join(line.strip() for line in section_text.splitlines() if line.strip())
    return [compact] if compact else []


def _section_explicitly_empty(section_text: str) -> bool:
    normalized = " ".join(section_text.lower().split())
    return normalized in {
        "",
        "none",
        "n/a",
        "na",
        "nothing",
        "no blockers.",
        "no blockers",
        "no approvals needed.",
        "no approvals needed",
        "none right now.",
        "none right now",
    }


def _first_meaningful_line(text: str) -> str:
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", "-", "*")):
            stripped = stripped.lstrip("#*- ").strip()
        if stripped:
            return stripped
    return ""


def _summarize_run_for_tracking(run_record: dict[str, object], output: str) -> str:
    structured_result = run_record.get("structured_result")
    if isinstance(structured_result, dict) and structured_result:
        return summarize_result_for_tracking(run_record, structured_result, output)
    objective = str(run_record.get("objective_preview") or "").strip()
    output_line = _first_meaningful_line(output)
    if output_line and output_line.lower() != objective.lower():
        return _clip_text(f"{objective} -> {output_line}", 220) if objective else _clip_text(output_line, 220)
    return _clip_text(objective or output_line or str(run_record.get("latest_checkpoint") or ""), 220)


def _sync_project_after_run(root_dir: Path, run_record: dict[str, object]) -> None:
    project_id = str(run_record.get("project_id") or "").strip()
    run_id = str(run_record.get("run_id") or "").strip()
    if not project_id or not run_id:
        return

    project_run_path = _project_run_path(root_dir, project_id, run_id)
    if project_run_path is None:
        return

    project_run_payload = {
        "run_id": run_id,
        "project_id": project_id,
        "profile_key": run_record.get("profile_key"),
        "status": run_record.get("status"),
        "phase": run_record.get("phase"),
        "created_at": run_record.get("created_at"),
        "started_at": run_record.get("started_at"),
        "completed_at": run_record.get("completed_at"),
        "objective_preview": run_record.get("objective_preview"),
        "latest_checkpoint": run_record.get("latest_checkpoint"),
        "output_preview": _clip_text(run_record.get("output"), 800),
        "error_preview": _clip_text(run_record.get("error"), 800),
    }

    projects = discover_projects(root_dir)
    project = next((row for row in projects if str(row.get("project_id") or "") == project_id), None)
    if project is None:
        _write_json(project_run_path, project_run_payload)
        return

    output = str(run_record.get("output") or "")
    structured_result = run_record.get("structured_result") if isinstance(run_record.get("structured_result"), dict) else {}
    work_order = run_record.get("work_order") if isinstance(run_record.get("work_order"), dict) else {}
    profile_key = str(run_record.get("profile_key") or "")
    action_type = str(work_order.get("action_type") or "direct_execute").strip() or "direct_execute"
    contract_review = result_contract_review(
        profile_key=profile_key,
        work_order=work_order,
        structured_result=structured_result,
    )
    closure_review = closure_gate_review(project=project, structured_result=structured_result, action_type=action_type)
    project_run_payload["action_type"] = action_type
    project_run_payload["contract_review"] = contract_review
    project_run_payload["closure_review"] = closure_review
    _write_json(project_run_path, project_run_payload)
    existing_done = list(project.get("done") or [])
    existing_blocked = list(project.get("blocked") or [])

    status = str(run_record.get("status") or "")
    if status == "completed":
        blocked_items: list[str] | None = None
        now_value = ""
        next_value: str | None = None
        if structured_result:
            now_value = str(structured_result.get("summary") or "").strip() or str(run_record.get("objective_preview") or "").strip()
            next_actions = structured_result.get("next_actions") if isinstance(structured_result.get("next_actions"), list) else []
            next_value = str(next_actions[0]).strip() if next_actions else None
            blocked_values = structured_result.get("blocked") if isinstance(structured_result.get("blocked"), list) else []
            blocked_items = [str(item).strip() for item in blocked_values if str(item).strip()]
        else:
            objective_section, objective_found = _extract_named_section(output, ("Objective",))
            next_section, next_found = _extract_named_section(output, ("Next checkpoint", "Next"))
            approvals_section, approvals_found = _extract_named_section(output, ("Approvals needed", "Blocked"))
            now_value = _first_meaningful_line(objective_section) if objective_found else str(run_record.get("objective_preview") or "").strip()
            next_value = _first_meaningful_line(next_section) if next_found else None
            if approvals_found:
                blocked_items = [] if _section_explicitly_empty(approvals_section) else _section_items(approvals_section)

        done_summary = _summarize_run_for_tracking(run_record, output)
        merged_done = [done_summary, *existing_done] if done_summary else existing_done
        deduped_done: list[str] = []
        seen_done: set[str] = set()
        for item in merged_done:
            normalized = item.strip().lower()
            if not normalized or normalized in seen_done:
                continue
            deduped_done.append(item.strip())
            seen_done.add(normalized)

        artifact_values = structured_result.get("artifacts") if isinstance(structured_result.get("artifacts"), list) else []
        primary_artifact = ", ".join(str(item).strip() for item in artifact_values[:3] if str(item).strip()) or None
        structured_project_update = (
            structured_result.get("project_update")
            if isinstance(structured_result.get("project_update"), dict)
            else {}
        )
        next_owner = str(structured_result.get("owner_lane") or structured_project_update.get("primary_lane") or "").strip() or None
        next_status = str(structured_project_update.get("status") or "").strip() or None
        next_now = str(structured_project_update.get("now") or "").strip() or None
        next_next = str(structured_project_update.get("next") or "").strip() or next_value
        declared_primary_artifact = str(structured_project_update.get("primary_artifact") or "").strip() or None
        declared_primary_lane = str(structured_project_update.get("primary_lane") or "").strip() or None
        declared_blocked = (
            [str(item).strip() for item in structured_project_update.get("blocked") or [] if str(item).strip()]
            if isinstance(structured_project_update.get("blocked"), list)
            else []
        )
        declared_done = (
            [str(item).strip() for item in structured_project_update.get("done") or [] if str(item).strip()]
            if isinstance(structured_project_update.get("done"), list)
            else []
        )
        contract_blockers = [str(item).strip() for item in contract_review.get("reasons") or [] if str(item).strip()]
        if declared_done:
            merged_done = [*declared_done, *deduped_done]
            deduped_done = []
            seen_done = set()
            for item in merged_done:
                normalized = item.strip().lower()
                if not normalized or normalized in seen_done:
                    continue
                deduped_done.append(item.strip())
                seen_done.add(normalized)

        if action_type == "close_slice" and (not closure_review.get("ready") or not contract_review.get("ready")):
            closure_blocked = [
                *contract_blockers,
                *[str(item).strip() for item in closure_review.get("reasons") or [] if str(item).strip()],
                *([str(item).strip() for item in blocked_items] if blocked_items else []),
                *declared_blocked,
            ]
            deduped_closure_blocked: list[str] = []
            seen_closure: set[str] = set()
            for item in closure_blocked:
                normalized = item.strip().lower()
                if not normalized or normalized in seen_closure:
                    continue
                deduped_closure_blocked.append(item.strip())
                seen_closure.add(normalized)

            update_project(
                root_dir,
                project_id=project_id,
                status="blocked",
                owner=next_owner,
                now=next_now or now_value or None,
                next_value=next_next,
                blocked=tuple(deduped_closure_blocked[:6]),
                done=tuple(deduped_done[:5]),
            )
            return

        if contract_blockers:
            blocked_items = [*contract_blockers, *(blocked_items or [])]
        if declared_blocked:
            blocked_items = [*declared_blocked, *(blocked_items or [])]

        resolved_status = (
            "completed"
            if action_type == "close_slice" and closure_review.get("ready") and contract_review.get("ready")
            else next_status or ("blocked" if blocked_items else "active")
        )

        update_project(
            root_dir,
            project_id=project_id,
            status=resolved_status,
            owner=next_owner,
            now=next_now or now_value or None,
            next_value=None if resolved_status == "completed" else next_next,
            blocked=tuple(blocked_items) if blocked_items is not None else None,
            done=tuple(deduped_done[:5]),
            primary_artifact=declared_primary_artifact or primary_artifact,
            primary_lane=declared_primary_lane,
        )
        return

    failure_summary = _clip_text(
        f"{str(run_record.get('objective_preview') or '').strip()} — {str(run_record.get('error') or run_record.get('latest_checkpoint') or 'Run failed.').strip()}",
        220,
    )
    merged_blocked = [failure_summary, *existing_blocked] if failure_summary else existing_blocked
    deduped_blocked: list[str] = []
    seen_blocked: set[str] = set()
    for item in merged_blocked:
        normalized = item.strip().lower()
        if not normalized or normalized in seen_blocked:
            continue
        deduped_blocked.append(item.strip())
        seen_blocked.add(normalized)

    update_project(
        root_dir,
        project_id=project_id,
        status="blocked",
        blocked=tuple(deduped_blocked[:5]),
    )


def _load_run(root_dir: Path, run_id: str) -> dict[str, object] | None:
    return store_load_portal_run(root_dir, run_id)


def _profile_state_db_path(root_dir: Path, profile_key: str) -> Path:
    return profiles_dir(root_dir) / profile_key / "state.db"


def _load_session_messages(
    root_dir: Path,
    *,
    profile_key: str,
    session_id: str,
) -> tuple[str, list[dict[str, object]], dict[str, object] | None] | None:
    session_id = session_id.strip()
    if not session_id:
        return None

    db_path = _profile_state_db_path(root_dir, profile_key)
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        session_row = conn.execute(
            "SELECT id, source, user_id, started_at, title FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if session_row is None:
            session_row = conn.execute(
                "SELECT id, source, user_id, started_at, title FROM sessions WHERE id LIKE ? "
                "ORDER BY started_at DESC LIMIT 1",
                (f"{session_id}%",),
            ).fetchone()
        if session_row is None:
            return None

        resolved_session_id = str(session_row["id"])
        messages: list[dict[str, object]] = []
        for row in conn.execute(
            "SELECT role, content, timestamp, tool_name FROM messages WHERE session_id = ? "
            "ORDER BY timestamp, id",
            (resolved_session_id,),
        ).fetchall():
            role = str(row["role"] or "").strip()
            content = str(row["content"] or "")
            if role not in {"system", "user", "assistant"}:
                continue
            if not content.strip():
                continue
            messages.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": row["timestamp"],
                    "tool_name": row["tool_name"],
                }
            )

        return resolved_session_id, messages, dict(session_row)
    finally:
        conn.close()


def _load_session_origin(root_dir: Path, profile_key: str, session_id: str) -> dict[str, object]:
    sessions_index = profiles_dir(root_dir) / profile_key / "sessions" / "sessions.json"
    if not sessions_index.exists():
        return {}
    try:
        payload = json.loads(sessions_index.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    for entry in payload.values():
        if not isinstance(entry, dict):
            continue
        if str(entry.get("session_id") or "") != session_id:
            continue
        origin = entry.get("origin")
        return origin if isinstance(origin, dict) else {}
    return {}


def _chunk_text(text: str, *, limit: int = 1900) -> list[str]:
    cleaned = str(text or "").strip()
    if not cleaned:
        return []

    chunks: list[str] = []
    remaining = cleaned
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit)
        if split_at < limit // 2:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at < limit // 2:
            split_at = limit
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


def _post_discord_message(bot_token: str, channel_id: str, content: str) -> None:
    request = Request(
        url=f"https://discord.com/api/v10/channels/{channel_id}/messages",
        data=json.dumps({"content": content}).encode("utf-8"),
        headers={
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=15):
        return


def _mirror_portal_chat_to_discord(
    root_dir: Path,
    *,
    profile_key: str,
    session_id: str,
    user_text: str,
    assistant_text: str,
) -> None:
    if profile_key != "operator" or not session_id:
        return

    origin = _load_session_origin(root_dir, profile_key, session_id)
    if str(origin.get("platform") or "").lower() != "discord":
        return

    target_channel_id = str(origin.get("thread_id") or origin.get("chat_id") or "").strip()
    if not target_channel_id:
        return

    env = _read_env_file(profiles_dir(root_dir) / profile_key / ".env")
    bot_token = env.get("DISCORD_BOT_TOKEN", "").strip()
    if not bot_token:
        return

    mirror_pairs = [
        ("[Portal] You", user_text),
        ("[Portal] Sheldon", assistant_text),
    ]
    for label, raw_text in mirror_pairs:
        chunks = _chunk_text(raw_text)
        for index, chunk in enumerate(chunks):
            prefix = f"{label}: " if index == 0 else f"{label} (cont.): "
            _post_discord_message(bot_token, target_channel_id, f"{prefix}{chunk}")


def _store_run(root_dir: Path, run_record: dict[str, object]) -> dict[str, object]:
    return store_upsert_portal_run(root_dir, run_record)


def _run_summary(run_record: dict[str, object]) -> dict[str, object]:
    summary = {
        key: value
        for key, value in run_record.items()
        if key not in {"prepared_updates", "request_body", "response_raw", "raw_output"}
    }
    summary["output_preview"] = _clip_text(summary.get("output"))
    summary["error_preview"] = _clip_text(summary.get("error"))
    return summary


def _list_runs(root_dir: Path, *, limit: int = RUN_LIST_LIMIT) -> list[dict[str, object]]:
    runs = [_run_summary(run_record) for run_record in store_list_portal_runs(root_dir)]
    runs.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return runs[:limit]


def _existing_active_run(root_dir: Path, *, profile_key: str, project_id: str) -> dict[str, object] | None:
    active_statuses = {"queued", "running"}
    for row in _list_runs(root_dir, limit=200):
        if str(row.get("profile_key") or "") != profile_key:
            continue
        if str(row.get("project_id") or "") != project_id:
            continue
        if str(row.get("status") or "") not in active_statuses:
            continue
        return row
    return None


def _load_run_records(root_dir: Path) -> list[dict[str, object]]:
    rows = list(store_list_portal_runs(root_dir))
    rows.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return rows


def _dispatch_summary(dispatch_record: dict[str, object]) -> dict[str, object]:
    summary = dict(dispatch_record)
    summary["prompt_preview"] = _clip_text(summary.get("prompt_preview"))
    summary["output_preview"] = _clip_text(summary.get("output_preview"))
    summary["error_preview"] = _clip_text(summary.get("error_preview"))
    return summary


def _sync_project_after_dispatch_failure(root_dir: Path, dispatch_record: dict[str, object]) -> None:
    project_id = str(dispatch_record.get("project_id") or "").strip()
    if not project_id:
        return

    projects = discover_projects(root_dir)
    project = next((row for row in projects if str(row.get("project_id") or "") == project_id), None)
    if project is None:
        return

    control = project.get("control") if isinstance(project.get("control"), dict) else {}
    if not bool(control.get("strict_dispatch", False)):
        return

    structured_result = (
        dispatch_record.get("structured_result")
        if isinstance(dispatch_record.get("structured_result"), dict)
        else {}
    )
    summary = str(
        structured_result.get("summary")
        or dispatch_record.get("output_preview")
        or dispatch_record.get("prompt_preview")
        or ""
    ).strip()
    next_actions = structured_result.get("next_actions") if isinstance(structured_result.get("next_actions"), list) else []
    blocked_rows = structured_result.get("blocked") if isinstance(structured_result.get("blocked"), list) else []
    supervisor = dispatch_record.get("supervisor") if isinstance(dispatch_record.get("supervisor"), dict) else {}
    critique = supervisor.get("critique") if isinstance(supervisor.get("critique"), list) else []
    error_preview = str(dispatch_record.get("error_preview") or "").strip()
    artifacts = structured_result.get("artifacts") if isinstance(structured_result.get("artifacts"), list) else []
    primary_artifact = ", ".join(str(item).strip() for item in artifacts[:3] if str(item).strip()) or None

    merged_blocked = [
        *[str(item).strip() for item in blocked_rows if str(item).strip()],
        *[str(item).strip() for item in critique if str(item).strip()],
    ]
    if error_preview:
        merged_blocked.append(error_preview)

    deduped_blocked: list[str] = []
    seen: set[str] = set()
    for item in merged_blocked:
        normalized = item.lower()
        if not normalized or normalized in seen:
            continue
        deduped_blocked.append(item)
        seen.add(normalized)

    update_project(
        root_dir,
        project_id=project_id,
        status="blocked",
        owner=str(dispatch_record.get("profile") or "").strip() or None,
        now=summary or None,
        next_value=str(next_actions[0]).strip() if next_actions else None,
        blocked=tuple(deduped_blocked[:6]),
        primary_artifact=primary_artifact,
    )


def _list_dispatches(root_dir: Path, *, limit: int = DISPATCH_LIST_LIMIT) -> list[dict[str, object]]:
    rows = [_dispatch_summary(dispatch_record) for dispatch_record in store_list_dispatches(root_dir)]
    rows.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return rows[:limit]


def _mark_stale_dispatches_failed(root_dir: Path, *, stale_minutes: int = STALE_DISPATCH_MINUTES) -> None:
    now = datetime.now(timezone.utc)
    for dispatch_record in store_list_dispatches(root_dir):
        if str(dispatch_record.get("status") or "") != "running":
            continue
        updated_at = _parse_timestamp(dispatch_record.get("updated_at") or dispatch_record.get("created_at"))
        if updated_at is None:
            continue
        age_minutes = (now - updated_at).total_seconds() / 60.0
        if age_minutes < stale_minutes:
            continue
        dispatch_record["status"] = "failed"
        dispatch_record["updated_at"] = _utc_now()
        dispatch_record["completed_at"] = dispatch_record["updated_at"]
        dispatch_record["error_preview"] = (
            f"Dispatch marked failed after {int(age_minutes)}m without completion. "
            "The operator bridge likely exited before finalizing the record."
        )
        store_upsert_dispatch(root_dir, dispatch_record)
        _sync_project_after_dispatch_failure(root_dir, dispatch_record)


def _parse_timestamp(value: object) -> datetime | None:
    return parse_timestamp(value)


def _minutes_since(value: object, *, now: datetime | None = None) -> float | None:
    return minutes_since(value, now=now)


def _contains_any(text: object, needles: tuple[str, ...]) -> bool:
    return contains_any(text, needles)


def _recent_assistant_message(
    root_dir: Path,
    *,
    profile_key: str,
    session_id: str,
) -> dict[str, object] | None:
    payload = _load_session_messages(root_dir, profile_key=profile_key, session_id=session_id)
    if not payload:
        return None
    _, messages, _session = payload
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return message
    return None


def _build_monitor_alerts(root_dir: Path, *, limit: int = MONITOR_ALERT_LIMIT) -> list[dict[str, object]]:
    now = datetime.now(timezone.utc)
    alerts: list[dict[str, object]] = []
    snapshot = build_snapshot(root_dir)
    profile_rows = snapshot.get("profiles", []) if isinstance(snapshot.get("profiles"), list) else []
    operator_profile = next((row for row in profile_rows if row.get("key") == "operator"), {})
    operator_sessions = operator_profile.get("recent_sessions") if isinstance(operator_profile.get("recent_sessions"), list) else []

    for run in _load_run_records(root_dir):
        status = str(run.get("status") or "")
        run_id = str(run.get("run_id") or "")
        profile_key = str(run.get("profile_key") or "")
        phase = str(run.get("phase") or "")
        project_id = str(run.get("project_id") or "")
        checkpoint_age = _minutes_since(
            run.get("last_checkpoint_at") or run.get("updated_at") or run.get("created_at"),
            now=now,
        )

        if status in {"queued", "running"} and checkpoint_age is not None and checkpoint_age >= 12:
            alerts.append(
                {
                    "tone": "down",
                    "kind": "stalled-run",
                    "title": f"{profile_key or 'lane'} run looks stalled",
                    "summary": f"{run_id or 'run'} has been {status} in phase {phase or 'unknown'} for about {int(checkpoint_age)}m.",
                    "detail": str(run.get("latest_checkpoint") or "No checkpoint text was recorded."),
                    "subject": run_id,
                    "profile_key": profile_key,
                    "project_id": project_id,
                    "updated_at": str(run.get("last_checkpoint_at") or run.get("updated_at") or ""),
                    "watch_only": True,
                    "recommendation": monitor_recommendation(
                        "stalled-run",
                        profile_key=profile_key,
                        project_id=project_id,
                        subject=run_id,
                    ),
                }
            )

        structured_result = run.get("structured_result") if isinstance(run.get("structured_result"), dict) else {}
        contract_review = run.get("contract_review") if isinstance(run.get("contract_review"), dict) else {}
        if status == "completed" and (
            bool(structured_result.get("handoff_needed"))
            or not bool(contract_review.get("ready", True))
            or _contains_any(
                run.get("output"),
                (
                    "if you say",
                    "want me to",
                    "your call",
                    "ok to",
                    "approve",
                    "hard refresh",
                    "please do a hard refresh",
                    "send a quick screenshot",
                    "on your ok",
                ),
            )
        ):
            alerts.append(
                {
                    "tone": "accent",
                    "kind": "handoff-gap",
                    "title": f"{profile_key or 'lane'} may have stopped at handoff",
                    "summary": f"{run_id or 'run'} finished, but the reply still appears to hand work back to the user instead of closing the loop.",
                    "detail": _clip_text(run.get("output") or run.get("output_preview") or "", 500),
                    "subject": run_id,
                    "profile_key": profile_key,
                    "project_id": project_id,
                    "updated_at": str(run.get("completed_at") or run.get("updated_at") or ""),
                    "watch_only": True,
                    "recommendation": monitor_recommendation(
                        "handoff-gap",
                        profile_key=profile_key,
                        project_id=project_id,
                        subject=run_id,
                    ),
                }
            )
        if status == "completed" and contract_review and not bool(contract_review.get("ready", True)):
            alerts.append(
                {
                    "tone": "accent",
                    "kind": "contract-gap",
                    "title": f"{profile_key or 'lane'} finished without a valid run contract",
                    "summary": f"{run_id or 'run'} completed, but its structured result is missing required state-machine fields or mismatches the work order.",
                    "detail": _clip_text(" ".join(str(item) for item in contract_review.get("reasons") or []), 500),
                    "subject": run_id,
                    "profile_key": profile_key,
                    "project_id": project_id,
                    "updated_at": str(run.get("completed_at") or run.get("updated_at") or ""),
                    "watch_only": True,
                    "recommendation": monitor_recommendation(
                        "handoff-gap",
                        profile_key=profile_key,
                        project_id=project_id,
                        subject=run_id,
                    ),
                }
            )

    for dispatch in _list_dispatches(root_dir, limit=DISPATCH_LIST_LIMIT):
        status = str(dispatch.get("status") or "")
        dispatch_id = str(dispatch.get("dispatch_id") or "")
        profile_key = str(dispatch.get("profile") or "")
        project_id = str(dispatch.get("project_id") or "")
        updated_minutes = _minutes_since(
            dispatch.get("updated_at") or dispatch.get("created_at"),
            now=now,
        )

        if status == "running" and updated_minutes is not None and updated_minutes >= 15:
            alerts.append(
                {
                    "tone": "accent",
                    "kind": "stalled-dispatch",
                    "title": f"{profile_key or 'specialist'} dispatch is quiet",
                    "summary": f"{dispatch_id or 'dispatch'} has been running for about {int(updated_minutes)}m without a recorded completion.",
                    "detail": str(dispatch.get("prompt_preview") or "No prompt preview available."),
                    "subject": dispatch_id,
                    "profile_key": profile_key,
                    "project_id": project_id,
                    "updated_at": str(dispatch.get("updated_at") or dispatch.get("created_at") or ""),
                    "watch_only": True,
                    "recommendation": monitor_recommendation(
                        "stalled-dispatch",
                        profile_key=profile_key,
                        project_id=project_id,
                        subject=dispatch_id,
                    ),
                }
            )

        if not project_id:
            alerts.append(
                {
                    "tone": "down",
                    "kind": "unbound-dispatch",
                    "title": f"{profile_key or 'specialist'} dispatch is missing project binding",
                    "summary": f"{dispatch_id or 'dispatch'} is not tied to a project, which makes logic drift and artifact loss more likely.",
                    "detail": str(dispatch.get("prompt_preview") or "No prompt preview available."),
                    "subject": dispatch_id,
                    "profile_key": profile_key,
                    "project_id": "",
                    "updated_at": str(dispatch.get("updated_at") or dispatch.get("created_at") or ""),
                    "watch_only": True,
                    "recommendation": monitor_recommendation(
                        "unbound-dispatch",
                        profile_key=profile_key,
                        project_id="",
                        subject=dispatch_id,
                    ),
                }
            )

    for session in operator_sessions[:2]:
        session_id = str(session.get("session_id") or "").strip()
        if not session_id:
            continue
        assistant_message = _recent_assistant_message(root_dir, profile_key="operator", session_id=session_id)
        if not assistant_message:
            continue
        content = str(assistant_message.get("content") or "")
        if _contains_any(
            content,
            (
                "if you say",
                "your call",
                "want me to",
                "ok to",
                "approve",
                "please do a hard refresh",
                "send a quick snap",
                "confirm",
            ),
        ):
            alerts.append(
                {
                    "tone": "accent",
                    "kind": "session-handoff",
                    "title": "Sheldon may be pausing on user handoff",
                    "summary": f"Recent operator session with {session.get('user_name') or session.get('display_name') or 'the user'} ends in approval or handoff language.",
                    "detail": _clip_text(content, 420),
                    "subject": session_id,
                    "profile_key": "operator",
                    "project_id": "",
                    "updated_at": str(session.get("updated_at") or ""),
                    "watch_only": True,
                    "recommendation": monitor_recommendation(
                        "session-handoff",
                        profile_key="operator",
                        project_id="",
                        subject=session_id,
                    ),
                }
            )

    alerts.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return alerts[:limit]


def _latest_user_message(messages: list[dict[str, str]]) -> str:
    return latest_user_message(messages)


def _project_keyword_score(project: dict[str, object], text: str) -> int:
    from hermes_stack.orchestration import project_keyword_score

    return project_keyword_score(project, text)


def _infer_project_id(
    root_dir: Path,
    *,
    profile_key: str,
    explicit_project_id: str,
    messages: list[dict[str, str]],
) -> str:
    return infer_project_id(
        discover_projects(root_dir),
        profile_key=profile_key,
        explicit_project_id=explicit_project_id,
        messages=messages,
    )


def _project_context_message(root_dir: Path, project_id: str) -> dict[str, str] | None:
    if not project_id:
        return None
    for project in discover_projects(root_dir):
        if str(project.get("project_id") or "") != project_id:
            continue
        return project_context_message(project)
    return None


def _runtime_contract_message(profile_key: str) -> dict[str, str]:
    return runtime_contract_message(profile_key)


def _execution_quality_issues(output: str) -> list[str]:
    return execution_quality_issues(output)


def _append_checkpoint(
    run_record: dict[str, object],
    *,
    status: str | None = None,
    phase: str | None = None,
    message: str,
    bump_updated_at: bool = True,
) -> None:
    timestamp = _utc_now()
    if status is not None:
        run_record["status"] = status
    if phase is not None:
        run_record["phase"] = phase
    if bump_updated_at:
        run_record["updated_at"] = timestamp
    run_record["last_checkpoint_at"] = timestamp
    run_record["latest_checkpoint"] = message
    checkpoints = list(run_record.get("checkpoints") or [])
    checkpoints.append(
        {
            "at": timestamp,
            "status": run_record.get("status"),
            "phase": run_record.get("phase"),
            "message": message,
        }
    )
    run_record["checkpoints"] = checkpoints[-RUN_MAX_CHECKPOINTS:]


def _request_timeout_for_profile(profile: dict[str, object]) -> int:
    try:
        gateway_timeout = int(profile.get("gateway_timeout") or 0)
    except (TypeError, ValueError):
        gateway_timeout = 0
    return max(RUN_REQUEST_TIMEOUT_SECONDS, gateway_timeout + 300 if gateway_timeout else 0)


def _mark_inflight_runs_interrupted(root_dir: Path, run_lock: threading.RLock) -> None:
    with run_lock:
        for run_record in store_list_portal_runs(root_dir):
            if str(run_record.get("status")) not in {"queued", "running"}:
                continue
            _append_checkpoint(
                run_record,
                status="interrupted",
                phase="portal_restart",
                message="Portal restarted before this run completed.",
            )
            run_record["completed_at"] = _utc_now()
            run_record["error"] = "Portal restarted before this run completed."
            _store_run(root_dir, run_record)


def _heartbeat_run(server: "PortalServer", run_id: str, stop_event: threading.Event) -> None:
    while not stop_event.wait(RUN_HEARTBEAT_SECONDS):
        with server.run_lock:
            run_record = _load_run(server.repo_root, run_id)
            if not run_record or str(run_record.get("status")) != "running":
                return
            _append_checkpoint(
                run_record,
                message="Still running in the background.",
            )
            _store_run(server.repo_root, run_record)


def _finish_run(
    server: "PortalServer",
    run_id: str,
    *,
    status: str,
    phase: str,
    message: str,
    output: str = "",
    error: str = "",
    session_id: str = "",
    response_raw: dict[str, object] | None = None,
) -> None:
    final_record: dict[str, object] | None = None
    display_output = output
    structured_result: dict[str, object] = {}
    contract_review: dict[str, object] = {}
    if output:
        display_output, structured_result = parse_assistant_output(output)
    with server.run_lock:
        run_record = _load_run(server.repo_root, run_id)
        if not run_record:
            return
        contract_review = result_contract_review(
            profile_key=str(run_record.get("profile_key") or ""),
            work_order=run_record.get("work_order") if isinstance(run_record.get("work_order"), dict) else {},
            structured_result=structured_result,
        )
        _append_checkpoint(run_record, status=status, phase=phase, message=message)
        run_record["completed_at"] = _utc_now()
        run_record["output"] = display_output
        run_record["raw_output"] = output
        run_record["structured_result"] = structured_result
        run_record["contract_review"] = contract_review
        run_record["error"] = error
        if session_id:
            run_record["session_id"] = session_id
        if response_raw is not None:
            run_record["response_raw"] = response_raw
        final_record = _store_run(server.repo_root, run_record)
    if final_record is not None:
        try:
            _sync_project_after_run(server.repo_root, final_record)
        except Exception:
            pass


def _run_worker(server: "PortalServer", run_id: str) -> None:
    stop_event = threading.Event()
    heartbeat_thread = threading.Thread(
        target=_heartbeat_run,
        args=(server, run_id, stop_event),
        daemon=True,
        name=f"portal-run-heartbeat-{run_id}",
    )
    heartbeat_thread.start()

    try:
        with server.run_lock:
            run_record = _load_run(server.repo_root, run_id)
            if not run_record:
                return
            run_record["started_at"] = run_record.get("started_at") or _utc_now()
            _append_checkpoint(
                run_record,
                status="running",
                phase="dispatching",
                message="Dispatching this run to the selected Hermes specialist.",
            )
            _store_run(server.repo_root, run_record)

        profile_key = str(run_record.get("profile_key") or "")
        port, api_key = _profile_api_credentials(server.repo_root, profile_key)
        if not port or not api_key:
            _finish_run(
                server,
                run_id,
                status="failed",
                phase="configuration_error",
                message="Profile API server is not configured.",
                error="Profile API server is not configured.",
            )
            return

        profile = _profile_record(server.repo_root, profile_key)
        timeout_seconds = _request_timeout_for_profile(profile)
        request = Request(
            url=f"http://127.0.0.1:{port}/v1/chat/completions",
            data=json.dumps(run_record.get("request_body") or {}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        request_session_id = str(run_record.get("session_id") or "").strip()
        if request_session_id:
            request.add_header("X-Hermes-Session-Id", request_session_id)

        with server.run_lock:
            run_record = _load_run(server.repo_root, run_id)
            if run_record:
                _append_checkpoint(
                    run_record,
                    status="running",
                    phase="awaiting_response",
                    message="Hermes accepted the run and is working in the background.",
                )
                _store_run(server.repo_root, run_record)

        with urlopen(request, timeout=timeout_seconds) as response:
            response_session_id = str(response.headers.get("X-Hermes-Session-Id") or request_session_id)
            raw = json.loads(response.read().decode("utf-8"))

        content = ""
        choices = raw.get("choices") or []
        if choices:
            content = str(((choices[0] or {}).get("message") or {}).get("content") or "")
        quality_issues = _execution_quality_issues(content)
        if quality_issues:
            _finish_run(
                server,
                run_id,
                status="failed",
                phase="quality_gate_failed",
                message="Background run failed the execution quality gate.",
                output=content,
                error=" ".join(quality_issues),
                session_id=response_session_id,
                response_raw=raw,
            )
            return

        _finish_run(
            server,
            run_id,
            status="completed",
            phase="completed",
            message="Background run completed successfully.",
            output=content,
            session_id=response_session_id,
            response_raw=raw,
        )
    except HTTPError as exc:
        details = ""
        try:
            details = exc.read().decode("utf-8", errors="replace")
        except Exception:
            details = ""
        _finish_run(
            server,
            run_id,
            status="failed",
            phase="http_error",
            message="The specialist API returned an HTTP error.",
            error=_clip_text(details or str(exc), 1200),
        )
    except URLError as exc:
        _finish_run(
            server,
            run_id,
            status="failed",
            phase="network_error",
            message="The portal could not reach the specialist API.",
            error=str(exc),
        )
    except Exception as exc:  # pragma: no cover - defensive runtime path
        _finish_run(
            server,
            run_id,
            status="failed",
            phase="runtime_error",
            message="The background run failed before completion.",
            error=str(exc),
        )
    finally:
        stop_event.set()
        with server.run_lock:
            server.run_threads.pop(run_id, None)


def _launch_run(server: "PortalServer", run_id: str) -> None:
    worker = threading.Thread(
        target=_run_worker,
        args=(server, run_id),
        daemon=True,
        name=f"portal-run-{run_id}",
    )
    with server.run_lock:
        server.run_threads[run_id] = worker
    worker.start()


def _guess_attachment_suffix(mime_type: str) -> str:
    suffix = mimetypes.guess_extension(mime_type) or ""
    if suffix == ".jpe":
        return ".jpg"
    return suffix or ".bin"


def _decode_image_data_url(data_url: str) -> tuple[str, bytes]:
    if not data_url.startswith("data:") or "," not in data_url:
        raise ValueError("Image attachments must be sent as base64 data URLs.")

    header, encoded = data_url.split(",", 1)
    if ";base64" not in header:
        raise ValueError("Image attachments must use base64 encoding.")

    mime_type = header[5:].split(";", 1)[0].strip().lower() or "application/octet-stream"
    if not mime_type.startswith("image/"):
        raise ValueError("Only image attachments are supported.")

    try:
        raw = base64.b64decode(encoded, validate=True)
    except binascii.Error as exc:
        raise ValueError("Image attachment payload was not valid base64.") from exc

    if len(raw) > MAX_ATTACHMENT_BYTES:
        raise ValueError(
            f"Each image must stay under {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB after decoding."
        )
    return mime_type, raw


def _normalize_attachment_payload(raw_attachments: object) -> list[dict[str, object]]:
    if not raw_attachments:
        return []
    if not isinstance(raw_attachments, list):
        raise ValueError("attachments must be a list")
    if len(raw_attachments) > MAX_ATTACHMENTS_PER_MESSAGE:
        raise ValueError(f"No more than {MAX_ATTACHMENTS_PER_MESSAGE} images can be sent at once.")

    attachments: list[dict[str, object]] = []
    for raw_attachment in raw_attachments:
        if not isinstance(raw_attachment, dict):
            raise ValueError("attachments entries must be objects")
        data_url = str(raw_attachment.get("data_url") or "").strip()
        mime_type, binary = _decode_image_data_url(data_url)
        name = Path(str(raw_attachment.get("name") or "image")).name or "image"
        attachments.append(
            {
                "name": name,
                "mime_type": mime_type,
                "binary": binary,
                "size_bytes": len(binary),
            }
        )
    return attachments


def _store_attachment(root_dir: Path, attachment: dict[str, object]) -> dict[str, object]:
    upload_dir = _portal_upload_dir(root_dir)
    mime_type = str(attachment["mime_type"])
    filename = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:10]}{_guess_attachment_suffix(mime_type)}"
    stored_path = upload_dir / filename
    stored_path.write_bytes(bytes(attachment["binary"]))
    return {
        "name": str(attachment["name"]),
        "mime_type": mime_type,
        "size_bytes": int(attachment["size_bytes"]),
        "stored_path": str(stored_path),
    }


def _extract_json_block(output: str) -> dict[str, object] | None:
    cleaned = output.strip()
    if not cleaned:
        return None
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None


def _run_vision_analysis(root_dir: Path, image_path: str) -> str:
    python_bin = hermes_state_dir(root_dir) / "venv" / "bin" / "python"
    if not python_bin.exists():
        return ""

    env = os.environ.copy()
    env["HERMES_HOME"] = str(profiles_dir(root_dir) / VISION_PROFILE_KEY)
    env.setdefault("HERMES_QUIET", "1")

    try:
        completed = subprocess.run(
            [str(python_bin), "-c", VISION_RUNNER, image_path, VISION_ANALYSIS_PROMPT],
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""

    if completed.returncode != 0:
        return ""

    payload = _extract_json_block(completed.stdout)
    if not payload or not payload.get("success"):
        return ""
    return str(payload.get("analysis") or "").strip()


def _enrich_user_message(content: str, stored_attachments: list[dict[str, object]], root_dir: Path) -> str:
    if not stored_attachments:
        return content

    enriched_parts: list[str] = []
    for attachment in stored_attachments:
        stored_path = str(attachment["stored_path"])
        analysis = _run_vision_analysis(root_dir, stored_path)
        if analysis:
            enriched_parts.append(
                f"[The user attached image {attachment['name']}~ Here's what I can see:\n{analysis}]\n"
                f"[If you need a closer look, use vision_analyze with image_url: {stored_path} ~]"
            )
        else:
            enriched_parts.append(
                f"[The user attached image {attachment['name']} but it could not be auto-analyzed this time. "
                f"You can still inspect it with vision_analyze using image_url: {stored_path}]"
            )

    prefix = "\n\n".join(enriched_parts)
    if content:
        return f"{prefix}\n\n{content}"
    return prefix


def _prepare_chat_messages(
    root_dir: Path,
    messages: list[object],
) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    prepared_messages: list[dict[str, str]] = []
    prepared_updates: list[dict[str, object]] = []

    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("messages entries must be objects")

        role = str(message.get("role") or "").strip()
        if role not in {"system", "user", "assistant"}:
            raise ValueError("messages must use system, user, or assistant roles")

        content = str(message.get("content") or "")
        prepared_message = {
            "role": role,
            "content": content,
        }

        if role == "user":
            attachments = _normalize_attachment_payload(message.get("attachments"))
            if attachments:
                stored_attachments = [_store_attachment(root_dir, attachment) for attachment in attachments]
                prepared_message["content"] = _enrich_user_message(content, stored_attachments, root_dir)
                client_id = str(message.get("client_id") or "").strip()
                if client_id:
                    prepared_updates.append(
                        {
                            "client_id": client_id,
                            "transport_content": prepared_message["content"],
                            "stored_attachments": stored_attachments,
                        }
                    )

        prepared_messages.append(prepared_message)

    return prepared_messages, prepared_updates


class PortalHandler(BaseHTTPRequestHandler):
    server_version = "HermesOperatorPortal/1.0"

    def do_GET(self) -> None:  # noqa: N802
        self._handle_read_request(head_only=False)

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle_read_request(head_only=True)

    def _handle_read_request(self, *, head_only: bool) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/branding/"):
            self._serve_branding_asset(
                parsed.path.removeprefix("/branding/"),
                head_only=head_only,
            )
            return
        if parsed.path in {"/", "/index.html"}:
            self._serve_static("index.html", head_only=head_only)
            return
        if parsed.path == "/styles.css":
            self._serve_static("styles.css", head_only=head_only)
            return
        if parsed.path == "/app.js":
            self._serve_static("app.js", head_only=head_only)
            return
        if parsed.path in {"/health", "/healthz", "/api/health"}:
            self._send_json(
                {
                    "ok": True,
                    "service": "hermes-operator-portal",
                    "status": "healthy",
                },
                head_only=head_only,
            )
            return
        if parsed.path == "/api/bootstrap":
            _mark_stale_dispatches_failed(self.server.repo_root)
            self._send_json(build_snapshot(self.server.repo_root), head_only=head_only)
            return
        if re.fullmatch(r"/api/sessions/[^/]+/messages", parsed.path):
            session_id = parsed.path.split("/")[3]
            query = parse_qs(parsed.query)
            profile_key = str((query.get("profile") or ["operator"])[0] or "operator").strip()
            valid_profiles = {spec.key for spec in PROFILE_SPECS}
            if profile_key not in valid_profiles:
                self.send_error(HTTPStatus.BAD_REQUEST, "Unknown profile")
                return
            payload = _load_session_messages(
                self.server.repo_root,
                profile_key=profile_key,
                session_id=session_id,
            )
            if not payload:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown session")
                return
            resolved_session_id, messages, session = payload
            self._send_json(
                {
                    "ok": True,
                    "profile": profile_key,
                    "session_id": resolved_session_id,
                    "session": session or {},
                    "messages": messages,
                },
                head_only=head_only,
            )
            return
        if parsed.path == "/api/runs":
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or [RUN_LIST_LIMIT])[0])
            except (TypeError, ValueError):
                limit = RUN_LIST_LIMIT
            self._send_json(
                {
                    "ok": True,
                    "runs": _list_runs(self.server.repo_root, limit=max(1, min(limit, 100))),
                },
                head_only=head_only,
            )
            return
        if parsed.path == "/api/dispatches":
            _mark_stale_dispatches_failed(self.server.repo_root)
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or [DISPATCH_LIST_LIMIT])[0])
            except (TypeError, ValueError):
                limit = DISPATCH_LIST_LIMIT
            self._send_json(
                {
                    "ok": True,
                    "dispatches": _list_dispatches(self.server.repo_root, limit=max(1, min(limit, 100))),
                },
                head_only=head_only,
            )
            return
        if parsed.path == "/api/monitor":
            _mark_stale_dispatches_failed(self.server.repo_root)
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or [MONITOR_ALERT_LIMIT])[0])
            except (TypeError, ValueError):
                limit = MONITOR_ALERT_LIMIT
            self._send_json(
                {
                    "ok": True,
                    "alerts": _build_monitor_alerts(self.server.repo_root, limit=max(1, min(limit, 100))),
                },
                head_only=head_only,
            )
            return
        if parsed.path == "/api/mission-cards":
            self._send_json(
                {
                    "ok": True,
                    "mission_cards": mission_cards(self.server.repo_root),
                },
                head_only=head_only,
            )
            return
        if parsed.path == "/api/watch":
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or [6])[0])
            except (TypeError, ValueError):
                limit = 6
            self._send_json(watch_digest(self.server.repo_root, limit=max(1, min(limit, 24))), head_only=head_only)
            return
        if parsed.path == "/api/handoffs":
            query = parse_qs(parsed.query)
            project_id = str((query.get("project_id") or [""])[0]).strip()
            status = str((query.get("status") or [""])[0]).strip()
            try:
                limit = int((query.get("limit") or [24])[0])
            except (TypeError, ValueError):
                limit = 24
            self._send_json(
                {
                    "ok": True,
                    "handoffs": list_handoffs(
                        self.server.repo_root,
                        project_id=project_id,
                        status=status,
                        limit=max(1, min(limit, 100)),
                    ),
                },
                head_only=head_only,
            )
            return
        if parsed.path == "/api/self-improvement":
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or [12])[0])
            except (TypeError, ValueError):
                limit = 12
            self._send_json(
                self_improvement_snapshot(self.server.repo_root, limit=max(1, min(limit, 50))),
                head_only=head_only,
            )
            return
        if parsed.path == "/api/truth-loop":
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or [12])[0])
            except (TypeError, ValueError):
                limit = 12
            self._send_json(
                truth_loop_snapshot(self.server.repo_root, limit=max(1, min(limit, 50))),
                head_only=head_only,
            )
            return
        if parsed.path == "/api/brain-graph":
            query = parse_qs(parsed.query)
            try:
                cognitive_limit = int((query.get("cognitive_limit") or [28])[0])
            except (TypeError, ValueError):
                cognitive_limit = 28
            self._send_json(
                brain_graph(self.server.repo_root, cognitive_limit=max(1, min(cognitive_limit, 100))),
                head_only=head_only,
            )
            return
        if parsed.path.startswith("/api/runs/"):
            run_id = parsed.path.removeprefix("/api/runs/").strip()
            if not run_id:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing run id")
                return
            with self.server.run_lock:
                run_record = _load_run(self.server.repo_root, run_id)
            if not run_record:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown run")
                return
            self._send_json({"ok": True, "run": _run_summary(run_record)}, head_only=head_only)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown route")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON payload")
            return

        if parsed.path == "/api/chat":
            self._handle_chat(payload)
            return
        if parsed.path == "/api/runs":
            self._handle_run_create(payload)
            return
        if parsed.path == "/api/projects/activate":
            self._handle_project_activate(payload)
            return
        if parsed.path == "/api/projects/archive":
            self._handle_project_archive(payload)
            return
        if parsed.path == "/api/briefing":
            self._handle_briefing(payload)
            return
        if parsed.path == "/api/handoff":
            self._handle_handoff(payload)
            return
        if parsed.path == "/api/handoff/status":
            self._handle_handoff_status(payload)
            return
        if parsed.path == "/api/self-improvement/propose":
            self._handle_self_improvement(payload)
            return
        if parsed.path == "/api/self-improvement/status":
            self._handle_self_improvement_status(payload)
            return
        if parsed.path == "/api/truth-loop/run":
            self._handle_truth_loop(payload)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Unknown route")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _handle_chat(self, payload: dict[str, object]) -> None:
        profile_key = str(payload.get("profile") or "").strip()
        explicit_project_id = str(payload.get("project_id") or "").strip()
        requested_session_id = str(payload.get("session_id") or "").strip()
        messages = payload.get("messages") or []
        valid_profiles = {spec.key for spec in PROFILE_SPECS}
        if profile_key not in valid_profiles:
            self.send_error(HTTPStatus.BAD_REQUEST, "Unknown profile")
            return
        if not isinstance(messages, list) or not messages:
            self.send_error(HTTPStatus.BAD_REQUEST, "messages is required")
            return

        try:
            prepared_messages, prepared_updates = _prepare_chat_messages(self.server.repo_root, messages)
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return

        effective_project_id = _infer_project_id(
            self.server.repo_root,
            profile_key=profile_key,
            explicit_project_id=explicit_project_id,
            messages=prepared_messages,
        )
        requested_fast = bool(payload.get("fast") or str(payload.get("mode") or "").strip().lower() == "fast")
        if requested_fast:
            fast_response = fast_route_chat(
                self.server.repo_root,
                profile_key=profile_key,
                project_id=effective_project_id,
                messages=[message for message in prepared_messages if isinstance(message, dict)],
            )
            if fast_response is not None:
                fast_response["prepared_updates"] = prepared_updates
                self._send_json(fast_response)
                return
        projects = discover_projects(self.server.repo_root)
        project = next((row for row in projects if str(row.get("project_id") or "") == effective_project_id), None)
        context_message = _project_context_message(self.server.repo_root, effective_project_id)
        work_order = build_work_order(
            profile_key=profile_key,
            project=project,
            messages=prepared_messages,
            source="portal-chat",
        )
        injected_messages = [_runtime_contract_message(profile_key)]
        if context_message:
            injected_messages.append(context_message)
        injected_messages.append(work_order_message(work_order))
        prepared_messages = [*injected_messages, *prepared_messages]

        port, api_key = _profile_api_credentials(self.server.repo_root, profile_key)
        if not port or not api_key:
            self.send_error(HTTPStatus.BAD_REQUEST, "Profile API server is not configured")
            return

        profile = _profile_record(self.server.repo_root, profile_key)
        request_body = json.dumps(
            {
                "model": profile_key,
                "messages": prepared_messages,
                "stream": False,
            }
        ).encode("utf-8")
        request_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if requested_session_id:
            request_headers["X-Hermes-Session-Id"] = requested_session_id

        request = Request(
            url=f"http://127.0.0.1:{port}/v1/chat/completions",
            data=request_body,
            headers=request_headers,
            method="POST",
        )

        timeout_seconds = _request_timeout_for_profile(profile)
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                response_session_id = str(
                    response.headers.get("X-Hermes-Session-Id") or requested_session_id
                )
                raw = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, socket.timeout) as exc:  # pragma: no cover - network error path
            self._send_json(
                {
                    "ok": False,
                    "profile": profile_key,
                    "project_id": effective_project_id,
                    "error": f"Timed out after {timeout_seconds} seconds: {exc}",
                    "hint": "Use the background-run flow for very long requests or retry after narrowing the task.",
                },
                status=HTTPStatus.GATEWAY_TIMEOUT,
            )
            return
        except Exception as exc:  # pragma: no cover - network error path
            self._send_json(
                {
                "ok": False,
                    "profile": profile_key,
                    "project_id": effective_project_id,
                    "error": str(exc),
                    "hint": f"Start the profile gateway with ./scripts/run-hermes-gateway.sh {profile_key}",
                },
                status=HTTPStatus.BAD_GATEWAY,
            )
            return

        content = ""
        choices = raw.get("choices") or []
        if choices:
            content = str(((choices[0] or {}).get("message") or {}).get("content") or "")
        display_content, structured_result = parse_assistant_output(content)
        quality_flags = _execution_quality_issues(content)
        raw_user_message = _latest_user_message([message for message in messages if isinstance(message, dict)])
        try:
            _mirror_portal_chat_to_discord(
                self.server.repo_root,
                profile_key=profile_key,
                session_id=response_session_id,
                user_text=raw_user_message,
                assistant_text=display_content,
            )
        except Exception:
            pass
        self._send_json(
            {
                "ok": True,
                "profile": profile_key,
                "project_id": effective_project_id,
                "label": profile.get("label"),
                "session_id": response_session_id,
                "content": display_content,
                "structured_result": structured_result,
                "work_order": work_order,
                "quality_flags": quality_flags,
                "prepared_updates": prepared_updates,
                "raw": raw,
            }
        )

    def _handle_project_activate(self, payload: dict[str, object]) -> None:
        project_id = str(payload.get("project_id") or "").strip()
        reason = str(payload.get("reason") or "").strip()
        if not project_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "project_id is required")
            return
        try:
            activate_project(self.server.repo_root, project_id=project_id, reason=reason)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown project")
            return
        self._send_json(_project_action_payload(self.server.repo_root, project_id))

    def _handle_project_archive(self, payload: dict[str, object]) -> None:
        project_id = str(payload.get("project_id") or "").strip()
        reason = str(payload.get("reason") or "").strip()
        if not project_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "project_id is required")
            return
        try:
            archive_project(self.server.repo_root, project_id=project_id, reason=reason)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown project")
            return
        self._send_json(
            {
                "ok": True,
                "project_id": project_id,
                "portfolio": build_snapshot(self.server.repo_root).get("portfolio"),
            }
        )

    def _handle_briefing(self, payload: dict[str, object]) -> None:
        project_id = str(payload.get("project_id") or "").strip()
        depth = str(payload.get("depth") or "short").strip().lower()
        mode = str(payload.get("mode") or "normal").strip().lower()
        if depth not in {"short", "medium", "deep"}:
            depth = "short"
        if mode not in {"normal", "car"}:
            mode = "normal"
        self._send_json(build_briefing(self.server.repo_root, project_id, depth=depth, mode=mode))

    def _handle_handoff(self, payload: dict[str, object]) -> None:
        project_id = str(payload.get("project_id") or "").strip()
        target = str(payload.get("target") or payload.get("agent") or "").strip()
        instruction = str(payload.get("instruction") or "").strip()
        if not project_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "project_id is required")
            return
        try:
            handoff = create_handoff(
                self.server.repo_root,
                project_id=project_id,
                target=target,
                instruction=instruction,
                source="operator",
            )
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown project")
            return
        self._send_json({"ok": True, "handoff": handoff})

    def _handle_handoff_status(self, payload: dict[str, object]) -> None:
        handoff_id = str(payload.get("handoff_id") or "").strip()
        status = str(payload.get("status") or "").strip()
        note = str(payload.get("note") or "").strip()
        if not handoff_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "handoff_id is required")
            return
        try:
            handoff = update_handoff_status(
                self.server.repo_root,
                handoff_id=handoff_id,
                status=status,
                note=note,
            )
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown handoff")
            return
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_json({"ok": True, "handoff": handoff})

    def _handle_self_improvement(self, payload: dict[str, object]) -> None:
        focus = str(payload.get("focus") or "").strip()
        self._send_json({"ok": True, "proposal": self_improvement_proposal(self.server.repo_root, focus=focus)})

    def _handle_self_improvement_status(self, payload: dict[str, object]) -> None:
        proposal_id = str(payload.get("proposal_id") or "").strip()
        status = str(payload.get("status") or "").strip()
        note = str(payload.get("note") or "").strip()
        if not proposal_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "proposal_id is required")
            return
        try:
            proposal = update_self_improvement_status(
                self.server.repo_root,
                proposal_id=proposal_id,
                status=status,
                note=note,
            )
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown proposal")
            return
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_json({"ok": True, "proposal": proposal})

    def _handle_truth_loop(self, payload: dict[str, object]) -> None:
        focus = str(payload.get("focus") or "").strip() or "operator truth loop"
        self._send_json(run_truth_loop(self.server.repo_root, focus=focus))

    def _handle_run_create(self, payload: dict[str, object]) -> None:
        profile_key = str(payload.get("profile") or "").strip()
        explicit_project_id = str(payload.get("project_id") or "").strip()
        requested_session_id = str(payload.get("session_id") or "").strip()
        messages = payload.get("messages") or []
        valid_profiles = {spec.key for spec in PROFILE_SPECS}
        if profile_key not in valid_profiles:
            self.send_error(HTTPStatus.BAD_REQUEST, "Unknown profile")
            return
        if not isinstance(messages, list) or not messages:
            self.send_error(HTTPStatus.BAD_REQUEST, "messages is required")
            return

        try:
            prepared_messages, prepared_updates = _prepare_chat_messages(self.server.repo_root, messages)
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return

        effective_project_id = _infer_project_id(
            self.server.repo_root,
            profile_key=profile_key,
            explicit_project_id=explicit_project_id,
            messages=prepared_messages,
        )
        projects = discover_projects(self.server.repo_root)
        project = next((row for row in projects if str(row.get("project_id") or "") == effective_project_id), None)
        context_message = _project_context_message(self.server.repo_root, effective_project_id)
        work_order = build_work_order(
            profile_key=profile_key,
            project=project,
            messages=prepared_messages,
            source="portal-run",
        )
        injected_messages = [_runtime_contract_message(profile_key)]
        if context_message:
            injected_messages.append(context_message)
        injected_messages.append(work_order_message(work_order))
        prepared_messages = [*injected_messages, *prepared_messages]

        port, api_key = _profile_api_credentials(self.server.repo_root, profile_key)
        if not port or not api_key:
            self.send_error(HTTPStatus.BAD_REQUEST, "Profile API server is not configured")
            return

        profile = _profile_record(self.server.repo_root, profile_key)
        latest_user_message = _latest_user_message(prepared_messages)
        active_run = _existing_active_run(
            self.server.repo_root,
            profile_key=profile_key,
            project_id=effective_project_id,
        )
        if active_run is not None:
            self._send_json(
                {
                    "ok": False,
                    "error": "A run for this lane and project is already active.",
                    "existing_run": active_run,
                },
                status=HTTPStatus.CONFLICT,
            )
            return
        run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        run_record: dict[str, object] = {
            "run_id": run_id,
            "profile_key": profile_key,
            "profile_label": profile.get("label") or profile_key,
            "project_id": effective_project_id,
            "session_id": requested_session_id,
            "status": "queued",
            "phase": "queued",
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "started_at": "",
            "completed_at": "",
            "last_checkpoint_at": "",
            "latest_checkpoint": "",
            "objective_preview": _clip_text(latest_user_message, 220),
            "latest_user_message": latest_user_message,
            "attachment_count": sum(
                len(update.get("stored_attachments") or [])
                for update in prepared_updates
                if isinstance(update, dict)
            ),
            "prepared_updates": prepared_updates,
            "work_order": work_order,
            "output": "",
            "error": "",
            "request_body": {
                "model": profile_key,
                "messages": prepared_messages,
                "stream": False,
            },
            "checkpoints": [],
            "response_raw": {},
        }
        _append_checkpoint(
            run_record,
            status="queued",
            phase="queued",
            message="Background run accepted by the portal and queued for dispatch.",
        )

        with self.server.run_lock:
            _store_run(self.server.repo_root, run_record)

        _launch_run(self.server, run_id)
        self._send_json(
            {
                "ok": True,
                "run": _run_summary(run_record),
                "work_order": work_order,
                "prepared_updates": prepared_updates,
            },
            status=HTTPStatus.ACCEPTED,
        )

    def _serve_static(self, relative_path: str, *, head_only: bool = False) -> None:
        path = STATIC_DIR / relative_path
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Missing static asset")
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def _serve_branding_asset(self, relative_path: str, *, head_only: bool = False) -> None:
        branding_root = (self.server.repo_root / "branding").resolve()
        candidate = (branding_root / relative_path).resolve()

        try:
            candidate.relative_to(branding_root)
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown branding asset")
            return

        if not candidate.exists() or not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Missing branding asset")
            return

        data = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def _send_json(
        self,
        payload: object,
        *,
        status: HTTPStatus = HTTPStatus.OK,
        head_only: bool = False,
    ) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)


class PortalServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_cls: type[BaseHTTPRequestHandler], repo_root: Path) -> None:
        super().__init__(server_address, handler_cls)
        self.repo_root = repo_root
        self.run_lock = threading.RLock()
        self.run_threads: dict[str, threading.Thread] = {}
        _mark_inflight_runs_interrupted(repo_root, self.run_lock)
        _mark_stale_dispatches_failed(repo_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the standalone Hermes operator portal.")
    parser.add_argument("--root-dir", default=".", help="Repository root")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8799, help="Bind port")
    args = parser.parse_args()

    root = repo_root(args.root_dir)
    server = PortalServer((args.host, args.port), PortalHandler, root)
    print(f"Hermes operator portal running on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
