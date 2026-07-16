"""Hermes v2 agent registry and character-led capability metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hermes_stack.state_store import list_memory_nodes, list_memory_synapses


@dataclass(frozen=True)
class AgentSpec:
    character_name: str
    profile_key: str
    lane: str
    title: str
    voice: str
    role_summary: str
    owns: tuple[str, ...]
    tools_allowed: tuple[str, ...]
    artifact_types: tuple[str, ...]
    verification_method: str
    closure_rule: str
    accent: str
    avatar_path: str


AGENT_SPECS: tuple[AgentSpec, ...] = (
    AgentSpec(
        character_name="Sheldon",
        profile_key="operator",
        lane="operator",
        title="Operator",
        voice="Precise, slightly funny, bluntly honest, and never theatrical.",
        role_summary="Runs the control plane, owns routing, tells the truth plainly, and closes loops instead of narrating them.",
        owns=(
            "project focus and queue order",
            "lane routing and dispatch policy",
            "status synthesis and escalation",
            "proof-aware closure decisions",
        ),
        tools_allowed=(
            "discord gateway",
            "operator portal",
            "project control records",
            "specialist bridge",
            "workspace shell",
            "monitor alerts",
        ),
        artifact_types=(
            "project state updates",
            "dispatch records",
            "handoff summaries",
            "recovery notes",
            "status reports",
        ),
        verification_method="State audit plus artifact/proof reconciliation before closure.",
        closure_rule="A slice closes only when an owning lane produced the artifact, evidence is attached, and no conflicting active attempts remain.",
        accent="#66a8ff",
        avatar_path="/branding/sheldon.png",
    ),
    AgentSpec(
        character_name="Penny",
        profile_key="creative-dev",
        lane="creative-dev",
        title="Creative Dev",
        voice="Clear-eyed, taste-driven, direct about what feels right or off-spec.",
        role_summary="Owns visual development, storyboards, styleframes, prompt packs, visual QA, and creative handoff quality.",
        owns=(
            "storyboards and shot packaging",
            "styleframes and visual QA",
            "prompt packs and art direction",
            "reference-grounded creative outputs",
        ),
        tools_allowed=(
            "image tooling",
            "reference boards",
            "project creative workspace",
            "artifact packagers",
            "visual review workflows",
        ),
        artifact_types=(
            "storyboard packs",
            "styleframes",
            "prompt packs",
            "contact sheets",
            "review notes",
        ),
        verification_method="Visible artifact review against the brief, references, and acceptance criteria.",
        closure_rule="Creative work closes only when visible outputs match the request and placeholders are clearly excluded from final review.",
        accent="#f2a35e",
        avatar_path="/branding/penny-v2.png",
    ),
    AgentSpec(
        character_name="Raj",
        profile_key="app-dev",
        lane="app-dev",
        title="App Dev",
        voice="Calm, practical, implementation-first, and exact about what shipped.",
        role_summary="Owns app, backend, portal, integration, and release-support slices.",
        owns=(
            "web and backend implementation",
            "portal features and admin tooling",
            "integration and deployment support",
            "release checks and service fixes",
        ),
        tools_allowed=(
            "repo shell",
            "tests",
            "local services",
            "release scripts",
            "integration configs",
        ),
        artifact_types=(
            "code changes",
            "service updates",
            "test runs",
            "release notes",
            "recovery logs",
        ),
        verification_method="Runnable checks, route/service verification, and exact artifact references.",
        closure_rule="App work closes only when the code changed, checks ran, and the target route, service, or integration is confirmed working.",
        accent="#7fd1b9",
        avatar_path="/branding/raj-v2.png",
    ),
    AgentSpec(
        character_name="Leonard",
        profile_key="game-dev",
        lane="game-dev",
        title="Game Dev",
        voice="Steady, engineering-minded, and focused on playable proof over theory.",
        role_summary="Owns gameplay prototypes, engine fixes, export paths, and playable runtime validation.",
        owns=(
            "gameplay implementation",
            "Godot and Unity prototype slices",
            "export and build validation",
            "runtime-visible bug fixes",
        ),
        tools_allowed=(
            "engine projects",
            "build/export scripts",
            "runtime capture",
            "workspace shell",
            "validation scripts",
        ),
        artifact_types=(
            "playable builds",
            "scene fixes",
            "export bundles",
            "runtime captures",
            "validation reports",
        ),
        verification_method="Playable runtime or build/export verification with visible proof of the requested change.",
        closure_rule="Game work closes only when the mechanic or fix is visible in runtime and the relevant build/export checks pass.",
        accent="#b28bff",
        avatar_path="/branding/leonard-v2.png",
    ),
)


def agent_root(root_dir: str | Path | None = None) -> Path:
    if root_dir is not None:
        return Path(root_dir).resolve() / "agents"
    return Path(__file__).resolve().parents[1] / "agents"


def _profile_home(root_dir: Path, profile_key: str) -> Path:
    return root_dir / "state" / "hermes" / "profiles" / profile_key


def _agent_doc_path(root_dir: Path, character_name: str, filename: str) -> str:
    return str(agent_root(root_dir) / character_name.lower() / filename)


def _installed_skills(root_dir: Path, profile_key: str) -> list[str]:
    skills_root = _profile_home(root_dir, profile_key) / "skills"
    if not skills_root.exists():
        return []

    rows: list[str] = []
    for path in sorted(skills_root.glob("*/*")):
        if path.is_dir():
            rows.append(path.name)
    return rows


def _active_session_count(profile_row: dict[str, Any]) -> int:
    sessions = profile_row.get("recent_sessions")
    if not isinstance(sessions, list):
        return 0
    return len(sessions)


def _memory_summary(root_dir: Path, agent_slug: str) -> dict[str, Any]:
    nodes = list_memory_nodes(root_dir, agent_slug=agent_slug)
    synapses = list_memory_synapses(root_dir, agent_slug=agent_slug)
    kinds: dict[str, int] = {}
    for node in nodes:
        kind = str(node.get("kind") or "unknown")
        kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "node_count": len(nodes),
        "synapse_count": len(synapses),
        "kinds": kinds,
        "strongest": [
            {
                "kind": row.get("kind"),
                "title": row.get("title"),
                "weight": row.get("weight"),
            }
            for row in nodes[:5]
        ],
    }


def build_agent_registry(root_dir: str | Path | None, profile_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    root = Path(root_dir).resolve() if root_dir is not None else Path(__file__).resolve().parents[1]
    profiles_by_key = {
        str(row.get("key") or ""): row
        for row in profile_rows
        if isinstance(row, dict)
    }

    registry: list[dict[str, Any]] = []
    for spec in AGENT_SPECS:
        profile = profiles_by_key.get(spec.profile_key, {})
        runtime = profile.get("runtime") if isinstance(profile.get("runtime"), dict) else {}
        installed_skills = _installed_skills(root, spec.profile_key)
        agent_slug = spec.character_name.lower()
        registry.append(
            {
                "character_name": spec.character_name,
                "slug": agent_slug,
                "profile_key": spec.profile_key,
                "lane": spec.lane,
                "title": spec.title,
                "voice": spec.voice,
                "role_summary": spec.role_summary,
                "owns": list(spec.owns),
                "tools_allowed": list(spec.tools_allowed),
                "skills_installed": installed_skills,
                "skill_count": len(installed_skills),
                "artifact_types": list(spec.artifact_types),
                "verification_method": spec.verification_method,
                "closure_rule": spec.closure_rule,
                "accent": spec.accent,
                "avatar_path": spec.avatar_path,
                "status": str(runtime.get("gateway_state") or ("active" if profile.get("api_server_live") else "offline")),
                "live": bool(runtime.get("live") or profile.get("api_server_live")),
                "connected_platforms": list(runtime.get("connected_platforms") or []),
                "session_count": _active_session_count(profile),
                "memory": _memory_summary(root, agent_slug),
                "profile_label": str(profile.get("label") or spec.title),
                "workspace_root": str(profile.get("workspace_root") or ""),
                "api_server_live": bool(profile.get("api_server_live")),
                "docs": {
                    "identity": _agent_doc_path(root, spec.character_name, "identity.md"),
                    "system_prompt": _agent_doc_path(root, spec.character_name, "system_prompt.md"),
                    "tools": _agent_doc_path(root, spec.character_name, "tools.md"),
                    "artifact_contracts": _agent_doc_path(root, spec.character_name, "artifact_contracts.md"),
                    "verification_checklist": _agent_doc_path(root, spec.character_name, "verification_checklist.md"),
                    "memory": str(agent_root(root) / spec.character_name.lower() / "memory"),
                    "examples": str(agent_root(root) / spec.character_name.lower() / "examples"),
                },
            }
        )
    return registry


def character_name_for_lane(lane: str) -> str:
    normalized = str(lane or "").strip()
    for spec in AGENT_SPECS:
        if spec.profile_key == normalized or spec.lane == normalized:
            return spec.character_name
    return normalized or "Unassigned"
