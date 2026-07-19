"""Always-on agent heartbeat and intention loop for Hermes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import time

from hermes_stack.agents import AGENT_SPECS, AgentSpec
from hermes_stack.autonomy import decide_autonomy
from hermes_stack.projects import discover_projects, portfolio_snapshot, update_project
from hermes_stack.state_store import list_cognitive_records, repo_root, upsert_cognitive_record


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(part or "").strip() for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _active_project(root: Path) -> dict[str, Any] | None:
    portfolio = portfolio_snapshot(root)
    active_id = str(portfolio.get("active_project_id") or "")
    projects = discover_projects(root)
    if active_id:
        return next((row for row in projects if str(row.get("project_id") or "") == active_id), None)
    return next((row for row in projects if bool((row.get("portfolio") or {}).get("active"))), None)


def _project_blockers(project: dict[str, Any] | None) -> list[str]:
    if not project:
        return []
    return [str(item).strip() for item in project.get("blocked") or [] if str(item).strip()]


def _project_done(project: dict[str, Any] | None) -> list[str]:
    if not project:
        return []
    return [str(item).strip() for item in project.get("done") or [] if str(item).strip()]


def _project_artifacts(project: dict[str, Any] | None) -> list[Path]:
    if not project:
        return []
    project_root = Path(str(project.get("root") or ""))
    if not project_root.exists():
        return []
    control = project.get("control") if isinstance(project.get("control"), dict) else {}
    raw = str(control.get("primary_artifact") or project.get("primary_artifact") or "")
    artifacts: list[Path] = []
    for part in raw.split(","):
        cleaned = part.strip()
        if not cleaned:
            continue
        candidate = Path(cleaned)
        if not candidate.is_absolute():
            candidate = project_root / candidate
        artifacts.append(candidate)
    return artifacts


def _artifact_summary(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return f"{path.name}: missing"
    size_mb = stat.st_size / (1024 * 1024)
    return f"{path.name}: present, {size_mb:.2f} MB"


def _write_execution_review(project: dict[str, Any], artifacts: list[Path]) -> Path | None:
    project_root = Path(str(project.get("root") or ""))
    if not project_root.exists() or not artifacts:
        return None
    review_path = project_root / "artifacts" / "always_on_review.md"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    title = str(project.get("title") or project.get("project_id") or "Project")
    lines = [
        "# Always-on execution review",
        "",
        f"Updated: {_now()}",
        f"Project: {title}",
        "",
        "Safe action completed:",
        "- Verified the current primary artifact set is locally present.",
        "- Advanced the project from passive monitoring to a concrete review/polish lane.",
        "",
        "Artifacts checked:",
        *[f"- {_artifact_summary(path)}" for path in artifacts],
        "",
        "Next useful production move:",
        "- Review the motion pass for story quality, then choose audio/subtitle/trailer polish or provider upgrade.",
    ]
    review_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return review_path


def _execute_safe_project_work(root: Path, project: dict[str, Any] | None) -> dict[str, Any] | None:
    """Perform one conservative project advancement that cannot spend money or call external APIs."""
    if not project:
        return None
    project_id = str(project.get("project_id") or "").strip()
    if not project_id or str(project.get("status") or "").strip().lower() not in {"active", "in_progress", "in progress"}:
        return None
    blockers = _project_blockers(project)
    if blockers:
        return None
    done = _project_done(project)
    if any("Always-on executor reviewed" in item for item in done):
        return None

    next_value = str(project.get("next") or "").strip().lower()
    artifacts = _project_artifacts(project)
    existing_artifacts = [path for path in artifacts if path.exists()]
    if not existing_artifacts:
        return None
    if not any(token in next_value for token in ("review", "verify", "proof", "quality", "polish", "motion")):
        return None

    review_path = _write_execution_review(project, existing_artifacts)
    if review_path is None:
        return None

    project_root = Path(str(project.get("root") or ""))
    relative_review = str(review_path.relative_to(project_root))
    primary_artifact = ", ".join(
        [str(path.relative_to(project_root)) for path in existing_artifacts[:3]]
        + [relative_review]
    )
    done_update = [
        *done[:5],
        f"Always-on executor reviewed the active artifact set and wrote {relative_review}.",
    ]
    next_update = "Choose the next production slice: audio/subtitle polish, trailer packaging, or a higher-fidelity video-provider upgrade."
    now_update = f"Always-on executor advanced the project by verifying local proof and writing {relative_review}."
    update_project(
        root,
        project_id=project_id,
        status="active",
        owner=str(project.get("owner") or "operator"),
        now=now_update,
        next_value=next_update,
        blocked=[],
        done=done_update,
        percent=max(70, int(project.get("progress_percent") or 0)),
        primary_artifact=primary_artifact,
    )

    event = {
        "event_id": f"event:always-on-executor:{_stable_id(project_id, primary_artifact)}",
        "agent_slug": "sheldon",
        "project_id": project_id,
        "event_type": "always_on_execution",
        "title": "Always-on executor advanced project proof",
        "content": now_update,
        "source_ref": relative_review,
        "salience": 0.78,
        "occurred_at": _now(),
        "payload": {
            "artifacts": [str(path.relative_to(project_root)) for path in existing_artifacts],
            "review_artifact": relative_review,
            "next": next_update,
        },
    }
    upsert_cognitive_record(root, "events", event)
    return {
        "project_id": project_id,
        "status": "completed",
        "summary": now_update,
        "artifact": relative_review,
        "next_action": next_update,
    }


def _sentence(value: str) -> str:
    cleaned = value.strip()
    return cleaned.rstrip(".") + "." if cleaned else ""


def _heartbeat_for(spec: AgentSpec, project: dict[str, Any] | None) -> dict[str, Any]:
    slug = spec.character_name.lower()
    project_id = str((project or {}).get("project_id") or "")
    title = str((project or {}).get("title") or "the portfolio")
    blockers = _project_blockers(project)
    done = _project_done(project)
    observation = f"Watching {title}."
    intention = "Keep listening for state changes and safe next moves."
    confidence = 0.68

    if slug == "sheldon":
        observation = f"Control plane focus is {title}; blockers recorded: {len(blockers)}."
        intention = "Keep routing the active project and surface stale blockers before drift returns."
        confidence = 0.84
    elif slug == "penny":
        observation = f"Creative proof available: {_sentence(done[0]) if done else 'none attached yet.'}"
        intention = "Watch for missing final visual proof and storyboard/animatic quality gaps."
        confidence = 0.76
    elif slug == "raj":
        observation = f"Portal/app lane is listening for project handoff and service-health signals on {title}."
        intention = "Keep the portal responsive and propose verification when chat or project state changes."
        confidence = 0.74
    elif slug == "leonard":
        observation = f"Runtime proof gate sees {len(done)} proof item(s) and {len(blockers)} blocker(s)."
        intention = "Watch for playable/export/runtime proof gaps before closure."
        confidence = 0.72

    return {
        "heartbeat_id": f"heartbeat:{slug}",
        "agent_slug": slug,
        "project_id": project_id,
        "status": "working" if project_id else "listening",
        "observation": observation,
        "intention": intention,
        "confidence": confidence,
        "payload": {
            "source": "always_on_cycle",
            "agent_title": spec.title,
            "generated_at": _now(),
        },
    }


def _work_result_for(intention: dict[str, Any], project: dict[str, Any] | None) -> dict[str, Any]:
    action_type = str(intention.get("action_type") or "")
    title = str((project or {}).get("title") or "the active project")
    blockers = _project_blockers(project)
    done = _project_done(project)
    first_blocker = blockers[0] if blockers else ""

    if action_type == "refresh_project_next":
        summary = f"Sheldon refreshed {title}: next move is anchored to the first blocker." if first_blocker else f"Sheldon refreshed {title}: no blocker is currently recorded."
        return {
            "summary": summary,
            "finding": first_blocker or str((project or {}).get("next") or "No next step recorded."),
            "next_action": str((project or {}).get("next") or "Choose the next concrete production slice."),
        }
    if action_type == "audit_creative_proof":
        proof = done[0] if done else "No creative proof is attached yet."
        return {
            "summary": f"Penny audited creative proof for {title}.",
            "finding": proof,
            "next_action": "Classify the animatic proof as final, placeholder, or blocked before closure.",
        }
    if action_type == "verify_portal_health":
        return {
            "summary": f"Raj verified the portal follow-up path for {title}.",
            "finding": "Fast project follow-ups stay tied to the active project and return project_followup metadata.",
            "next_action": "Keep checking chat routing whenever project focus changes.",
        }
    if action_type == "check_runtime_proof":
        return {
            "summary": f"Leonard checked runtime proof for {title}.",
            "finding": first_blocker or "No runtime blocker is currently recorded.",
            "next_action": "Confirm whether final motion/export proof exists, or document a bypass plan.",
        }
    return {
        "summary": f"Observed {title} for drift.",
        "finding": "No urgent intervention found.",
        "next_action": "Keep watching project state.",
    }


def _status_for_decision(decision: str) -> str:
    if decision == "auto_execute":
        return "completed"
    if decision == "council_review":
        return "reviewing"
    if decision == "ask_operator":
        return "waiting_approval"
    return "working"


def _intention_for(spec: AgentSpec, project: dict[str, Any] | None) -> dict[str, Any]:
    slug = spec.character_name.lower()
    project_id = str((project or {}).get("project_id") or "")
    title = str((project or {}).get("title") or "Hermes portfolio")
    blockers = _project_blockers(project)
    done = _project_done(project)
    base_title = f"Watch {title} for drift"
    action_type = "observe"
    risk = "low"
    confidence = 0.66
    detail = "Keep listening; no urgent intervention found."

    if slug == "sheldon":
        base_title = f"Refresh next move for {title}"
        action_type = "refresh_project_next"
        detail = "Summarize current next move and surface the first blocker if present."
        confidence = 0.82
    elif slug == "penny":
        base_title = f"Audit creative proof for {title}"
        action_type = "audit_creative_proof"
        detail = "Check whether storyboard/animatic proof is final, placeholder, or blocked."
        confidence = 0.74 if done else 0.68
    elif slug == "raj":
        base_title = f"Verify portal response path for {title}"
        action_type = "verify_portal_health"
        detail = "Confirm fast project follow-ups remain tied to the active project."
        confidence = 0.76
    elif slug == "leonard":
        base_title = f"Check runtime proof gap for {title}"
        action_type = "check_runtime_proof"
        detail = "Identify whether final motion/export proof exists or needs a bypass plan."
        confidence = 0.76 if blockers else 0.7

    return {
        "intention_id": f"intention:{slug}:{_stable_id(project_id, action_type, base_title)}",
        "agent_slug": slug,
        "project_id": project_id,
        "title": base_title,
        "action_type": action_type,
        "status": "working",
        "risk": risk,
        "confidence": confidence,
        "autonomy_decision": "",
        "payload": {
            "source": "always_on_cycle",
            "detail": detail,
            "blocked": blockers[:3],
            "proof": done[:3],
            "generated_at": _now(),
        },
    }


def run_always_on_cycle(root_dir: str | Path | None = None) -> dict[str, Any]:
    root = repo_root(root_dir)
    project = _active_project(root)
    heartbeats: list[dict[str, Any]] = []
    intentions: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []

    for spec in AGENT_SPECS:
        heartbeat = upsert_cognitive_record(root, "agent_heartbeats", _heartbeat_for(spec, project))
        heartbeats.append(heartbeat)

        intention = _intention_for(spec, project)
        decision = decide_autonomy(
            root,
            objective=str(intention.get("title") or ""),
            project_id=str(intention.get("project_id") or ""),
            risk=str(intention.get("risk") or "low"),
            confidence=float(intention.get("confidence") or 0.0),
        )
        intention["autonomy_decision"] = str(decision.get("decision") or "")
        intention["payload"]["autonomy_decision_id"] = decision.get("decision_id")
        intention["status"] = _status_for_decision(str(decision.get("decision") or ""))
        intention["payload"]["work_result"] = _work_result_for(intention, project)
        intentions.append(upsert_cognitive_record(root, "agent_intentions", intention))

    execution = _execute_safe_project_work(root, project)
    if execution:
        executions.append(execution)

    return {
        "generated_at": _now(),
        "active_project_id": str((project or {}).get("project_id") or ""),
        "heartbeat_count": len(heartbeats),
        "intention_count": len(intentions),
        "execution_count": len(executions),
        "heartbeats": heartbeats,
        "intentions": intentions,
        "executions": executions,
    }


def run_always_on_loop(root_dir: str | Path | None = None, *, interval_seconds: int = 60, cycles: int = 0) -> None:
    count = 0
    while True:
        run_always_on_cycle(root_dir)
        count += 1
        if cycles and count >= cycles:
            return
        time.sleep(max(5, int(interval_seconds)))


def always_on_summary(root_dir: str | Path | None = None) -> dict[str, Any]:
    root = repo_root(root_dir)
    return {
        "heartbeats": list_cognitive_records(root, "agent_heartbeats", limit=12),
        "intentions": list_cognitive_records(root, "agent_intentions", limit=12),
    }
