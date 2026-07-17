"""Fast deterministic chat reflexes for the Hermes operator portal."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import re

from hermes_stack.cognitive_kernel import activate_cognition, cognitive_summary
from hermes_stack.projects import activate_project, discover_projects, portfolio_snapshot, update_project


HEAVY_REQUEST_PATTERN = re.compile(
    r"\b("
    r"build|implement|fix|change|update|delete|remove|install|deploy|push|commit|"
    r"create|generate|write|edit|refactor|migrate|restart|stop|start|run|test|"
    r"research|browse|look\s+up|scrape|download"
    r")\b",
    re.IGNORECASE,
)
FAST_REQUEST_PATTERN = re.compile(
    r"\b("
    r"hi|hello|hey|status|where|what'?s|what is|queue|project|blocked|proof|"
    r"memory|cognition|brain|synapse|route|agent|team|who|slow|portal|chat|"
    r"gateway|online|ready|brief|summary|recap"
    r")\b",
    re.IGNORECASE,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(part or "").strip() for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _latest_user_content(messages: list[dict[str, object]]) -> str:
    for message in reversed(messages):
        if str(message.get("role") or "") != "user":
            continue
        content = str(message.get("content") or "").strip()
        if content:
            return content
    return ""


def _active_project(projects: list[dict[str, Any]], project_id: str) -> dict[str, Any] | None:
    normalized = project_id.strip()
    if normalized:
        return next((row for row in projects if str(row.get("project_id") or "") == normalized), None)
    return next((row for row in projects if bool((row.get("portfolio") or {}).get("active"))), None)


def _normalize_match_text(value: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return " ".join(normalized.split())


def _looks_like_focus_request(query: str) -> bool:
    normalized = _normalize_match_text(query)
    return _has_intent(
        normalized,
        (
            "pick back up",
            "back up on",
            "continue",
            "resume",
            "switch to",
            "focus",
            "open project",
            "work on",
        ),
    )


def _resolve_requested_project(query: str, projects: list[dict[str, Any]]) -> dict[str, Any] | None:
    normalized_query = _normalize_match_text(query)
    if not normalized_query:
        return None
    scored: list[tuple[float, dict[str, Any]]] = []
    query_tokens = set(normalized_query.split())
    for project in projects:
        project_id = str(project.get("project_id") or "")
        title = str(project.get("title") or "")
        candidates = (
            _normalize_match_text(project_id),
            _normalize_match_text(project_id.replace("-", " ")),
            _normalize_match_text(title),
        )
        best_score = 0.0
        for candidate in candidates:
            if not candidate:
                continue
            if candidate in normalized_query:
                best_score = max(best_score, 1.0)
                continue
            candidate_tokens = set(candidate.split())
            if candidate_tokens:
                overlap_count = len(query_tokens & candidate_tokens)
                overlap = overlap_count / len(candidate_tokens)
                if overlap_count >= 2:
                    overlap = max(overlap, 0.72)
                best_score = max(best_score, overlap)
        if best_score >= 0.55:
            scored.append((best_score, project))
    scored.sort(key=lambda row: row[0], reverse=True)
    return scored[0][1] if scored else None


def _is_fast_safe(query: str) -> bool:
    compact = " ".join(query.split())
    if not compact:
        return False
    if len(compact) > 420:
        return False
    if HEAVY_REQUEST_PATTERN.search(compact):
        return False
    if _looks_like_focus_request(compact):
        return True
    return bool(FAST_REQUEST_PATTERN.search(compact)) or len(compact.split()) <= 4


def _has_intent(text: str, intents: tuple[str, ...]) -> bool:
    for intent in intents:
        pattern = r"\b" + re.escape(intent).replace(r"\ ", r"\s+") + r"\b"
        if re.search(pattern, text):
            return True
    return False


def _project_lines(project: dict[str, Any] | None) -> list[str]:
    if not project:
        return ["No active project is focused right now."]
    blocked = list(project.get("blocked") or [])
    done = list(project.get("done") or [])
    return [
        f"Focus: {project.get('title') or project.get('project_id')} ({project.get('status') or 'active'}).",
        f"Now: {project.get('now') or 'No current milestone recorded.'}",
        f"Next: {project.get('next') or 'No next step recorded.'}",
        f"Blocked: {blocked[0] if blocked else 'none recorded.'}",
        f"Proof: {done[0] if done else 'no proof signal attached yet.'}",
    ]


def _focus_reply(project: dict[str, Any], *, revived: bool) -> str:
    title = str(project.get("title") or project.get("project_id") or "the project")
    blocked = [str(item).strip() for item in project.get("blocked") or [] if str(item).strip()]
    next_value = str(project.get("next") or "").strip()
    lines = [
        f"Focused {title}.",
        "I revived it from archived state and made it the active project." if revived else "I made it the active project.",
    ]
    if next_value:
        lines.append(f"Next: {next_value}")
    if blocked:
        lines.append(f"First blocker: {blocked[0]}")
    else:
        lines.append("No blocker is recorded right now.")
    return "\n".join(lines)


def _resume_next_value(project: dict[str, Any]) -> str:
    blocked = [str(item).strip() for item in project.get("blocked") or [] if str(item).strip()]
    if blocked:
        return "Resume by resolving or bypassing the first recorded blocker, then refresh the production slice."
    return "Resume by refreshing the current milestone and choosing the next concrete production slice."


def _has_stale_pause_next(project: dict[str, Any]) -> bool:
    next_value = str(project.get("next") or "").strip().lower()
    return any(token in next_value for token in ("global stop", "pause", "paused", "archived", "archive"))


def _team_line() -> str:
    return (
        "Team routing: Sheldon owns operator/control, Penny owns creative QA, "
        "Raj owns app/portal/backend, and Leonard owns game/runtime proof."
    )


def _is_small_talk(text: str) -> bool:
    return _has_intent(
        text,
        (
            "how are you",
            "how are things",
            "how is it going",
            "hows it going",
            "how's it going",
            "great",
            "nice",
            "thanks",
            "thank you",
            "cool",
            "awesome",
        ),
    )


def _compose_fast_reply(
    *,
    query: str,
    project: dict[str, Any] | None,
    activation: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    normalized = query.lower()
    counts = summary.get("counts") if isinstance(summary.get("counts"), dict) else {}
    chosen_action = str(activation.get("chosen_action") or "operator_synthesize")
    confidence = float(activation.get("confidence") or 0.0)
    project_lines = _project_lines(project)

    if _is_small_talk(normalized):
        return (
            "Going smoothly. The bubble is online, the fast route is behaving, "
            "and I am keeping one eye on the active project without turning every pleasantry into a quarterly report.\n"
            f"{project_lines[0]}"
        )

    if _has_intent(normalized, ("hi", "hello", "hey", "online", "ready")):
        return (
            "I am online in fast-router mode. Tiny lab coat, very low latency.\n"
            f"{project_lines[0]}\n"
            "Ask for status, routing, blockers, memory, or proof and I can answer immediately; "
            "ask me to build or fix something and I will escalate to deep Sheldon."
        )

    if _has_intent(normalized, ("memory", "cognition", "brain", "synapse")):
        return (
            "Cognitive layer is active.\n"
            f"Storage: {summary.get('storage') or 'unknown'}.\n"
            f"Recorded cognition: {counts.get('facts', 0)} facts, {counts.get('procedures', 0)} procedures, "
            f"{counts.get('activations', 0)} activations, {counts.get('reflections', 0)} reflections.\n"
            f"Latest activation routed this as `{chosen_action}` with confidence {confidence:.2f}."
        )

    if _has_intent(normalized, ("who", "agent", "team", "route")):
        return (
            f"{_team_line()}\n"
            f"For this message, my cognitive router chose `{chosen_action}` at confidence {confidence:.2f}."
        )

    if _has_intent(normalized, ("slow", "portal", "chat", "gateway")):
        return (
            "The portal now has a reflex path: lightweight status/routing questions answer locally first. "
            "Heavier build/fix requests still go through the full operator gateway so we do not fake work.\n"
            f"Current route: `{chosen_action}`, confidence {confidence:.2f}."
        )

    return "\n".join(
        [
            "Status snapshot:",
            *project_lines,
            "Queue: tracked in portfolio state.",
            f"Cognitive route: `{chosen_action}` at confidence {confidence:.2f}.",
            _team_line(),
        ]
    )


def fast_route_chat(
    root_dir: str | Path | None,
    *,
    profile_key: str,
    project_id: str = "",
    messages: list[dict[str, object]],
) -> dict[str, Any] | None:
    """Return a local response when a portal message is safe to answer without the LLM gateway."""
    query = _latest_user_content(messages)
    if profile_key != "operator" or not _is_fast_safe(query):
        return None

    root = Path(root_dir).resolve() if root_dir is not None else Path.cwd()
    projects = discover_projects(root)
    portfolio = portfolio_snapshot(root)
    focus_project = _resolve_requested_project(query, projects) if _looks_like_focus_request(query) else None
    if focus_project is not None:
        focus_project_id = str(focus_project.get("project_id") or "").strip()
        revived = str(focus_project.get("status") or "").strip().lower() == "archived"
        if revived or _has_stale_pause_next(focus_project):
            update_project(root, project_id=focus_project_id, status="active", next_value=_resume_next_value(focus_project))
        activate_project(root, project_id=focus_project_id, reason=f"Focused from portal chat: {query[:160]}")
        projects = discover_projects(root)
        project = _active_project(projects, focus_project_id) or focus_project
        activation = activate_cognition(
            root,
            query=query,
            agent_slug="sheldon",
            project_id=focus_project_id,
            limit=5,
        )
        session_id = f"fast:{_stable_id(focus_project_id, query, _now()[:13])}"
        return {
            "ok": True,
            "profile": profile_key,
            "project_id": focus_project_id,
            "label": "Operator",
            "session_id": "",
            "content": _focus_reply(project, revived=revived),
            "structured_result": {},
            "work_order": {
                "action_type": "focus_project",
                "source": "portal-chat-fast-router",
                "project_id": focus_project_id,
                "chosen_action": activation.get("chosen_action"),
                "confidence": activation.get("confidence"),
            },
            "quality_flags": [],
            "prepared_updates": [],
            "raw": {
                "fast_router": True,
                "generated_at": _now(),
                "activation_id": activation.get("activation_id"),
                "synthetic_session_id": session_id,
            },
            "fast_path": True,
        }
    effective_project_id = project_id.strip() or str(portfolio.get("active_project_id") or "").strip()
    project = _active_project(projects, effective_project_id)
    if project and not effective_project_id:
        effective_project_id = str(project.get("project_id") or "")
    activation = activate_cognition(
        root,
        query=query,
        agent_slug="sheldon",
        project_id=effective_project_id,
        limit=5,
    )
    summary = cognitive_summary(root)
    content = _compose_fast_reply(
        query=query,
        project=project,
        activation=activation,
        summary=summary,
    )
    session_id = f"fast:{_stable_id(effective_project_id, query, _now()[:13])}"
    return {
        "ok": True,
        "profile": profile_key,
        "project_id": effective_project_id,
        "label": "Operator",
        "session_id": "",
        "content": content,
        "structured_result": {},
        "work_order": {
            "action_type": "fast_reflex",
            "source": "portal-chat-fast-router",
            "project_id": effective_project_id,
            "chosen_action": activation.get("chosen_action"),
            "confidence": activation.get("confidence"),
        },
        "quality_flags": [],
        "prepared_updates": [],
        "raw": {
            "fast_router": True,
            "generated_at": _now(),
            "activation_id": activation.get("activation_id"),
            "synthetic_session_id": session_id,
        },
        "fast_path": True,
    }
