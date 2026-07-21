"""Mission-mode helpers for project-aware Sheldon surfaces."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from hermes_stack.always_on import run_always_on_cycle
from hermes_stack.projects import discover_projects
from hermes_stack.scaffold import hermes_state_dir
from hermes_stack.state_store import repo_root, upsert_cognitive_record


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


def _truth_loop_dir(root_dir: str | Path | None = None) -> Path:
    path = _mission_dir(root_dir) / "truth_loop"
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


def _improvement_path(root_dir: str | Path | None, proposal_id: str) -> Path:
    return _improvement_dir(root_dir) / f"{str(proposal_id or '').replace(':', '_')}.json"


def _truth_receipt_path(root_dir: str | Path | None, receipt_id: str) -> Path:
    return _truth_loop_dir(root_dir) / f"{str(receipt_id or '').replace(':', '_')}.json"


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


def score_mission_card(card: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "objective": bool(str(card.get("objective") or "").strip()),
        "now": bool(str(card.get("now") or "").strip()) and str(card.get("now") or "").strip() != "No current milestone recorded.",
        "next": bool(str(card.get("next") or "").strip()) and str(card.get("next") or "").strip() != "Choose the next concrete proof step.",
        "proof": bool(card.get("proof") or card.get("receipts")),
        "unblocked": not bool(card.get("blocked")),
    }
    score = round(sum(1 for value in checks.values() if value) / len(checks), 2)
    missing = [name for name, ok in checks.items() if not ok]
    if "unblocked" in missing:
        recommendation = "Resolve or route the current blocker before adding more work."
    elif "proof" in missing:
        recommendation = "Capture one receipt so the next move has memory."
    elif missing:
        recommendation = f"Clarify {missing[0]} so the mission card can drive action."
    else:
        recommendation = "Healthy card. Look for automation or packaging gains."
    return {
        "project_id": card.get("project_id") or "",
        "title": card.get("title") or "",
        "score": score,
        "checks": checks,
        "missing": missing,
        "recommendation": recommendation,
    }


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
    scores = [score_mission_card(card) for card in cards]
    blocked_count = sum(1 for card in cards if card.get("blocked"))
    low_proof = [card for card in cards if not card.get("proof")]
    weakest = sorted(scores, key=lambda row: float(row.get("score") or 0))[:3]
    proposal = {
        "proposal_id": f"improve:{_stable_id(focus, len(cards), blocked_count, _now())}",
        "created_at": _now(),
        "updated_at": _now(),
        "status": "proposed",
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
            "average_card_score": round(sum(float(row.get("score") or 0) for row in scores) / max(1, len(scores)), 2),
        },
        "weakest_cards": weakest,
        "next_experiment": {
            "name": "receipt pressure test",
            "operator_prompt": "Ask each active agent for the next receipt they can produce in under 30 minutes.",
            "success_signal": "Every active project has a concrete proof receipt or an explicit blocker.",
            "rollback": "Mark the proposal rejected and keep the existing mission state unchanged.",
        },
        "guardrails": [
            "Do not change project state without an explicit handoff or operator approval.",
            "Prefer observations and proposals over autonomous destructive edits.",
            "Every improvement needs a receipt or a rollback path.",
        ],
    }
    _write_json_file(_improvement_path(root_dir, proposal["proposal_id"]), proposal)
    return proposal


def list_self_improvement_proposals(root_dir: str | Path | None = None, *, limit: int = 12) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for path in _improvement_dir(root_dir).glob("improve_*.json"):
        proposal = _read_json_file(path)
        if proposal:
            proposals.append(proposal)
    proposals.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return proposals[: max(1, limit)]


def self_improvement_snapshot(root_dir: str | Path | None = None, *, limit: int = 12) -> dict[str, Any]:
    cards = mission_cards(root_dir)
    scores = [score_mission_card(card) for card in cards]
    proposals = list_self_improvement_proposals(root_dir, limit=limit)
    average_score = round(sum(float(row.get("score") or 0) for row in scores) / max(1, len(scores)), 2)
    weak_cards = sorted(scores, key=lambda row: float(row.get("score") or 0))[:5]
    return {
        "ok": True,
        "generated_at": _now(),
        "summary": f"Mission brain score is {int(average_score * 100)}%.",
        "average_score": average_score,
        "weak_cards": weak_cards,
        "proposals": proposals,
        "latest": proposals[0] if proposals else {},
        "next_move": (
            "Generate a proposal for the weakest mission card."
            if not proposals
            else "Accept, reject, or apply the latest proposal so the loop has feedback."
        ),
    }


def update_self_improvement_status(
    root_dir: str | Path | None,
    *,
    proposal_id: str,
    status: str,
    note: str = "",
) -> dict[str, Any]:
    clean_status = str(status or "").strip().lower()
    if clean_status not in {"proposed", "accepted", "applied", "rejected"}:
        raise ValueError("status must be proposed, accepted, applied, or rejected")
    path = _improvement_path(root_dir, proposal_id)
    proposal = _read_json_file(path)
    if not proposal:
        raise FileNotFoundError("Unknown proposal")
    event = {
        "at": _now(),
        "status": clean_status,
        "note": str(note or "").strip(),
    }
    events = proposal.get("events")
    if not isinstance(events, list):
        events = []
    events.append(event)
    proposal["status"] = clean_status
    proposal["updated_at"] = event["at"]
    proposal["events"] = events
    if event["note"]:
        proposal["last_note"] = event["note"]
    _write_json_file(path, proposal)
    return proposal


def list_truth_loop_receipts(root_dir: str | Path | None = None, *, limit: int = 12) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in _truth_loop_dir(root_dir).glob("truth_*.json"):
        receipt = _read_json_file(path)
        if receipt:
            receipts.append(receipt)
    receipts.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return receipts[: max(1, limit)]


def truth_loop_snapshot(root_dir: str | Path | None = None, *, limit: int = 12) -> dict[str, Any]:
    improvement = self_improvement_snapshot(root_dir, limit=limit)
    receipts = list_truth_loop_receipts(root_dir, limit=limit)
    latest = receipts[0] if receipts else {}
    return {
        "ok": True,
        "generated_at": _now(),
        "summary": (
            str(latest.get("summary") or "")
            if latest
            else "Truth Loop is wired and waiting for its first run."
        ),
        "latest": latest,
        "receipts": receipts,
        "self_improvement": improvement,
        "next_move": (
            "Run Truth Loop to refresh agent intentions and write a receipt."
            if not latest
            else "Run Truth Loop again after project state changes or before closure."
        ),
    }


def run_truth_loop(root_dir: str | Path | None = None, *, focus: str = "operator truth loop") -> dict[str, Any]:
    root = repo_root(root_dir)
    cycle = run_always_on_cycle(root)
    improvement_before = self_improvement_snapshot(root, limit=6)
    proposal = self_improvement_proposal(root, focus=focus or "operator truth loop")
    proposal = update_self_improvement_status(
        root,
        proposal_id=str(proposal.get("proposal_id") or ""),
        status="applied",
        note="Truth Loop applied as a non-destructive observation, routing, and receipt pass.",
    )
    improvement_after = self_improvement_snapshot(root, limit=6)

    active_project_id = str(cycle.get("active_project_id") or "")
    executions = cycle.get("executions") if isinstance(cycle.get("executions"), list) else []
    intentions = cycle.get("intentions") if isinstance(cycle.get("intentions"), list) else []
    completed_intentions = [row for row in intentions if str(row.get("status") or "") == "completed"]
    receipt_id = f"truth:{_stable_id(active_project_id, focus, _now())}"
    summary = (
        f"Truth Loop ran {len(intentions)} agent intention(s), "
        f"{len(completed_intentions)} completed decision(s), and {len(executions)} safe execution(s)."
    )
    receipt = {
        "receipt_id": receipt_id,
        "created_at": _now(),
        "updated_at": _now(),
        "status": "applied",
        "focus": focus or "operator truth loop",
        "summary": summary,
        "active_project_id": active_project_id,
        "agent_movement": [
            {
                "agent_slug": str(row.get("agent_slug") or ""),
                "title": str(row.get("title") or ""),
                "status": str(row.get("status") or ""),
                "decision": str(row.get("autonomy_decision") or ""),
                "work_result": (row.get("payload") or {}).get("work_result") if isinstance(row.get("payload"), dict) else {},
            }
            for row in intentions[:8]
        ],
        "executions": executions,
        "proposal": proposal,
        "score_before": improvement_before.get("average_score"),
        "score_after": improvement_after.get("average_score"),
        "guardrails": [
            "No paid provider calls.",
            "No destructive edits.",
            "Every run writes a durable receipt and cognitive event.",
        ],
    }
    _write_json_file(_truth_receipt_path(root, receipt_id), receipt)
    upsert_cognitive_record(
        root,
        "events",
        {
            "event_id": f"event:truth-loop:{_stable_id(receipt_id)}",
            "agent_slug": "sheldon",
            "project_id": active_project_id,
            "event_type": "truth_loop",
            "title": "Truth Loop wrote an operator receipt",
            "content": summary,
            "source_ref": f"mission_control/truth_loop/{receipt_id.replace(':', '_')}.json",
            "salience": 0.86,
            "occurred_at": _now(),
            "payload": receipt,
        },
    )
    return {
        "ok": True,
        "receipt": receipt,
        "cycle": cycle,
        "self_improvement": improvement_after,
        "snapshot": truth_loop_snapshot(root, limit=12),
    }
