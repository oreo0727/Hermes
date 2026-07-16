"""Project records and orchestration control-plane helpers for Hermes studio work."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

from hermes_stack.orchestration import build_delivery_model, extract_operator_request_text
from hermes_stack.state_store import (
    list_dispatches as store_list_dispatches,
    list_portal_runs as store_list_portal_runs,
    list_project_entries,
    load_portfolio_payload,
    load_project_entry,
    save_portfolio_payload,
    save_project_payload,
)


PROJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
TRACK_NAMES = ("app", "game", "creative")
VALID_LANES = ("operator", "app-dev", "game-dev", "creative-dev")
PORTFOLIO_SCHEMA_VERSION = "1"
PROJECT_TRACK_ALIASES = {
    "app": ("app", "tools", "scripts"),
    "game": ("game", "godot-maze", "godot-web", "maze-forest", "narrative-maze", "narrative-maze-prototype"),
    "creative": ("creative", "docs/ui", "branding"),
}
IGNORED_PATH_PARTS = {
    ".git",
    ".godot",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "venv",
    ".venv",
    "build",
    "_archive",
}


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    title: str
    summary: str
    status: str
    specialists: tuple[str, ...]
    owner: str
    now: str
    next: str
    blocked: tuple[str, ...]
    done: tuple[str, ...]
    percent_override: int | None
    priority_override: int | None
    project_kind: str
    control_mode: str
    delivery_target: str
    primary_artifact: str
    acceptance: tuple[str, ...]
    primary_lane: str
    lane_sequence: tuple[str, ...]
    strict_dispatch: bool
    capability_gaps: tuple[str, ...]
    root: Path
    created_at: str
    updated_at: str


def repo_root(root_dir: str | Path | None = None) -> Path:
    if root_dir is not None:
        return Path(root_dir).resolve()
    return Path(__file__).resolve().parents[1]


def projects_dir(root_dir: str | Path | None = None) -> Path:
    return repo_root(root_dir) / "state" / "projects"


def project_dir(root_dir: str | Path | None, project_id: str) -> Path:
    return projects_dir(root_dir) / project_id


def orchestration_state_dir(root_dir: str | Path | None = None) -> Path:
    path = repo_root(root_dir) / "state" / "hermes" / "orchestration"
    path.mkdir(parents=True, exist_ok=True)
    return path


def portfolio_state_path(root_dir: str | Path | None = None) -> Path:
    return orchestration_state_dir(root_dir) / "portfolio.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        try:
            if not item.is_file() or _path_is_ignored(item):
                continue
        except OSError:
            continue
        total += 1
    return total


def _path_is_ignored(path: Path) -> bool:
    return any(part in IGNORED_PATH_PARTS for part in path.parts)


def _project_file_rows(path: Path) -> list[tuple[float, Path]]:
    if not path.exists():
        return []
    rows: list[tuple[float, Path]] = []
    for item in path.rglob("*"):
        try:
            if not item.is_file() or _path_is_ignored(item):
                continue
            rows.append((item.stat().st_mtime, item))
        except OSError:
            continue
    rows.sort(key=lambda entry: entry[0], reverse=True)
    return rows


def _project_repo_root(project_root: Path) -> Path:
    return project_root.resolve().parents[2]


def _project_hermes_state_dir(project_root: Path) -> Path:
    return _project_repo_root(project_root) / "state" / "hermes"


def _count_unique_files(paths: tuple[Path, ...]) -> int:
    seen: set[Path] = set()
    for base_path in paths:
        if not base_path.exists():
            continue
        for item in base_path.rglob("*"):
            if not item.is_file() or _path_is_ignored(item):
                continue
            try:
                seen.add(item.resolve())
            except OSError:
                continue
    return len(seen)


def _track_file_counts(record: ProjectRecord) -> dict[str, int]:
    counts: dict[str, int] = {}
    for track in TRACK_NAMES:
        candidates = tuple(record.root / relative_path for relative_path in PROJECT_TRACK_ALIASES.get(track, (track,)))
        counts[track] = _count_unique_files(candidates)
    return counts


def _load_json_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _linked_portal_runs(record: ProjectRecord) -> list[dict[str, Any]]:
    rows = store_list_portal_runs(_project_repo_root(record.root))
    return [row for row in rows if str(row.get("project_id") or "") == record.project_id]


def _linked_dispatches(record: ProjectRecord) -> list[dict[str, Any]]:
    rows = store_list_dispatches(_project_repo_root(record.root))
    return [row for row in rows if str(row.get("project_id") or "") == record.project_id]


def _linked_run_count(record: ProjectRecord) -> int:
    run_ids: set[str] = set()
    runs_dir = record.root / "runs"
    if runs_dir.exists():
        for path in runs_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                run_ids.add(path.stem)
                continue
            run_ids.add(str(payload.get("run_id") or path.stem))
    for row in _linked_portal_runs(record):
        run_ids.add(str(row.get("run_id") or ""))
    run_ids.discard("")
    return len(run_ids)


def _linked_dispatch_count(record: ProjectRecord) -> int:
    dispatch_ids = {
        str(row.get("dispatch_id") or "")
        for row in _linked_dispatches(record)
    }
    dispatch_ids.discard("")
    return len(dispatch_ids)


def _active_attempt_summary(record: ProjectRecord) -> dict[str, object]:
    runs = _linked_portal_runs(record)
    dispatches = _linked_dispatches(record)
    active_statuses = {"queued", "running"}

    active_runs = [row for row in runs if str(row.get("status") or "") in active_statuses]
    active_dispatches = [row for row in dispatches if str(row.get("status") or "") in active_statuses]
    closed_failures = [
        row
        for row in [*runs, *dispatches]
        if str(row.get("status") or "") in {"failed", "interrupted"}
    ]

    loop_risk = "low"
    if len(active_runs) + len(active_dispatches) > 1:
        loop_risk = "high"
    elif closed_failures and (active_runs or active_dispatches):
        loop_risk = "elevated"

    latest_active = None
    sortable = active_runs + active_dispatches
    if sortable:
        latest_active = sorted(
            sortable,
            key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""),
            reverse=True,
        )[0]

    return {
        "active_runs": len(active_runs),
        "active_dispatches": len(active_dispatches),
        "active_attempts": len(active_runs) + len(active_dispatches),
        "retry_count": len(closed_failures),
        "loop_risk": loop_risk,
        "latest_active_status": str((latest_active or {}).get("status") or ""),
        "latest_active_updated_at": str((latest_active or {}).get("updated_at") or (latest_active or {}).get("created_at") or ""),
    }


def _proof_rows(
    record: ProjectRecord,
    *,
    recent_file_rows: list[dict[str, str]],
    primary_artifact: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_row(path_value: str, source: str, updated_at: str) -> None:
        normalized = path_value.strip()
        if not normalized or normalized in seen:
            return
        rows.append(
            {
                "path": normalized,
                "source": source,
                "updated_at": updated_at,
            }
        )
        seen.add(normalized)

    if primary_artifact:
        add_row(primary_artifact, "primary-artifact", record.updated_at)

    for item in recent_file_rows[:6]:
        add_row(str(item.get("path") or ""), "recent-file", str(item.get("updated_at") or ""))

    for source_name, collection in (
        ("run-artifact", _linked_portal_runs(record)),
        ("dispatch-artifact", _linked_dispatches(record)),
    ):
        for row in collection:
            structured = row.get("structured_result")
            if not isinstance(structured, dict):
                continue
            artifacts = structured.get("artifacts")
            if not isinstance(artifacts, list):
                continue
            for artifact in artifacts[:6]:
                add_row(str(artifact or ""), source_name, str(row.get("updated_at") or row.get("created_at") or ""))

    rows.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    return rows[:8]


def _linked_activity_rows(record: ProjectRecord) -> list[tuple[float, str]]:
    rows: list[tuple[float, str]] = []
    for run in _linked_portal_runs(record):
        updated_at = _parse_iso_timestamp(
            run.get("last_checkpoint_at") or run.get("completed_at") or run.get("updated_at") or run.get("created_at")
        )
        if updated_at is None:
            continue
        rows.append(
            (
                updated_at.timestamp(),
                f"portal-runs/{run.get('run_id') or 'run'}.json",
            )
        )
    for dispatch in _linked_dispatches(record):
        updated_at = _parse_iso_timestamp(
            dispatch.get("completed_at") or dispatch.get("updated_at") or dispatch.get("created_at")
        )
        if updated_at is None:
            continue
        rows.append(
            (
                updated_at.timestamp(),
                f"specialist-dispatches/{dispatch.get('dispatch_id') or 'dispatch'}.json",
            )
        )
    rows.sort(key=lambda entry: entry[0], reverse=True)
    return rows


def _timestamp_to_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _parse_iso_timestamp(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _activity_state(last_activity_at: str) -> str:
    if not last_activity_at:
        return "idle"
    try:
        last_activity = datetime.fromisoformat(last_activity_at)
    except ValueError:
        return "idle"
    age_seconds = (datetime.now(timezone.utc) - last_activity.astimezone(timezone.utc)).total_seconds()
    if age_seconds <= 3600:
        return "hot"
    if age_seconds <= 86400:
        return "warm"
    return "idle"


def _progress_stage(*, docs_ready: int, total_track_files: int, artifact_count: int, run_count: int) -> str:
    if docs_ready < 2 and not total_track_files:
        return "briefing"
    if docs_ready == 3 and not total_track_files and not run_count:
        return "framing"
    if total_track_files and not artifact_count:
        return "building"
    if artifact_count and not run_count:
        return "packaging"
    if artifact_count and run_count:
        return "shipping"
    return "active"


def _progress_percent(
    *,
    docs_ready: int,
    specialist_count: int,
    total_track_files: int,
    artifact_count: int,
    run_count: int,
) -> int:
    score = 0.0
    score += min(docs_ready, 3) / 3 * 42
    score += min(specialist_count, 4) / 4 * 14
    score += min(total_track_files, 24) / 24 * 24
    score += min(run_count, 6) / 6 * 10
    score += min(artifact_count, 6) / 6 * 10
    return max(0, min(100, round(score)))


def _priority_score(
    *,
    status: str,
    blocked_count: int,
    activity_state: str,
    progress_percent: int,
    priority_override: int | None,
) -> int:
    if priority_override is not None:
        return max(0, min(100, priority_override))

    score = 0
    normalized_status = (status or "active").strip().lower()
    if normalized_status == "blocked":
        score += 40
    elif normalized_status == "active":
        score += 24
    elif normalized_status == "paused":
        score += 8
    elif normalized_status in {"done", "archived"}:
        score += 0
    else:
        score += 16

    score += min(blocked_count, 3) * 10
    if activity_state == "hot":
        score += 18
    elif activity_state == "warm":
        score += 10
    elif activity_state == "idle":
        score += 2

    score += min(progress_percent, 70) // 7
    return max(0, min(100, score))


def _normalize_specialists(specialists: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for raw in specialists or ():
        value = raw.strip()
        if not value or value in seen:
            continue
        ordered.append(value)
        seen.add(value)
    return tuple(ordered)


def _normalize_text_list(values: object) -> tuple[str, ...]:
    if isinstance(values, str):
        values = [line.strip() for line in values.splitlines() if line.strip()]
    if not isinstance(values, (list, tuple)):
        return ()
    rows: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        normalized = text.lower()
        if normalized in seen:
            continue
        rows.append(text)
        seen.add(normalized)
    return tuple(rows)


def _normalize_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def _sanitize_tracking_value(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if (
        text.startswith("[The user attached image")
        or text.startswith("Project context\nProject:")
        or "\n\nUser request\n" in text
        or text.startswith("User request\n")
    ):
        return ""
    cleaned = extract_operator_request_text(text)
    if cleaned and cleaned != text:
        return ""
    return text


def _sanitize_tracking_items(values: list[str]) -> list[str]:
    rows: list[str] = []
    for raw in values:
        text = _sanitize_tracking_value(raw)
        if text:
            rows.append(text)
    return rows


def _normalize_lane_sequence(
    lanes: tuple[str, ...] | list[str] | None,
    *,
    specialists: tuple[str, ...] | list[str] | None = None,
) -> tuple[str, ...]:
    rows: list[str] = []
    seen: set[str] = set()
    for candidate in (*(lanes or ()), *(specialists or ())):
        lane = str(candidate or "").strip()
        if not lane or lane not in VALID_LANES or lane in seen:
            continue
        rows.append(lane)
        seen.add(lane)
    if "operator" in seen:
        rows = ["operator", *[lane for lane in rows if lane != "operator"]]
    elif specialists and "operator" in tuple(str(item).strip() for item in specialists):
        rows.insert(0, "operator")
    return tuple(rows)


def _default_primary_lane(specialists: tuple[str, ...]) -> str:
    for lane in ("game-dev", "app-dev", "creative-dev"):
        if lane in specialists:
            return lane
    return "operator"


def _infer_project_kind(title: str, summary: str, specialists: tuple[str, ...]) -> str:
    lowered = f"{title} {summary}".lower()
    if "game-dev" in specialists or any(token in lowered for token in ("game", "maze", "playable", "godot", "hud", "enemy")):
        return "game"
    if "creative-dev" in specialists and "app-dev" not in specialists and "game-dev" not in specialists:
        return "creative"
    if "app-dev" in specialists and "game-dev" not in specialists and "creative-dev" not in specialists:
        return "app"
    return "mixed"


def _default_control(title: str, summary: str, specialists: tuple[str, ...]) -> dict[str, object]:
    project_stub = {
        "title": title,
        "summary": summary,
        "specialists": list(specialists),
    }
    delivery_model = build_delivery_model(
        profile_key="operator",
        project=project_stub,
        objective=f"{title} {summary}".strip(),
    )
    lane_sequence = _normalize_lane_sequence(
        delivery_model.get("lane_sequence") if isinstance(delivery_model, dict) else (),
        specialists=specialists,
    )
    primary_lane = _default_primary_lane(lane_sequence or specialists)
    return {
        "project_kind": _infer_project_kind(title, summary, specialists),
        "control_mode": "orchestrated",
        "delivery_target": "",
        "primary_artifact": "",
        "acceptance": [],
        "primary_lane": primary_lane,
        "lane_sequence": list(lane_sequence),
        "strict_dispatch": "operator" in specialists and primary_lane != "operator",
        "capability_gaps": [],
    }


def _default_portfolio_state() -> dict[str, object]:
    return {
        "schema_version": PORTFOLIO_SCHEMA_VERSION,
        "updated_at": _now(),
        "active_project_id": "",
        "project_queue": [],
    }


def _portfolio_known_project_ids(root_dir: str | Path | None = None) -> tuple[str, ...]:
    known_ids: list[str] = []
    for manifest_root, payload in list_project_entries(root_dir):
        if manifest_root.name == "_archive":
            continue
        if str(payload.get("status") or "").strip().lower() == "archived":
            continue
        known_ids.append(manifest_root.name)
    return tuple(known_ids)


def _normalize_portfolio_binding(binding: object) -> dict[str, str] | None:
    if not isinstance(binding, dict):
        return None
    profile_key = str(binding.get("profile_key") or "").strip()
    session_id = str(binding.get("session_id") or "").strip()
    if not profile_key or not session_id:
        return None
    payload = {
        "profile_key": profile_key,
        "session_id": session_id,
        "platform": str(binding.get("platform") or "").strip(),
        "chat_id": str(binding.get("chat_id") or "").strip(),
        "updated_at": str(binding.get("updated_at") or "").strip() or _now(),
    }
    return payload


def _normalize_portfolio_entry(entry: object, *, project_id: str = "") -> dict[str, object] | None:
    payload = entry if isinstance(entry, dict) else {}
    normalized_project_id = project_id or str(payload.get("project_id") or "").strip().lower()
    if not normalized_project_id:
        return None
    state = str(payload.get("state") or "queued").strip().lower()
    if state not in {"active", "queued", "parked"}:
        state = "queued"
    session_bindings = []
    raw_bindings = payload.get("session_bindings")
    if isinstance(raw_bindings, list):
        for binding in raw_bindings:
            normalized_binding = _normalize_portfolio_binding(binding)
            if normalized_binding:
                session_bindings.append(normalized_binding)
    return {
        "project_id": normalized_project_id,
        "state": state,
        "last_activated_at": str(payload.get("last_activated_at") or "").strip(),
        "reason": str(payload.get("reason") or "").strip(),
        "session_bindings": session_bindings,
    }


def _load_portfolio_state(root_dir: str | Path | None = None) -> dict[str, object]:
    payload = load_portfolio_payload(root_dir)
    if payload is None:
        payload = _default_portfolio_state()
        return payload
    if not isinstance(payload, dict):
        return _default_portfolio_state()

    active_project_id = str(payload.get("active_project_id") or "").strip().lower()
    raw_queue = payload.get("project_queue")
    normalized_queue: list[dict[str, object]] = []
    if isinstance(raw_queue, list):
        for item in raw_queue:
            entry = _normalize_portfolio_entry(item)
            if entry:
                normalized_queue.append(entry)
    normalized = {
        "schema_version": str(payload.get("schema_version") or PORTFOLIO_SCHEMA_VERSION),
        "updated_at": str(payload.get("updated_at") or "").strip() or _now(),
        "active_project_id": active_project_id,
        "project_queue": normalized_queue,
    }
    if normalized != payload:
        save_portfolio_payload(root_dir, normalized)
    return normalized


def _save_portfolio_state(root_dir: str | Path | None, payload: dict[str, object]) -> dict[str, object]:
    normalized = {
        "schema_version": str(payload.get("schema_version") or PORTFOLIO_SCHEMA_VERSION),
        "updated_at": str(payload.get("updated_at") or "").strip() or _now(),
        "active_project_id": str(payload.get("active_project_id") or "").strip().lower(),
        "project_queue": [],
    }
    raw_queue = payload.get("project_queue")
    if isinstance(raw_queue, list):
        for item in raw_queue:
            entry = _normalize_portfolio_entry(item)
            if entry:
                normalized["project_queue"].append(entry)
    save_portfolio_payload(root_dir, normalized)
    return normalized


def _sync_portfolio_state(
    root_dir: str | Path | None,
    payload: dict[str, object],
    *,
    known_project_ids: tuple[str, ...],
) -> dict[str, object]:
    queue_rows = payload.get("project_queue")
    if not isinstance(queue_rows, list):
        queue_rows = []
    entry_map = {
        str(entry.get("project_id") or ""): entry
        for entry in queue_rows
        if isinstance(entry, dict) and str(entry.get("project_id") or "")
    }

    normalized_queue: list[dict[str, object]] = []
    seen: set[str] = set()
    for project_id in known_project_ids:
        existing = entry_map.get(project_id)
        if existing is None:
            existing = {
                "project_id": project_id,
                "state": "queued",
                "last_activated_at": "",
                "reason": "",
                "session_bindings": [],
            }
        normalized_queue.append(_normalize_portfolio_entry(existing, project_id=project_id) or {})
        seen.add(project_id)

    active_project_id = str(payload.get("active_project_id") or "").strip().lower()
    if active_project_id and active_project_id not in seen:
        active_project_id = ""

    if not active_project_id:
        for entry in normalized_queue:
            if str(entry.get("state") or "") == "active":
                active_project_id = str(entry.get("project_id") or "")
                break

    if active_project_id:
        for entry in normalized_queue:
            project_id = str(entry.get("project_id") or "")
            entry["state"] = "active" if project_id == active_project_id else ("parked" if str(entry.get("state") or "") == "parked" else "queued")
    else:
        for entry in normalized_queue:
            if str(entry.get("state") or "") == "active":
                entry["state"] = "queued"

    payload["active_project_id"] = active_project_id
    payload["project_queue"] = normalized_queue
    payload["updated_at"] = _now()
    return _save_portfolio_state(root_dir, payload)


def ensure_portfolio(root_dir: str | Path | None = None) -> dict[str, object]:
    known_project_ids = _portfolio_known_project_ids(root_dir)
    payload = _load_portfolio_state(root_dir)
    return _sync_portfolio_state(root_dir, payload, known_project_ids=known_project_ids)


def _portfolio_entry(payload: dict[str, object], project_id: str) -> dict[str, object] | None:
    queue_rows = payload.get("project_queue")
    if not isinstance(queue_rows, list):
        return None
    for entry in queue_rows:
        if str(entry.get("project_id") or "") == project_id:
            return entry
    return None


def activate_project(
    root_dir: str | Path | None,
    *,
    project_id: str,
    reason: str = "",
) -> dict[str, object]:
    normalized_id = project_id.strip().lower()
    if normalized_id in {"", "none"}:
        payload = ensure_portfolio(root_dir)
        queue_rows = payload.get("project_queue")
        if not isinstance(queue_rows, list):
            queue_rows = []
        for row in queue_rows:
            if not isinstance(row, dict):
                continue
            row["state"] = "parked" if str(row.get("state") or "") == "parked" else "queued"
        payload["active_project_id"] = ""
        payload["project_queue"] = queue_rows
        payload["updated_at"] = _now()
        return _save_portfolio_state(root_dir, payload)
    project_entry = load_project_entry(root_dir, normalized_id)
    if project_entry is None:
        raise FileNotFoundError(f"Project does not exist: {normalized_id}")
    payload = ensure_portfolio(root_dir)
    queue_rows = payload.get("project_queue")
    if not isinstance(queue_rows, list):
        queue_rows = []
    entry = _portfolio_entry(payload, normalized_id)
    if entry is None:
        entry = {
            "project_id": normalized_id,
            "state": "queued",
            "last_activated_at": "",
            "reason": "",
            "session_bindings": [],
        }
        queue_rows.append(entry)

    for row in queue_rows:
        if not isinstance(row, dict):
            continue
        row["state"] = "queued" if str(row.get("state") or "") != "parked" else "parked"

    entry["state"] = "active"
    entry["last_activated_at"] = _now()
    entry["reason"] = reason.strip()
    queue_rows[:] = [entry, *[row for row in queue_rows if row is not entry]]
    payload["active_project_id"] = normalized_id
    payload["project_queue"] = queue_rows
    payload["updated_at"] = _now()
    return _save_portfolio_state(root_dir, payload)


def bind_project_session(
    root_dir: str | Path | None,
    *,
    project_id: str,
    profile_key: str,
    session_id: str,
    platform: str = "",
    chat_id: str = "",
) -> dict[str, object]:
    normalized_id = project_id.strip().lower()
    payload = ensure_portfolio(root_dir)
    entry = _portfolio_entry(payload, normalized_id)
    if entry is None:
        raise FileNotFoundError(f"Project is not registered in the portfolio: {normalized_id}")

    bindings = entry.get("session_bindings")
    if not isinstance(bindings, list):
        bindings = []
        entry["session_bindings"] = bindings
    bindings[:] = [
        binding
        for binding in bindings
        if not (
            str(binding.get("profile_key") or "") == profile_key.strip()
            and str(binding.get("session_id") or "") == session_id.strip()
        )
    ]
    bindings.append(
        {
            "profile_key": profile_key.strip(),
            "session_id": session_id.strip(),
            "platform": platform.strip(),
            "chat_id": chat_id.strip(),
            "updated_at": _now(),
        }
    )
    entry["session_bindings"] = bindings[-8:]
    payload["updated_at"] = _now()
    return _save_portfolio_state(root_dir, payload)


def archive_project(
    root_dir: str | Path | None,
    *,
    project_id: str,
    reason: str = "",
) -> dict[str, object]:
    normalized_id = project_id.strip().lower()
    payload = ensure_portfolio(root_dir)
    queue_rows = payload.get("project_queue")
    if not isinstance(queue_rows, list):
        queue_rows = []
    queue_rows[:] = [
        row
        for row in queue_rows
        if str(row.get("project_id") or "") != normalized_id
    ]
    if str(payload.get("active_project_id") or "") == normalized_id:
        payload["active_project_id"] = str(queue_rows[0].get("project_id") or "") if queue_rows else ""
    payload["project_queue"] = queue_rows
    payload["updated_at"] = _now()
    _save_portfolio_state(root_dir, payload)
    return update_project(root_dir, project_id=normalized_id, status="archived", next_value=reason or None)


def portfolio_snapshot(root_dir: str | Path | None = None) -> dict[str, object]:
    payload = ensure_portfolio(root_dir)
    queue_rows = payload.get("project_queue")
    if not isinstance(queue_rows, list):
        queue_rows = []
    return {
        "active_project_id": str(payload.get("active_project_id") or ""),
        "project_queue": queue_rows,
        "active_count": sum(1 for row in queue_rows if str(row.get("state") or "") == "active"),
        "queued_count": sum(1 for row in queue_rows if str(row.get("state") or "") == "queued"),
        "parked_count": sum(1 for row in queue_rows if str(row.get("state") or "") == "parked"),
        "updated_at": str(payload.get("updated_at") or ""),
    }


def _markdown_section_items(path: Path, heading: str) -> tuple[str, ...]:
    if not path.exists():
        return ()

    target = heading.strip().lower()
    in_section = False
    rows: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip().lower()
            if in_section and title != target:
                break
            in_section = title == target
            continue
        if not in_section:
            continue
        if stripped.startswith(("- ", "* ")):
            rows.append(stripped[2:].strip())
    return tuple(item for item in rows if item)


def _load_record(project_root: Path, payload: dict[str, Any]) -> ProjectRecord:
    tracking = payload.get("tracking")
    if not isinstance(tracking, dict):
        tracking = {}
    control = payload.get("control")
    if not isinstance(control, dict):
        control = _default_control(
            str(payload.get("title") or ""),
            str(payload.get("summary") or ""),
            _normalize_specialists(tuple(str(item) for item in payload.get("specialists", []))),
        )
    percent_override = tracking.get("percent")
    priority_override = tracking.get("priority")
    try:
        normalized_percent_override = int(percent_override) if percent_override is not None else None
    except (TypeError, ValueError):
        normalized_percent_override = None
    try:
        normalized_priority_override = int(priority_override) if priority_override is not None else None
    except (TypeError, ValueError):
        normalized_priority_override = None

    specialists = _normalize_specialists(tuple(str(item) for item in payload.get("specialists", [])))
    lane_sequence = _normalize_lane_sequence(control.get("lane_sequence"), specialists=specialists)
    primary_lane = str(control.get("primary_lane") or "").strip()
    if primary_lane not in VALID_LANES:
        primary_lane = _default_primary_lane(lane_sequence or specialists)

    return ProjectRecord(
        project_id=str(payload["project_id"]),
        title=str(payload["title"]),
        summary=str(payload.get("summary", "")),
        status=str(payload.get("status", "active")),
        specialists=specialists,
        owner=str(tracking.get("owner", "")).strip(),
        now=str(tracking.get("now", "")).strip(),
        next=str(tracking.get("next", "")).strip(),
        blocked=_normalize_text_list(tracking.get("blocked")),
        done=_normalize_text_list(tracking.get("done")),
        percent_override=normalized_percent_override,
        priority_override=normalized_priority_override,
        project_kind=str(control.get("project_kind") or _infer_project_kind(str(payload.get("title") or ""), str(payload.get("summary") or ""), specialists)).strip(),
        control_mode=str(control.get("control_mode") or "orchestrated").strip(),
        delivery_target=str(control.get("delivery_target") or "").strip(),
        primary_artifact=str(control.get("primary_artifact") or "").strip(),
        acceptance=_normalize_text_list(control.get("acceptance")),
        primary_lane=primary_lane,
        lane_sequence=lane_sequence,
        strict_dispatch=_normalize_bool(control.get("strict_dispatch"), default=False),
        capability_gaps=_normalize_text_list(control.get("capability_gaps")),
        root=project_root,
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
    )


def _portfolio_view_for_project(
    project_id: str,
    payload: dict[str, object],
    *,
    discovered_rank: int = 0,
) -> dict[str, object]:
    queue_rows = payload.get("project_queue")
    if not isinstance(queue_rows, list):
        queue_rows = []
    queue_position = 0
    entry = None
    for index, row in enumerate(queue_rows, start=1):
        if str(row.get("project_id") or "") == project_id:
            entry = row
            queue_position = index
            break
    entry = entry or {
        "project_id": project_id,
        "state": "queued",
        "last_activated_at": "",
        "reason": "",
        "session_bindings": [],
    }
    return {
        "active": str(payload.get("active_project_id") or "") == project_id,
        "queue_position": queue_position or discovered_rank,
        "state": str(entry.get("state") or "queued"),
        "last_activated_at": str(entry.get("last_activated_at") or ""),
        "reason": str(entry.get("reason") or ""),
        "session_bindings": entry.get("session_bindings") if isinstance(entry.get("session_bindings"), list) else [],
    }


def _record_snapshot(
    record: ProjectRecord,
    *,
    portfolio_state_payload: dict[str, object] | None = None,
    discovered_rank: int = 0,
) -> dict[str, Any]:
    documents = {
        "brief": (record.root / "brief.md").exists(),
        "canon": (record.root / "canon.md").exists(),
        "roadmap": (record.root / "roadmap.md").exists(),
    }
    docs_ready = sum(1 for ready in documents.values() if ready)
    track_file_counts = _track_file_counts(record)
    total_track_files = sum(track_file_counts.values())
    artifact_count = _count_files(record.root / "artifacts")
    run_count = _linked_run_count(record)
    dispatch_count = _linked_dispatch_count(record)
    file_rows = _project_file_rows(record.root)
    linked_activity_rows = _linked_activity_rows(record)
    last_activity_candidates = [
        file_rows[0][0] if file_rows else None,
        linked_activity_rows[0][0] if linked_activity_rows else None,
        _parse_iso_timestamp(record.updated_at).timestamp() if _parse_iso_timestamp(record.updated_at) else None,
    ]
    last_activity_at = max((value for value in last_activity_candidates if value is not None), default=None)
    last_activity_iso = _timestamp_to_iso(last_activity_at) if last_activity_at is not None else record.updated_at
    roadmap_path = record.root / "roadmap.md"
    recent_file_rows = [
        {
            "path": str(path.relative_to(record.root)),
            "updated_at": _timestamp_to_iso(timestamp),
        }
        for timestamp, path in file_rows[:4]
    ]
    if len(recent_file_rows) < 4:
        seen_paths = {row["path"] for row in recent_file_rows}
        for timestamp, synthetic_path in linked_activity_rows:
            if synthetic_path in seen_paths:
                continue
            recent_file_rows.append(
                {
                    "path": synthetic_path,
                    "updated_at": _timestamp_to_iso(timestamp),
                }
            )
            seen_paths.add(synthetic_path)
            if len(recent_file_rows) >= 4:
                break
    progress_percent = (
        max(0, min(100, record.percent_override))
        if record.percent_override is not None
        else _progress_percent(
            docs_ready=docs_ready,
            specialist_count=len(record.specialists),
            total_track_files=total_track_files,
            artifact_count=artifact_count,
            run_count=run_count,
        )
    )
    owner = record.owner or (record.specialists[0] if record.specialists else "operator")
    roadmap_now = next(iter(_markdown_section_items(roadmap_path, "Now")), "")
    roadmap_next = next(iter(_markdown_section_items(roadmap_path, "Next")), "")
    now_value = _sanitize_tracking_value(record.now)
    if not now_value:
        now_value = _sanitize_tracking_value(roadmap_now)
    next_value = _sanitize_tracking_value(record.next)
    if not next_value:
        next_value = _sanitize_tracking_value(roadmap_next)
    blocked = _sanitize_tracking_items(list(record.blocked or _markdown_section_items(roadmap_path, "Blocked")))
    done = _sanitize_tracking_items(list(record.done))
    if not done and docs_ready == 3:
        done.append("Core brief, canon, and roadmap are in place.")
    if artifact_count and len(done) < 2:
        done.append(f"{artifact_count} packaged artifact{'s' if artifact_count != 1 else ''} available for review.")
    blocked_count = len(blocked)
    priority_score = _priority_score(
        status=record.status,
        blocked_count=blocked_count,
        activity_state=_activity_state(last_activity_iso),
        progress_percent=progress_percent,
        priority_override=record.priority_override,
    )
    control = {
        "project_kind": record.project_kind,
        "control_mode": record.control_mode,
        "delivery_target": record.delivery_target,
        "primary_artifact": record.primary_artifact,
        "acceptance": list(record.acceptance),
        "primary_lane": record.primary_lane,
        "lane_sequence": list(record.lane_sequence),
        "strict_dispatch": record.strict_dispatch,
        "capability_gaps": list(record.capability_gaps),
    }
    active_attempts = _active_attempt_summary(record)
    proof_rows = _proof_rows(
        record,
        recent_file_rows=recent_file_rows,
        primary_artifact=record.primary_artifact,
    )
    focused_slice = (
        record.delivery_target.strip()
        or now_value
        or record.primary_artifact.strip()
        or record.summary.strip()
        or record.title
    )
    project_context = {
        "project_id": record.project_id,
        "title": record.title,
        "summary": record.summary,
        "specialists": list(record.specialists),
        "control": control,
    }
    portfolio = _portfolio_view_for_project(
        record.project_id,
        portfolio_state_payload or _default_portfolio_state(),
        discovered_rank=discovered_rank,
    )
    return {
        "project_id": record.project_id,
        "title": record.title,
        "summary": record.summary,
        "status": record.status,
        "specialists": list(record.specialists),
        "owner": owner,
        "now": now_value,
        "next": next_value,
        "blocked": blocked,
        "blocked_count": blocked_count,
        "done": done,
        "done_count": len(done),
        "root": str(record.root),
        "created_at": record.created_at,
        "updated_at": last_activity_iso,
        "manifest_updated_at": record.updated_at,
        "documents": documents,
        "docs_ready_count": docs_ready,
        "artifact_count": artifact_count,
        "run_count": run_count,
        "dispatch_count": dispatch_count,
        "track_file_counts": track_file_counts,
        "track_ready_count": sum(1 for count in track_file_counts.values() if count),
        "total_track_files": total_track_files,
        "progress_stage": _progress_stage(
            docs_ready=docs_ready,
            total_track_files=total_track_files,
            artifact_count=artifact_count,
            run_count=run_count,
        ),
        "progress_percent": progress_percent,
        "priority_score": priority_score,
        "last_activity_at": last_activity_iso,
        "activity_state": _activity_state(last_activity_iso),
        "recent_files": recent_file_rows,
        "focused_slice": focused_slice,
        "proof": proof_rows,
        "proof_count": len(proof_rows),
        "attempts": active_attempts,
        "loop_risk": active_attempts["loop_risk"],
        "delivery_model": build_delivery_model(
            profile_key="operator",
            project=project_context,
            objective=f"{record.title} {record.summary}".strip(),
        ),
        "tracking": {
            "owner": owner,
            "now": now_value,
            "next": next_value,
            "blocked": blocked,
            "done": done,
            "percent": progress_percent,
            "priority": priority_score,
        },
        "control": control,
        "slice": {
            "label": focused_slice,
            "owner_lane": record.primary_lane or owner,
            "delivery_target": record.delivery_target,
            "primary_artifact": record.primary_artifact,
            "acceptance": list(record.acceptance),
            "evidence_required": "Artifact plus proof plus truthful project-state convergence.",
            "active_attempts": active_attempts["active_attempts"],
            "retry_count": active_attempts["retry_count"],
            "loop_risk": active_attempts["loop_risk"],
        },
        "portfolio": portfolio,
    }


def _build_project_readme(title: str, summary: str, specialists: tuple[str, ...]) -> str:
    specialist_text = "\n".join(f"- `{item}`" for item in specialists) or "- Assign specialists as the project sharpens."
    body = summary.strip() or "Persistent Hermes project workspace for multi-specialist delivery."
    return f"""# {title}

{body}

## Specialists

{specialist_text}

## Project Layout

- `brief.md` for the working brief and outcomes
- `canon.md` for stable rules, tone, and continuity
- `roadmap.md` for milestones and sequencing
- `app/` for application-facing artifacts
- `game/` for gameplay, systems, and build work
- `creative/` for story, image, video, and publishing assets
- `artifacts/` for packaged outputs
- `runs/` for structured run summaries
"""


def _build_brief(title: str, summary: str) -> str:
    lead = summary.strip() or "Capture the outcome this project should deliver."
    return f"""# {title} Brief

{lead}

## Goal

- Define the real outcome this project should produce.

## Audience

- Note who this project is for.

## Deliverables

- List the app, game, creative, publishing, or media artifacts that matter.

## Success Signals

- Define what done looks like in concrete terms.
"""


def _build_canon(title: str) -> str:
    return f"""# {title} Canon

Use this file for the rules that should stay stable across runs.

## Non-Negotiables

- Record any hard constraints, continuity rules, or brand truths here.

## Product And World Rules

- Capture systems, story logic, or UX principles that should not drift.

## Voice And Visual Direction

- Keep the tone, style, and aesthetic guardrails visible.
"""


def _build_roadmap(title: str) -> str:
    return f"""# {title} Roadmap

## Now

- Define the current milestone.

## Next

- List the next concrete delivery slice.

## Later

- Capture longer-range work without losing the near-term focus.
"""


def create_project(
    root_dir: str | Path | None,
    *,
    project_id: str,
    title: str,
    summary: str = "",
    specialists: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    root = repo_root(root_dir)
    normalized_id = project_id.strip().lower()
    if not PROJECT_ID_PATTERN.match(normalized_id):
        raise ValueError(
            "project_id must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens"
        )
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValueError("title is required")

    normalized_specialists = _normalize_specialists(specialists)
    project_root = project_dir(root, normalized_id)
    project_entry = load_project_entry(root, normalized_id)
    if project_entry is not None:
        raise FileExistsError(f"Project already exists: {normalized_id}")

    timestamp = _now()
    payload = {
        "project_id": normalized_id,
        "title": cleaned_title,
        "summary": summary.strip(),
        "status": "active",
        "specialists": list(normalized_specialists),
        "tracking": {
            "owner": normalized_specialists[0] if normalized_specialists else "operator",
            "now": "",
            "next": "",
            "blocked": [],
            "done": [],
            "priority": 50,
        },
        "control": _default_control(cleaned_title, summary.strip(), normalized_specialists),
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    for path in (
        projects_dir(root),
        project_root,
        project_root / "artifacts",
        project_root / "runs",
        *(project_root / track for track in TRACK_NAMES),
    ):
        path.mkdir(parents=True, exist_ok=True)

    _write_if_missing(project_root / "README.md", _build_project_readme(cleaned_title, summary, normalized_specialists))
    _write_if_missing(project_root / "brief.md", _build_brief(cleaned_title, summary))
    _write_if_missing(project_root / "canon.md", _build_canon(cleaned_title))
    _write_if_missing(project_root / "roadmap.md", _build_roadmap(cleaned_title))
    save_project_payload(root, project_root, payload)
    activate_project(root, project_id=normalized_id, reason="Project created")
    return _record_snapshot(_load_record(project_root, payload), portfolio_state_payload=ensure_portfolio(root))


def update_project(
    root_dir: str | Path | None,
    *,
    project_id: str,
    title: str | None = None,
    summary: str | None = None,
    status: str | None = None,
    specialists: tuple[str, ...] | list[str] | None = None,
    owner: str | None = None,
    now: str | None = None,
    next_value: str | None = None,
    blocked: tuple[str, ...] | list[str] | None = None,
    done: tuple[str, ...] | list[str] | None = None,
    percent: int | None = None,
    priority: int | None = None,
    project_kind: str | None = None,
    control_mode: str | None = None,
    delivery_target: str | None = None,
    primary_artifact: str | None = None,
    acceptance: tuple[str, ...] | list[str] | None = None,
    primary_lane: str | None = None,
    lane_sequence: tuple[str, ...] | list[str] | None = None,
    strict_dispatch: bool | None = None,
    capability_gaps: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    root = repo_root(root_dir)
    normalized_id = project_id.strip().lower()
    if not PROJECT_ID_PATTERN.match(normalized_id):
        raise ValueError(
            "project_id must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens"
        )

    project_entry = load_project_entry(root, normalized_id)
    if project_entry is None:
        raise FileNotFoundError(f"Project does not exist: {normalized_id}")
    project_root, payload = project_entry
    tracking = payload.get("tracking")
    if not isinstance(tracking, dict):
        tracking = {}
        payload["tracking"] = tracking
    control = payload.get("control")
    if not isinstance(control, dict):
        control = _default_control(
            str(payload.get("title") or ""),
            str(payload.get("summary") or ""),
            _normalize_specialists(tuple(str(item) for item in payload.get("specialists", []))),
        )
        payload["control"] = control

    if title is not None:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("title cannot be empty")
        payload["title"] = cleaned_title
    if summary is not None:
        payload["summary"] = summary.strip()
    if status is not None:
        payload["status"] = status.strip() or "active"
    if specialists is not None:
        payload["specialists"] = list(_normalize_specialists(specialists))
    if owner is not None:
        tracking["owner"] = owner.strip()
    if now is not None:
        tracking["now"] = _sanitize_tracking_value(now)
    if next_value is not None:
        tracking["next"] = _sanitize_tracking_value(next_value)
    if blocked is not None:
        tracking["blocked"] = list(_sanitize_tracking_items(list(_normalize_text_list(blocked))))
    if done is not None:
        tracking["done"] = list(_sanitize_tracking_items(list(_normalize_text_list(done))))
    if percent is not None:
        tracking["percent"] = max(0, min(100, int(percent)))
    if priority is not None:
        tracking["priority"] = max(0, min(100, int(priority)))

    specialists_tuple = _normalize_specialists(tuple(str(item) for item in payload.get("specialists", [])))
    if project_kind is not None:
        control["project_kind"] = project_kind.strip() or _infer_project_kind(
            str(payload.get("title") or ""),
            str(payload.get("summary") or ""),
            specialists_tuple,
        )
    if control_mode is not None:
        control["control_mode"] = control_mode.strip() or "orchestrated"
    if delivery_target is not None:
        control["delivery_target"] = delivery_target.strip()
    if primary_artifact is not None:
        control["primary_artifact"] = primary_artifact.strip()
    if acceptance is not None:
        control["acceptance"] = list(_normalize_text_list(acceptance))
    if lane_sequence is not None:
        control["lane_sequence"] = list(_normalize_lane_sequence(lane_sequence, specialists=specialists_tuple))
    if primary_lane is not None:
        normalized_primary_lane = primary_lane.strip()
        if normalized_primary_lane and normalized_primary_lane not in VALID_LANES:
            raise ValueError(f"primary_lane must be one of: {', '.join(VALID_LANES)}")
        control["primary_lane"] = normalized_primary_lane or _default_primary_lane(specialists_tuple)
    if strict_dispatch is not None:
        control["strict_dispatch"] = bool(strict_dispatch)
    if capability_gaps is not None:
        control["capability_gaps"] = list(_normalize_text_list(capability_gaps))

    if not str(control.get("project_kind") or "").strip():
        control["project_kind"] = _infer_project_kind(
            str(payload.get("title") or ""),
            str(payload.get("summary") or ""),
            specialists_tuple,
        )
    if not str(control.get("control_mode") or "").strip():
        control["control_mode"] = "orchestrated"
    normalized_lane_sequence = _normalize_lane_sequence(control.get("lane_sequence"), specialists=specialists_tuple)
    control["lane_sequence"] = list(normalized_lane_sequence)
    normalized_primary_lane = str(control.get("primary_lane") or "").strip()
    if normalized_primary_lane not in VALID_LANES:
        control["primary_lane"] = _default_primary_lane(normalized_lane_sequence or specialists_tuple)

    payload["updated_at"] = _now()
    save_project_payload(root, project_root, payload)

    if str(payload.get("status") or "").strip().lower() == "archived":
        archive_payload = ensure_portfolio(root)
        queue_rows = archive_payload.get("project_queue")
        if isinstance(queue_rows, list):
            queue_rows[:] = [row for row in queue_rows if str(row.get("project_id") or "") != normalized_id]
            if str(archive_payload.get("active_project_id") or "") == normalized_id:
                archive_payload["active_project_id"] = str(queue_rows[0].get("project_id") or "") if queue_rows else ""
            archive_payload["project_queue"] = queue_rows
            archive_payload["updated_at"] = _now()
            _save_portfolio_state(root, archive_payload)
    else:
        ensure_portfolio(root)

    return _record_snapshot(_load_record(project_root, payload), portfolio_state_payload=ensure_portfolio(root))


def discover_projects(root_dir: str | Path | None = None) -> list[dict[str, Any]]:
    root = projects_dir(root_dir)
    if not root.exists() and not list_project_entries(root_dir):
        return []
    portfolio = ensure_portfolio(root_dir)
    portfolio_positions = {
        str(row.get("project_id") or ""): index
        for index, row in enumerate(portfolio.get("project_queue") or [], start=1)
        if isinstance(row, dict)
    }
    rows: list[dict[str, Any]] = []
    for project_root, payload in list_project_entries(root_dir):
        record = _load_record(project_root, payload)
        rows.append(
            _record_snapshot(
                record,
                portfolio_state_payload=portfolio,
                discovered_rank=portfolio_positions.get(record.project_id, 0),
            )
        )
    rows.sort(
        key=lambda row: (
            0 if bool(((row.get("portfolio") or {}).get("active"))) else 1,
            int(((row.get("portfolio") or {}).get("queue_position")) or 9999),
            -int(row.get("priority_score") or 0),
            str(row.get("last_activity_at") or row.get("updated_at") or ""),
        ),
    )
    for index, row in enumerate(rows, start=1):
        row["queue_rank"] = index
        tracking = row.get("tracking")
        if isinstance(tracking, dict):
            tracking["queue_rank"] = index
        portfolio_view = row.get("portfolio")
        if isinstance(portfolio_view, dict) and not portfolio_view.get("queue_position"):
            portfolio_view["queue_position"] = index
    return rows
