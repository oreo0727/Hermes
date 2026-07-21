"""Read-only brain graph projection for Hermes memory and cognition state."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes_stack.agents import AGENT_SPECS
from hermes_stack.mission_control import list_handoffs, list_self_improvement_proposals
from hermes_stack.projects import discover_projects
from hermes_stack.state_store import (
    COGNITIVE_TABLES,
    _connect,
    list_agent_identities,
    list_cognitive_records,
    list_memory_nodes,
    list_memory_synapses,
    runtime_settings,
    using_postgres,
)


COGNITIVE_KINDS = (
    "events",
    "facts",
    "procedures",
    "reflections",
    "activations",
    "beliefs",
    "contradictions",
    "dream_jobs",
    "experiments",
    "skill_evolutions",
    "autonomy_decisions",
    "agent_heartbeats",
    "agent_intentions",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: object, fallback: str = "") -> str:
    result = str(value or "").strip()
    return result or fallback


def _clip(value: object, limit: int = 420) -> str:
    clean = " ".join(_text(value).split())
    return clean if len(clean) <= limit else f"{clean[: limit - 1]}…"


def _node(
    node_id: str,
    *,
    label: str,
    group: str,
    kind: str,
    detail: str = "",
    agent_slug: str = "",
    project_id: str = "",
    weight: float = 1.0,
    source: str = "",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "label": label,
        "group": group,
        "kind": kind,
        "detail": _clip(detail),
        "agent_slug": agent_slug,
        "project_id": project_id,
        "weight": weight,
        "source": source,
        "payload": payload or {},
    }


def _edge(
    edge_id: str,
    source: str,
    target: str,
    *,
    relation: str,
    weight: float = 1.0,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": edge_id,
        "source": source,
        "target": target,
        "relation": relation,
        "weight": weight,
        "payload": payload or {},
    }


def _record_id(kind: str, record: dict[str, Any]) -> str:
    config = COGNITIVE_TABLES.get(kind) or {}
    id_key = config.get("id") or f"{kind}_id"
    return _text(record.get(id_key), f"{kind}:{abs(hash(str(record))) % 1000000}")


def _record_label(kind: str, record: dict[str, Any]) -> str:
    for key in ("title", "subject", "topic", "objective", "hypothesis", "query", "belief", "job_type"):
        if _text(record.get(key)):
            return _text(record.get(key))[:96]
    return _record_id(kind, record)


def _record_detail(kind: str, record: dict[str, Any]) -> str:
    if kind == "facts":
        return f"{_text(record.get('subject'))} {_text(record.get('predicate'))} {_text(record.get('object'))}"
    if kind == "contradictions":
        return f"{_text(record.get('statement_a'))} / {_text(record.get('statement_b'))}"
    for key in ("content", "result", "recommendation", "decision", "observation", "intention", "payload"):
        if record.get(key):
            return _clip(record.get(key))
    return _clip(record)


def _database_stats(root: Path) -> dict[str, Any]:
    settings = runtime_settings(root)
    stats = {
        "backend": settings.get("backend") or "file",
        "database": "postgres" if using_postgres(root) else "file fallback",
        "tables": [],
    }
    if not using_postgres(root):
        return stats

    table_names = [
        "hermes_agents",
        "hermes_memory_nodes",
        "hermes_memory_synapses",
        *[config["table"] for config in COGNITIVE_TABLES.values()],
    ]
    seen: set[str] = set()
    with _connect(root) as conn:
        with conn.cursor() as cur:
            for table in table_names:
                if table in seen:
                    continue
                seen.add(table)
                cur.execute("SELECT to_regclass(%s)", (table,))
                if cur.fetchone()[0] is None:
                    continue
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                stats["tables"].append({"name": table, "rows": int(cur.fetchone()[0] or 0)})
    return stats


def brain_graph(root_dir: str | Path | None = None, *, cognitive_limit: int = 28) -> dict[str, Any]:
    root = Path(root_dir or ".").resolve()
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}

    identities = list_agent_identities(root)
    if not identities:
        identities = [
            {
                "agent_slug": spec.character_name.lower(),
                "profile_key": spec.profile_key,
                "lane": spec.lane,
                "character_name": spec.character_name,
                "title": spec.title,
                "role_summary": spec.role_summary,
            }
            for spec in AGENT_SPECS
        ]

    for agent in identities:
        slug = _text(agent.get("agent_slug") or agent.get("slug")).lower()
        if not slug:
            continue
        node_id = f"agent:{slug}"
        nodes[node_id] = _node(
            node_id,
            label=_text(agent.get("character_name"), slug.title()),
            group="agent",
            kind=_text(agent.get("profile_key") or agent.get("lane"), "agent"),
            detail=_text(agent.get("role_summary") or agent.get("title")),
            agent_slug=slug,
            weight=1.3,
            source="hermes_agents",
            payload=agent,
        )

    for project in discover_projects(root):
        project_id = _text(project.get("project_id"))
        if not project_id:
            continue
        node_id = f"project:{project_id}"
        nodes[node_id] = _node(
            node_id,
            label=_text(project.get("title"), project_id),
            group="project",
            kind=_text(project.get("status"), "project"),
            detail=_text(project.get("summary") or project.get("now") or project.get("next")),
            project_id=project_id,
            weight=1.05,
            source="hermes_projects",
            payload={"project_id": project_id, "status": project.get("status"), "progress_percent": project.get("progress_percent")},
        )

    memory_nodes = list_memory_nodes(root)
    for memory in memory_nodes:
        raw_id = _text(memory.get("node_id"))
        if not raw_id:
            continue
        node_id = f"memory:{raw_id}"
        agent_slug = _text(memory.get("agent_slug")).lower()
        payload = memory.get("payload") if isinstance(memory.get("payload"), dict) else {}
        project_id = _text(payload.get("project_id"))
        nodes[node_id] = _node(
            node_id,
            label=_text(memory.get("title"), raw_id),
            group="memory",
            kind=_text(memory.get("kind"), "memory"),
            detail=_text(memory.get("content")),
            agent_slug=agent_slug,
            project_id=project_id,
            weight=float(memory.get("weight") or 1.0),
            source=_text(memory.get("source_path"), "hermes_memory_nodes"),
            payload=memory,
        )
        if agent_slug and f"agent:{agent_slug}" in nodes:
            edge_id = f"agent-memory:{agent_slug}:{raw_id}"
            edges[edge_id] = _edge(edge_id, f"agent:{agent_slug}", node_id, relation="owns_memory", weight=0.68)
        if project_id and f"project:{project_id}" in nodes:
            edge_id = f"project-memory:{project_id}:{raw_id}"
            edges[edge_id] = _edge(edge_id, f"project:{project_id}", node_id, relation="contextualizes", weight=0.72)

    for synapse in list_memory_synapses(root):
        source = f"memory:{_text(synapse.get('from_node_id'))}"
        target = f"memory:{_text(synapse.get('to_node_id'))}"
        if source not in nodes or target not in nodes:
            continue
        edge_id = f"synapse:{_text(synapse.get('edge_id'), source + target)}"
        edges[edge_id] = _edge(
            edge_id,
            source,
            target,
            relation=_text(synapse.get("relation"), "synapse"),
            weight=float(synapse.get("weight") or 1.0),
            payload=synapse,
        )

    for kind in COGNITIVE_KINDS:
        try:
            records = list_cognitive_records(root, kind=kind, limit=cognitive_limit)
        except Exception:
            records = []
        for record in records:
            raw_id = _record_id(kind, record)
            node_id = f"cognitive:{kind}:{raw_id}"
            agent_slug = _text(record.get("agent_slug")).lower()
            project_id = _text(record.get("project_id"))
            nodes[node_id] = _node(
                node_id,
                label=_record_label(kind, record),
                group="cognitive",
                kind=kind,
                detail=_record_detail(kind, record),
                agent_slug=agent_slug,
                project_id=project_id,
                weight=float(record.get("confidence") or record.get("salience") or 0.65),
                source=COGNITIVE_TABLES.get(kind, {}).get("table", kind),
                payload=record,
            )
            if agent_slug and f"agent:{agent_slug}" in nodes:
                edge_id = f"agent-cog:{agent_slug}:{kind}:{raw_id}"
                edges[edge_id] = _edge(edge_id, f"agent:{agent_slug}", node_id, relation=f"records_{kind}", weight=0.56)
            if project_id and f"project:{project_id}" in nodes:
                edge_id = f"project-cog:{project_id}:{kind}:{raw_id}"
                edges[edge_id] = _edge(edge_id, f"project:{project_id}", node_id, relation=f"has_{kind}", weight=0.56)
            if kind == "activations":
                for activated in record.get("activated_nodes") or []:
                    activated_id = _text(activated.get("node_id") if isinstance(activated, dict) else activated)
                    target = f"memory:{activated_id}"
                    if target in nodes:
                        edge_id = f"activation-memory:{raw_id}:{activated_id}"
                        edges[edge_id] = _edge(edge_id, node_id, target, relation="activated_memory", weight=0.92)

    for handoff in list_handoffs(root, limit=24):
        raw_id = _text(handoff.get("handoff_id"))
        if not raw_id:
            continue
        target_slug = _text(handoff.get("target")).lower()
        project_id = _text(handoff.get("project_id"))
        node_id = f"handoff:{raw_id}"
        nodes[node_id] = _node(
            node_id,
            label=f"{target_slug.title()} handoff",
            group="handoff",
            kind=_text(handoff.get("status"), "queued"),
            detail=_text(handoff.get("instruction")),
            agent_slug=target_slug,
            project_id=project_id,
            weight=0.78,
            source="mission_control/handoffs",
            payload=handoff,
        )
        if target_slug and f"agent:{target_slug}" in nodes:
            edge_id = f"handoff-agent:{raw_id}:{target_slug}"
            edges[edge_id] = _edge(edge_id, f"agent:{target_slug}", node_id, relation="assigned_handoff", weight=0.7)
        if project_id and f"project:{project_id}" in nodes:
            edge_id = f"handoff-project:{raw_id}:{project_id}"
            edges[edge_id] = _edge(edge_id, f"project:{project_id}", node_id, relation="routes_work", weight=0.74)

    for proposal in list_self_improvement_proposals(root, limit=12):
        raw_id = _text(proposal.get("proposal_id"))
        if not raw_id:
            continue
        node_id = f"improvement:{raw_id}"
        nodes[node_id] = _node(
            node_id,
            label=_text(proposal.get("focus"), "Self-improvement proposal"),
            group="improvement",
            kind=_text(proposal.get("status"), "proposed"),
            detail=_text(proposal.get("hypothesis")),
            agent_slug="sheldon",
            weight=0.82,
            source="mission_control/self_improvement",
            payload=proposal,
        )
        if "agent:sheldon" in nodes:
            edge_id = f"improvement-agent:{raw_id}"
            edges[edge_id] = _edge(edge_id, "agent:sheldon", node_id, relation="self_improves", weight=0.86)

    node_list = list(nodes.values())
    edge_list = [edge for edge in edges.values() if edge["source"] in nodes and edge["target"] in nodes]
    node_counts = Counter(str(node.get("group") or "unknown") for node in node_list)
    edge_counts = Counter(str(edge.get("relation") or "unknown") for edge in edge_list)

    return {
        "ok": True,
        "generated_at": _now(),
        "database": _database_stats(root),
        "summary": {
            "nodes": len(node_list),
            "edges": len(edge_list),
            "groups": dict(sorted(node_counts.items())),
            "relations": dict(edge_counts.most_common(14)),
        },
        "nodes": node_list,
        "edges": edge_list,
    }
