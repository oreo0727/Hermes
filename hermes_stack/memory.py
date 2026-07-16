"""Agent memory graph seeding and inspection for Hermes."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

from hermes_stack.agents import AGENT_SPECS, AgentSpec
from hermes_stack.state_store import (
    list_memory_nodes,
    list_memory_synapses,
    list_project_entries,
    repo_root,
    upsert_agent_identity,
    upsert_memory_node,
    upsert_memory_synapse,
)


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(part or "").strip() for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _agent_dir(root: Path, spec: AgentSpec) -> Path:
    return root / "agents" / spec.character_name.lower()


def _profile_home(root: Path, spec: AgentSpec) -> Path:
    return root / "state" / "hermes" / "profiles" / spec.profile_key


def _bullet_items(text: str) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            value = stripped[2:].strip()
            if value:
                rows.append(value)
    return rows


def _node(
    *,
    spec: AgentSpec,
    kind: str,
    title: str,
    content: str,
    source_path: Path | str = "",
    scope: str = "agent",
    weight: float = 1.0,
    confidence: float = 1.0,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_text = str(source_path or "")
    return {
        "node_id": f"{spec.character_name.lower()}:{kind}:{_stable_id(title, content, source_text)}",
        "agent_slug": spec.character_name.lower(),
        "scope": scope,
        "kind": kind,
        "title": title.strip(),
        "content": content.strip(),
        "source_path": source_text,
        "confidence": confidence,
        "weight": weight,
        "payload": payload or {},
    }


def _edge(
    *,
    spec: AgentSpec,
    from_node_id: str,
    to_node_id: str,
    relation: str,
    weight: float = 1.0,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "edge_id": f"{spec.character_name.lower()}:{relation}:{_stable_id(from_node_id, to_node_id)}",
        "agent_slug": spec.character_name.lower(),
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "relation": relation,
        "weight": weight,
        "payload": payload or {},
    }


def _project_memory_nodes(root: Path, spec: AgentSpec) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for project_root, payload in list_project_entries(root):
        specialists = payload.get("specialists") if isinstance(payload.get("specialists"), list) else []
        control = payload.get("control") if isinstance(payload.get("control"), dict) else {}
        primary_lane = str(control.get("primary_lane") or "").strip()
        lane_sequence = control.get("lane_sequence") if isinstance(control.get("lane_sequence"), list) else []
        relevant = (
            spec.profile_key in specialists
            or spec.lane in specialists
            or spec.profile_key == primary_lane
            or spec.profile_key in lane_sequence
            or spec.profile_key == "operator"
        )
        if not relevant:
            continue
        tracking = payload.get("tracking") if isinstance(payload.get("tracking"), dict) else {}
        summary = "\n".join(
            item
            for item in (
                f"Project: {payload.get('title') or payload.get('project_id')}",
                f"Status: {payload.get('status') or 'active'}",
                f"Summary: {payload.get('summary') or ''}",
                f"Now: {tracking.get('now') or ''}",
                f"Next: {tracking.get('next') or ''}",
                f"Blocked: {', '.join(str(row) for row in tracking.get('blocked') or [])}",
            )
            if item.split(":", 1)[-1].strip()
        )
        nodes.append(
            _node(
                spec=spec,
                kind="project_context",
                title=str(payload.get("project_id") or project_root.name),
                content=summary,
                source_path=project_root,
                scope="project",
                weight=0.72 if spec.profile_key == "operator" else 0.58,
                payload={
                    "project_id": payload.get("project_id") or project_root.name,
                    "status": payload.get("status") or "",
                    "primary_lane": primary_lane,
                },
            )
        )
    return nodes


def _normalize_agent_slug(value: str) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    for spec in AGENT_SPECS:
        slug = spec.character_name.lower()
        if raw in {slug, spec.profile_key, spec.lane.lower()}:
            return slug
    return raw


def seed_agent_memory(root_dir: str | Path | None = None) -> dict[str, Any]:
    root = repo_root(root_dir)
    counts = {
        "agents": 0,
        "nodes": 0,
        "synapses": 0,
    }
    by_agent: dict[str, dict[str, int]] = {}

    for spec in AGENT_SPECS:
        slug = spec.character_name.lower()
        agent_dir = _agent_dir(root, spec)
        profile_home = _profile_home(root, spec)
        identity_path = agent_dir / "identity.md"
        prompt_path = agent_dir / "system_prompt.md"
        memory_readme_path = agent_dir / "memory" / "README.md"
        soul_path = profile_home / "SOUL.md"
        memory_path = profile_home / "memories" / "MEMORY.md"
        user_path = profile_home / "memories" / "USER.md"

        identity_payload = {
            "agent_slug": slug,
            "character_name": spec.character_name,
            "profile_key": spec.profile_key,
            "lane": spec.lane,
            "title": spec.title,
            "voice": spec.voice,
            "role_summary": spec.role_summary,
            "owns": list(spec.owns),
            "tools_allowed": list(spec.tools_allowed),
            "artifact_types": list(spec.artifact_types),
            "verification_method": spec.verification_method,
            "closure_rule": spec.closure_rule,
            "source_paths": {
                "identity": str(identity_path),
                "system_prompt": str(prompt_path),
                "memory_readme": str(memory_readme_path),
                "soul": str(soul_path),
                "memory": str(memory_path),
                "user": str(user_path),
            },
        }
        upsert_agent_identity(root, identity_payload)
        counts["agents"] += 1
        by_agent[slug] = {"nodes": 0, "synapses": 0}

        identity_node = _node(
            spec=spec,
            kind="identity_anchor",
            title=f"{spec.character_name} identity",
            content=_read_text(identity_path) or spec.role_summary,
            source_path=identity_path,
            weight=1.0,
            payload={"voice": spec.voice, "role_summary": spec.role_summary},
        )
        prompt_node = _node(
            spec=spec,
            kind="behavior_contract",
            title=f"{spec.character_name} system prompt",
            content=_read_text(prompt_path),
            source_path=prompt_path,
            weight=0.95,
        )
        soul_node = _node(
            spec=spec,
            kind="personality_contract",
            title=f"{spec.character_name} SOUL",
            content=_read_text(soul_path),
            source_path=soul_path,
            weight=0.92,
        )
        profile_memory_node = _node(
            spec=spec,
            kind="profile_memory",
            title=f"{spec.character_name} profile memory",
            content=_read_text(memory_path),
            source_path=memory_path,
            weight=0.82,
        )

        nodes = [identity_node, prompt_node, soul_node, profile_memory_node]

        memory_readme = _read_text(memory_readme_path)
        for item in _bullet_items(memory_readme):
            nodes.append(
                _node(
                    spec=spec,
                    kind="durable_memory_bucket",
                    title=item,
                    content=item,
                    source_path=memory_readme_path,
                    weight=0.74,
                )
            )

        user_text = _read_text(user_path)
        for item in _bullet_items(user_text):
            nodes.append(
                _node(
                    spec=spec,
                    kind="operator_preference",
                    title=item[:96],
                    content=item,
                    source_path=user_path,
                    scope="operator",
                    weight=0.9,
                )
            )

        nodes.extend(_project_memory_nodes(root, spec))

        for node in nodes:
            if node["content"]:
                upsert_memory_node(root, node)
                counts["nodes"] += 1
                by_agent[slug]["nodes"] += 1

        edges = [
            _edge(
                spec=spec,
                from_node_id=identity_node["node_id"],
                to_node_id=prompt_node["node_id"],
                relation="governs_behavior",
                weight=0.96,
            ),
            _edge(
                spec=spec,
                from_node_id=identity_node["node_id"],
                to_node_id=soul_node["node_id"],
                relation="expresses_personality",
                weight=0.92,
            ),
            _edge(
                spec=spec,
                from_node_id=identity_node["node_id"],
                to_node_id=profile_memory_node["node_id"],
                relation="grounds_memory",
                weight=0.82,
            ),
        ]

        for node in nodes:
            if node["node_id"] in {identity_node["node_id"], prompt_node["node_id"], soul_node["node_id"], profile_memory_node["node_id"]}:
                continue
            relation = {
                "operator_preference": "serves_operator_preference",
                "project_context": "recalls_project_context",
                "durable_memory_bucket": "specializes_memory",
            }.get(str(node["kind"]), "associates")
            edges.append(
                _edge(
                    spec=spec,
                    from_node_id=identity_node["node_id"],
                    to_node_id=node["node_id"],
                    relation=relation,
                    weight=float(node.get("weight") or 0.7),
                )
            )

        for edge in edges:
            upsert_memory_synapse(root, edge)
            counts["synapses"] += 1
            by_agent[slug]["synapses"] += 1

    return {"ok": True, "counts": counts, "agents": by_agent}


def agent_memory_summary(root_dir: str | Path | None = None, *, agent_slug: str = "") -> dict[str, Any]:
    root = repo_root(root_dir)
    agent_slug = _normalize_agent_slug(agent_slug)
    nodes = list_memory_nodes(root, agent_slug=agent_slug)
    synapses = list_memory_synapses(root, agent_slug=agent_slug)
    by_agent: dict[str, dict[str, Any]] = {}
    for node in nodes:
        slug = str(node.get("agent_slug") or "").strip()
        if not slug:
            continue
        row = by_agent.setdefault(slug, {"node_count": 0, "synapse_count": 0, "kinds": {}, "strongest": []})
        row["node_count"] += 1
        kinds = row["kinds"]
        if isinstance(kinds, dict):
            kind = str(node.get("kind") or "unknown")
            kinds[kind] = int(kinds.get(kind, 0)) + 1
        strongest = row["strongest"]
        if isinstance(strongest, list) and len(strongest) < 6:
            strongest.append(
                {
                    "kind": node.get("kind"),
                    "title": node.get("title"),
                    "weight": node.get("weight"),
                }
            )
    for edge in synapses:
        slug = str(edge.get("agent_slug") or "").strip()
        if not slug:
            continue
        row = by_agent.setdefault(slug, {"node_count": 0, "synapse_count": 0, "kinds": {}, "strongest": []})
        row["synapse_count"] += 1
    return {
        "agent_slug": agent_slug.strip().lower(),
        "total_nodes": len(nodes),
        "total_synapses": len(synapses),
        "agents": by_agent,
    }
