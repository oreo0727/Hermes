"""Experimental cognition layer for Hermes agents.

The memory graph stores what the agents know. The cognitive kernel records how
that knowledge gets activated, believed, reflected on, and debated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import re

from hermes_stack.agents import AGENT_SPECS, AgentSpec
from hermes_stack.state_store import (
    list_cognitive_records,
    list_memory_nodes,
    list_project_entries,
    repo_root,
    runtime_settings,
    upsert_cognitive_record,
)


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{2,}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(part or "").strip() for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _tokens(text: object) -> set[str]:
    return set(TOKEN_PATTERN.findall(str(text or "").lower()))


def _agent_slug(value: str) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    for spec in AGENT_SPECS:
        slug = spec.character_name.lower()
        if raw in {slug, spec.profile_key, spec.lane.lower()}:
            return slug
    return raw


def _agent_spec(slug: str) -> AgentSpec | None:
    normalized = _agent_slug(slug)
    for spec in AGENT_SPECS:
        if spec.character_name.lower() == normalized:
            return spec
    return None


def _event(
    *,
    agent_slug: str = "",
    project_id: str = "",
    event_type: str,
    title: str,
    content: str,
    source_ref: str = "",
    salience: float = 0.5,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": f"event:{_stable_id(agent_slug, project_id, event_type, title, content, source_ref)}",
        "agent_slug": agent_slug,
        "project_id": project_id,
        "event_type": event_type,
        "title": title,
        "content": content,
        "source_ref": source_ref,
        "salience": salience,
        "payload": payload or {},
        "occurred_at": _now(),
    }


def _fact(
    *,
    scope: str,
    subject: str,
    predicate: str,
    object_value: str,
    confidence: float = 0.75,
    source_event_id: str = "",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "fact_id": f"fact:{_stable_id(scope, subject, predicate, object_value)}",
        "scope": scope,
        "subject": subject,
        "predicate": predicate,
        "object": object_value,
        "confidence": confidence,
        "source_event_id": source_event_id,
        "payload": payload or {},
    }


def _procedure(spec: AgentSpec, *, trigger: str, title: str, steps: list[str], confidence: float = 0.78) -> dict[str, Any]:
    return {
        "procedure_id": f"procedure:{spec.character_name.lower()}:{_stable_id(trigger, title)}",
        "agent_slug": spec.character_name.lower(),
        "trigger": trigger,
        "title": title,
        "steps": steps,
        "confidence": confidence,
        "payload": {
            "lane": spec.lane,
            "closure_rule": spec.closure_rule,
            "verification_method": spec.verification_method,
        },
    }


def _belief(spec: AgentSpec, *, subject: str, belief: str, confidence: float = 0.82) -> dict[str, Any]:
    return {
        "belief_id": f"belief:{spec.character_name.lower()}:{_stable_id(subject, belief)}",
        "agent_slug": spec.character_name.lower(),
        "subject": subject,
        "belief": belief,
        "confidence": confidence,
        "payload": {"voice": spec.voice},
    }


def seed_cognitive_kernel(root_dir: str | Path | None = None) -> dict[str, Any]:
    root = repo_root(root_dir)
    counts = {
        "events": 0,
        "facts": 0,
        "procedures": 0,
        "beliefs": 0,
        "reflections": 0,
        "contradictions": 0,
    }

    for spec in AGENT_SPECS:
        slug = spec.character_name.lower()
        identity_event = _event(
            agent_slug=slug,
            event_type="identity_seed",
            title=f"{spec.character_name} identity loaded",
            content=f"{spec.character_name} is {spec.title}: {spec.role_summary}",
            source_ref=f"agents/{slug}/identity.md",
            salience=0.95,
            payload={"voice": spec.voice, "owns": list(spec.owns)},
        )
        upsert_cognitive_record(root, "events", identity_event)
        counts["events"] += 1

        for fact in (
            _fact(
                scope="agent",
                subject=slug,
                predicate="has_voice",
                object_value=spec.voice,
                confidence=0.95,
                source_event_id=identity_event["event_id"],
            ),
            _fact(
                scope="agent",
                subject=slug,
                predicate="owns_lane",
                object_value=spec.lane,
                confidence=0.98,
                source_event_id=identity_event["event_id"],
            ),
            _fact(
                scope="agent",
                subject=slug,
                predicate="closes_when",
                object_value=spec.closure_rule,
                confidence=0.92,
                source_event_id=identity_event["event_id"],
            ),
        ):
            upsert_cognitive_record(root, "facts", fact)
            counts["facts"] += 1

        for proc in (
            _procedure(
                spec,
                trigger=f"{spec.lane} work request",
                title=f"{spec.character_name} lane execution loop",
                steps=[
                    "activate relevant memories and facts",
                    "inspect the current project state",
                    "choose direct execution, dispatch, block, or closure",
                    "produce or verify a concrete artifact",
                    "write a reflection when the outcome changes future behavior",
                ],
            ),
            _procedure(
                spec,
                trigger="closure decision",
                title=f"{spec.character_name} proof gate",
                steps=[
                    f"use verification method: {spec.verification_method}",
                    f"apply closure rule: {spec.closure_rule}",
                    "separate implemented, verified, assumed, and blocked",
                ],
                confidence=0.86,
            ),
        ):
            upsert_cognitive_record(root, "procedures", proc)
            counts["procedures"] += 1

        for belief in (
            _belief(spec, subject="operator", belief="The operator values real artifacts, direct progress, and truthful verification.", confidence=0.9),
            _belief(spec, subject=spec.lane, belief=spec.closure_rule, confidence=0.86),
        ):
            upsert_cognitive_record(root, "beliefs", belief)
            counts["beliefs"] += 1

        reflection = {
            "reflection_id": f"reflection:{slug}:seed:{_stable_id(spec.role_summary)}",
            "agent_slug": slug,
            "project_id": "",
            "title": f"{spec.character_name} cognition baseline",
            "content": (
                f"Preserve {spec.character_name}'s existing voice while using memory activation, "
                "belief confidence, and proof gates to change behavior over time."
            ),
            "lessons": [
                "personality is an anchor, not a substitute for verification",
                "memory should alter routing and closure decisions",
            ],
            "payload": {"source": "cognitive_kernel_seed"},
        }
        upsert_cognitive_record(root, "reflections", reflection)
        counts["reflections"] += 1

    for project_root, payload in list_project_entries(root):
        project_id = str(payload.get("project_id") or project_root.name)
        tracking = payload.get("tracking") if isinstance(payload.get("tracking"), dict) else {}
        project_event = _event(
            project_id=project_id,
            event_type="project_state_seed",
            title=f"Project state loaded: {project_id}",
            content=f"{payload.get('title') or project_id}: {payload.get('status') or 'active'}",
            source_ref=str(project_root),
            salience=0.72,
            payload={"tracking": tracking},
        )
        upsert_cognitive_record(root, "events", project_event)
        counts["events"] += 1
        upsert_cognitive_record(
            root,
            "facts",
            _fact(
                scope="project",
                subject=project_id,
                predicate="has_status",
                object_value=str(payload.get("status") or "active"),
                confidence=0.86,
                source_event_id=project_event["event_id"],
            ),
        )
        counts["facts"] += 1

    contradiction_result = detect_contradictions(root)
    counts["contradictions"] += int(contradiction_result.get("created", 0))
    return {"ok": True, "counts": counts}


def _score_record(query_tokens: set[str], record: dict[str, Any], fields: tuple[str, ...]) -> float:
    if not query_tokens:
        return 0.0
    haystack = " ".join(str(record.get(field) or "") for field in fields)
    overlap = len(query_tokens & _tokens(haystack))
    base = overlap / max(1, len(query_tokens))
    weight = float(record.get("weight") or record.get("confidence") or 0.65)
    return round(base * weight, 4)


def activate_cognition(
    root_dir: str | Path | None = None,
    *,
    query: str,
    agent_slug: str = "",
    project_id: str = "",
    limit: int = 8,
) -> dict[str, Any]:
    root = repo_root(root_dir)
    normalized_agent = _agent_slug(agent_slug)
    query_tokens = _tokens(query)

    scored_nodes = []
    for node in list_memory_nodes(root, agent_slug=normalized_agent):
        score = _score_record(query_tokens, node, ("title", "content", "kind", "scope"))
        if score > 0:
            scored_nodes.append({**node, "score": score})
    scored_nodes.sort(key=lambda row: float(row.get("score") or 0), reverse=True)

    scored_facts = []
    for fact in list_cognitive_records(root, "facts", limit=200):
        score = _score_record(query_tokens, fact, ("subject", "predicate", "object", "scope"))
        if score > 0:
            scored_facts.append({**fact, "score": score})
    scored_facts.sort(key=lambda row: float(row.get("score") or 0), reverse=True)

    scored_procedures = []
    for procedure in list_cognitive_records(root, "procedures", agent_slug=normalized_agent, limit=80):
        score = _score_record(query_tokens, procedure, ("trigger", "title"))
        if score > 0:
            scored_procedures.append({**procedure, "score": score})
    scored_procedures.sort(key=lambda row: float(row.get("score") or 0), reverse=True)

    chosen_action = "direct_execute"
    lowered = query.lower()
    if any(token in lowered for token in ("blocked", "stuck", "risk", "contradict")):
        chosen_action = "mark_blocked_or_resolve_contradiction"
    elif any(token in lowered for token in ("visual", "story", "style", "prompt")):
        chosen_action = "dispatch_or_consult_creative"
    elif any(token in lowered for token in ("game", "playable", "runtime", "export")):
        chosen_action = "dispatch_or_consult_game"
    elif any(token in lowered for token in ("app", "backend", "portal", "api", "test")):
        chosen_action = "dispatch_or_consult_app"
    elif any(token in lowered for token in ("plan", "route", "status", "queue")):
        chosen_action = "operator_synthesize"

    top_nodes = scored_nodes[:limit]
    top_facts = scored_facts[:limit]
    top_procedures = scored_procedures[:limit]
    confidence = min(
        1.0,
        sum(float(row.get("score") or 0) for row in [*top_nodes[:3], *top_facts[:3], *top_procedures[:2]]),
    )

    activation = {
        "activation_id": f"activation:{_stable_id(query, normalized_agent, project_id, _now())}",
        "query": query,
        "agent_slug": normalized_agent,
        "project_id": project_id,
        "activated_nodes": [
            {"node_id": row.get("node_id"), "title": row.get("title"), "kind": row.get("kind"), "score": row.get("score")}
            for row in top_nodes
        ],
        "activated_facts": [
            {"fact_id": row.get("fact_id"), "subject": row.get("subject"), "predicate": row.get("predicate"), "object": row.get("object"), "score": row.get("score")}
            for row in top_facts
        ],
        "activated_procedures": [
            {"procedure_id": row.get("procedure_id"), "title": row.get("title"), "score": row.get("score")}
            for row in top_procedures
        ],
        "chosen_action": chosen_action,
        "confidence": round(confidence, 4),
        "payload": {"token_count": len(query_tokens)},
    }
    upsert_cognitive_record(root, "activations", activation)
    return activation


def write_reflection(
    root_dir: str | Path | None = None,
    *,
    agent_slug: str,
    title: str,
    content: str,
    project_id: str = "",
    lessons: list[str] | None = None,
) -> dict[str, Any]:
    root = repo_root(root_dir)
    normalized_agent = _agent_slug(agent_slug)
    reflection = {
        "reflection_id": f"reflection:{normalized_agent}:{_stable_id(project_id, title, content)}",
        "agent_slug": normalized_agent,
        "project_id": project_id,
        "title": title,
        "content": content,
        "lessons": lessons or [],
        "payload": {"source": "manual_or_runtime_reflection"},
    }
    upsert_cognitive_record(root, "reflections", reflection)
    return reflection


def detect_contradictions(root_dir: str | Path | None = None) -> dict[str, Any]:
    root = repo_root(root_dir)
    created = 0
    rows: list[dict[str, Any]] = []
    for _project_root, payload in list_project_entries(root):
        project_id = str(payload.get("project_id") or "").strip()
        status = str(payload.get("status") or "").strip().lower()
        tracking = payload.get("tracking") if isinstance(payload.get("tracking"), dict) else {}
        blocked = tracking.get("blocked") if isinstance(tracking.get("blocked"), list) else []
        portfolio = payload.get("portfolio") if isinstance(payload.get("portfolio"), dict) else {}
        portfolio_state = str(portfolio.get("state") or "").strip().lower()

        checks = []
        if status in {"completed", "done"} and blocked:
            checks.append((
                "project marked complete",
                f"project has blockers: {', '.join(str(item) for item in blocked[:3])}",
                0.82,
            ))
        if status == "archived" and portfolio_state == "active":
            checks.append(("project is archived", "portfolio says project is active", 0.76))

        for statement_a, statement_b, severity in checks:
            contradiction = {
                "contradiction_id": f"contradiction:{_stable_id(project_id, statement_a, statement_b)}",
                "scope": "project",
                "subject": project_id,
                "statement_a": statement_a,
                "statement_b": statement_b,
                "status": "open",
                "severity": severity,
                "payload": {"source": "detect_contradictions"},
            }
            upsert_cognitive_record(root, "contradictions", contradiction)
            created += 1
            rows.append(contradiction)
    return {"ok": True, "created": created, "contradictions": rows}


def run_dream_cycle(root_dir: str | Path | None = None) -> dict[str, Any]:
    root = repo_root(root_dir)
    jobs = []
    projects = [payload for _project_root, payload in list_project_entries(root)]
    open_contradictions = [
        row for row in list_cognitive_records(root, "contradictions", limit=50)
        if str(row.get("status") or "open") == "open"
    ]

    for spec in AGENT_SPECS:
        slug = spec.character_name.lower()
        relevant_projects = [
            row for row in projects
            if spec.profile_key == "operator"
            or spec.profile_key in (row.get("specialists") if isinstance(row.get("specialists"), list) else [])
            or spec.lane in (row.get("specialists") if isinstance(row.get("specialists"), list) else [])
        ]
        objective = (
            f"Review {len(relevant_projects)} relevant project(s), "
            f"{len(open_contradictions)} open contradiction(s), and extract the next useful cognitive link for {spec.character_name}."
        )
        result = {
            "recommended_focus": "resolve contradictions first" if open_contradictions and spec.profile_key == "operator" else "strengthen reusable procedures",
            "project_ids": [str(row.get("project_id") or "") for row in relevant_projects[:6]],
            "contradictions": [str(row.get("contradiction_id") or "") for row in open_contradictions[:6]],
        }
        job = {
            "job_id": f"dream:{slug}:{_stable_id(objective, result)}",
            "agent_slug": slug,
            "job_type": "idle_cognition",
            "status": "completed",
            "objective": objective,
            "result": result,
        }
        upsert_cognitive_record(root, "dream_jobs", job)
        jobs.append(job)
    return {"ok": True, "jobs": jobs}


def convene_council(
    root_dir: str | Path | None = None,
    *,
    topic: str,
    project_id: str = "",
) -> dict[str, Any]:
    root = repo_root(root_dir)
    positions = []
    for spec in AGENT_SPECS:
        activation = activate_cognition(root, query=topic, agent_slug=spec.character_name.lower(), project_id=project_id, limit=5)
        positions.append(
            {
                "agent_slug": spec.character_name.lower(),
                "character_name": spec.character_name,
                "lane": spec.lane,
                "stance": activation["chosen_action"],
                "confidence": activation["confidence"],
                "top_memory": (activation.get("activated_nodes") or [{}])[0],
            }
        )
    operator_position = next((row for row in positions if row["agent_slug"] == "sheldon"), positions[0])
    decision = (
        "Sheldon should arbitrate, then route to the highest-confidence specialist lane with proof requirements attached."
        if operator_position["confidence"] >= 0.15
        else "Run one clarification/activation pass before committing a lane."
    )
    confidence = round(max(float(row.get("confidence") or 0) for row in positions), 4)
    council = {
        "council_id": f"council:{_stable_id(project_id, topic, _now())}",
        "project_id": project_id,
        "topic": topic,
        "positions": positions,
        "decision": decision,
        "confidence": confidence,
        "payload": {"source": "convene_council"},
    }
    upsert_cognitive_record(root, "council_records", council)
    return council


def cognitive_summary(root_dir: str | Path | None = None) -> dict[str, Any]:
    root = repo_root(root_dir)
    counts = {
        kind: len(list_cognitive_records(root, kind, limit=10000))
        for kind in (
            "events",
            "facts",
            "procedures",
            "reflections",
            "activations",
            "beliefs",
            "contradictions",
            "dream_jobs",
            "council_records",
            "experiments",
            "skill_evolutions",
            "autonomy_decisions",
        )
    }
    open_contradictions = [
        row for row in list_cognitive_records(root, "contradictions", limit=100)
        if str(row.get("status") or "open") == "open"
    ]
    recent_activations = list_cognitive_records(root, "activations", limit=5)
    recent_dreams = list_cognitive_records(root, "dream_jobs", limit=5)
    recent_councils = list_cognitive_records(root, "council_records", limit=5)
    return {
        "storage": runtime_settings(root).get("backend"),
        "counts": counts,
        "open_contradictions": open_contradictions[:8],
        "recent_activations": recent_activations,
        "recent_dreams": recent_dreams,
        "recent_councils": recent_councils,
    }
