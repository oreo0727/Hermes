"""Mission-mode helpers for project-aware Sheldon surfaces."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from hermes_stack.projects import discover_projects
from hermes_stack.scaffold import hermes_state_dir


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(part or "").strip() for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _as_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _tracking(project: dict[str, Any]) -> dict[str, Any]:
    value = project.get("tracking")
    return value if isinstance(value, dict) else {}


def _delivery(project: dict[str, Any]) -> dict[str, Any]:
    value = project.get("delivery_model")
    return value if isinstance(value, dict) else {}


def _mission_dir(root_dir: str | Path | None = None) -> Path:
    path = hermes_state_dir(root_dir) / "mission_control"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _handoff_dir(root_dir: str | Path | None = None) -> Path:
    path = _mission_dir(root_dir) / "handoffs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _improvement_dir(root_dir: str | Path | None = None) -> Path:
    path = _mission_dir(root_dir) / "self_improvement"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json_file(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _handoff_path(root_dir: str | Path | None, handoff_id: str) -> Path:
    return _handoff_dir(root_dir) / f"{str(handoff_id or '').replace(':', '_')}.json"


def mission_card(project: dict[str, Any]) -> dict[str, Any]:
    tracking = _tracking(project)
    delivery = _delivery(project)
    blocked = _as_list(project.get("blocked") or tracking.get("blocked"))
    proof = _as_list(project.get("proof"))
    done = _as_list(project.get("done"))
    receipts = []
    for row in proof[:4]:
        receipts.append(row if isinstance(row, str) else str(row))
    receipts.extend(done[: max(0, 4 - len(receipts))])

    project_id = str(project.get("project_id") or "").strip()
    title = str(project.get("title") or project_id or "Untitled project").strip()
    now = str(project.get("now") or tracking.get("now") or "No current milestone recorded.").strip()
    next_move = str(project.get("next") or tracking.get("next") or "Choose the next concrete proof step.").strip()
    objective = str(
        project.get("focused_slice")
        or delivery.get("delivery_target")
        or project.get("summary")
        or "Keep this project moving with visible proof."
    ).strip()

    return {
        "project_id": project_id,
        "title": title,
        "status": project.get("status") or "tracked",
        "objective": objective,
        "now": now,
        "next": next_move,
        "blocked": blocked,
        "proof": receipts,
        "owner": tracking.get("owner") or delivery.get("active_lane") or project.get("owner") or "operator",
        "progress_percent": project.get("progress_percent") or tracking.get("percent") or 0,
        "priority_score": project.get("priority_score") or tracking.get("priority") or 0,
        "active": bool((project.get("portfolio") or {}).get("active")),
        "loop_risk": project.get("loop_risk") or ((project.get("attempts") or {}).get("loop_risk")) or "unknown",
        "updated_at": project.get("updated_at") or project.get("last_activity_at") or "",
        "receipts": _receipt_chips(project, receipts),
    }


def _receipt_chips(project: dict[str, Any], fallback: list[str]) -> list[dict[str, str]]:
    chips: list[dict[str, str]] = []
    for row in project.get("proof") or []:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "").strip()
        if path:
            chips.append(
                {
                    "label": str(row.get("source") or "proof"),
                    "path": path,
                    "updated_at": str(row.get("updated_at") or ""),
                }
            )
    if not chips:
        for item in fallback[:3]:
            chips.append({"label": "proof", "path": item, "updated_at": ""})
    return chips[:5]


def mission_cards(root_dir: str | Path | None = None) -> list[dict[str, Any]]:
    cards = [mission_card(project) for project in discover_projects(root_dir)]
    return sorted(cards, key=lambda row: (not bool(row.get("active")), -int(row.get("priority_score") or 0), str(row.get("title") or "")))


def find_mission_card(root_dir: str | Path | None, project_id: str) -> dict[str, Any] | None:
    normalized = str(project_id or "").strip()
    if not normalized:
        cards = mission_cards(root_dir)
        return cards[0] if cards else None
    return next((card for card in mission_cards(root_dir) if card.get("project_id") == normalized), None)


def build_briefing(root_dir: str | Path | None, project_id: str, *, depth: str = "short", mode: str = "normal") -> dict[str, Any]:
    card = find_mission_card(root_dir, project_id)
    if not card:
        return {
            "ok": False,
            "error": "Unknown project",
            "briefing": "I could not find that project.",
            "card": {},
            "receipts": [],
        }

    blocked = list(card.get("blocked") or [])
    receipts = list(card.get("receipts") or [])
    car_mode = mode == "car"
    lines = [
        f"{card['title']}.",
        f"Now: {card['now']}",
        f"Next: {card['next']}",
    ]
    if blocked:
        lines.append(f"Blocked: {blocked[0]}")
    else:
        lines.append("Blocked: none recorded.")
    if not car_mode and depth in {"medium", "deep"}:
        lines.append(f"Objective: {card['objective']}")
        lines.append(f"Owner: {card['owner']}. Progress: {card['progress_percent']}%.")
    if not car_mode and depth == "deep" and receipts:
        lines.append("Receipts: " + "; ".join(str(item.get("path") or "") for item in receipts[:3]))
    return {
        "ok": True,
        "project_id": card["project_id"],
        "mode": mode,
        "depth": depth,
        "briefing": "\n".join(lines),
        "card": card,
        "receipts": receipts,
    }


def watch_digest(root_dir: str | Path | None = None, *, limit: int = 6) -> dict[str, Any]:
    cards = mission_cards(root_dir)
    handoffs = list_handoffs(root_dir, limit=12)
    open_handoffs = [row for row in handoffs if str(row.get("status") or "") in {"queued", "working", "blocked"}]
    alerts: list[dict[str, Any]] = []
    for card in cards:
        if card.get("blocked"):
            alerts.append({"tone": "blocked", "project_id": card["project_id"], "title": card["title"], "message": str(card["blocked"][0])})
        elif card.get("active"):
            alerts.append({"tone": "active", "project_id": card["project_id"], "title": card["title"], "message": str(card["next"])})
        elif int(card.get("progress_percent") or 0) >= 70:
            alerts.append({"tone": "proof", "project_id": card["project_id"], "title": card["title"], "message": "Close to packaging; verify proof and finish the handoff."})
    for handoff in open_handoffs[: max(0, limit - len(alerts))]:
        alerts.append(
            {
                "tone": "handoff",
                "project_id": handoff.get("project_id") or "",
                "title": f"{handoff.get('target', 'agent').title()} handoff",
                "message": handoff.get("instruction") or "Queued specialist work needs a status update.",
                "handoff_id": handoff.get("handoff_id") or "",
            }
        )
    return {
        "ok": True,
        "generated_at": _now(),
        "summary": "Nothing urgent." if not alerts else f"{len(alerts[:limit])} mission signal(s) need attention.",
        "alerts": alerts[:limit],
        "handoffs": open_handoffs[:limit],
    }


def list_handoffs(
    root_dir: str | Path | None = None,
    *,
    project_id: str = "",
    status: str = "",
    limit: int = 24,
) -> list[dict[str, Any]]:
    handoffs: list[dict[str, Any]] = []
    normalized_project_id = str(project_id or "").strip()
    normalized_status = str(status or "").strip().lower()
    for path in _handoff_dir(root_dir).glob("handoff_*.json"):
        handoff = _read_json_file(path)
        if not handoff:
            continue
        if normalized_project_id and handoff.get("project_id") != normalized_project_id:
            continue
        if normalized_status and str(handoff.get("status") or "").lower() != normalized_status:
            continue
        handoffs.append(handoff)
    handoffs.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return handoffs[: max(1, limit)]


def create_handoff(
    root_dir: str | Path | None,
    *,
    project_id: str,
    target: str,
    instruction: str,
    source: str = "sheldon",
) -> dict[str, Any]:
    card = find_mission_card(root_dir, project_id)
    if not card:
        raise FileNotFoundError("Unknown project")
    clean_target = str(target or "").strip() or "sheldon"
    clean_instruction = str(instruction or "").strip()
    if not clean_instruction:
        clean_instruction = f"Review {card['title']} and report the next useful proof step."
    handoff = {
        "handoff_id": f"handoff:{_stable_id(card['project_id'], clean_target, clean_instruction, _now())}",
        "project_id": card["project_id"],
        "project_title": card["title"],
        "target": clean_target,
        "instruction": clean_instruction,
        "source": source,
        "status": "queued",
        "created_at": _now(),
        "updated_at": _now(),
        "mission_card": card,
        "events": [
            {
                "at": _now(),
                "status": "queued",
                "note": "Handoff queued from mission control.",
            }
        ],
    }
    _write_json_file(_handoff_path(root_dir, handoff["handoff_id"]), handoff)
    return handoff


def update_handoff_status(
    root_dir: str | Path | None,
    *,
    handoff_id: str,
    status: str,
    note: str = "",
) -> dict[str, Any]:
    clean_status = str(status or "").strip().lower()
    if clean_status not in {"queued", "working", "blocked", "done", "cancelled"}:
        raise ValueError("status must be queued, working, blocked, done, or cancelled")
    path = _handoff_path(root_dir, handoff_id)
    handoff = _read_json_file(path)
    if not handoff:
        raise FileNotFoundError("Unknown handoff")
    event = {
        "at": _now(),
        "status": clean_status,
        "note": str(note or "").strip(),
    }
    events = handoff.get("events")
    if not isinstance(events, list):
        events = []
    events.append(event)
    handoff["status"] = clean_status
    handoff["updated_at"] = event["at"]
    handoff["events"] = events
    if event["note"]:
        handoff["last_note"] = event["note"]
    _write_json_file(path, handoff)
    return handoff


def self_improvement_proposal(root_dir: str | Path | None, *, focus: str = "") -> dict[str, Any]:
    cards = mission_cards(root_dir)
    blocked_count = sum(1 for card in cards if card.get("blocked"))
    low_proof = [card for card in cards if not card.get("proof")]
    proposal = {
        "proposal_id": f"improve:{_stable_id(focus, len(cards), blocked_count, _now())}",
        "created_at": _now(),
        "focus": focus or "mission reliability",
        "hypothesis": "Sheldon improves fastest by comparing promised next moves against proof receipts and reducing repeat blockers.",
        "experiments": [
            "Score each mission card for objective/now/next/proof completeness.",
            "Flag projects where the next move repeats without a new receipt.",
            "Ask the owning agent for one narrow improvement when proof is missing.",
        ],
        "signals": {
            "project_count": len(cards),
            "blocked_count": blocked_count,
            "missing_proof_count": len(low_proof),
        },
        "guardrails": [
            "Do not change project state without an explicit handoff or operator approval.",
            "Prefer observations and proposals over autonomous destructive edits.",
            "Every improvement needs a receipt or a rollback path.",
        ],
    }
    path = _improvement_dir(root_dir) / f"{proposal['proposal_id'].replace(':', '_')}.json"
    path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    return proposal
