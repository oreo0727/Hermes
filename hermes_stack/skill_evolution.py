"""Condense experiment memory into agent skill evolution records."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib

from hermes_stack.agents import AGENT_SPECS
from hermes_stack.state_store import list_cognitive_records, repo_root, upsert_cognitive_record


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(part or "").strip() for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _agent_focus(agent_slug: str) -> tuple[str, str]:
    mapping = {
        "sheldon": (
            "operator reflex routing",
            "Prefer fast local status/routing answers, but escalate build/fix work to deep execution.",
        ),
        "penny": (
            "creative proof sensitivity",
            "Turn visual/creative experiments into explicit artifact-readiness checks before closure.",
        ),
        "raj": (
            "portal and integration instrumentation",
            "Use experiment metrics to make portal/backend changes measurable before declaring success.",
        ),
        "leonard": (
            "runtime proof gates",
            "Convert playable/build experiments into visible runtime or export verification gates.",
        ),
    }
    return mapping.get(agent_slug, ("general learning", "Convert experiment outcomes into a reusable proof habit."))


def _evolution_record(agent_slug: str, experiments: list[dict[str, Any]]) -> dict[str, Any]:
    skill_area, recommendation = _agent_focus(agent_slug)
    evidence_bits = [
        str(row.get("hypothesis") or "").strip()
        for row in experiments[:4]
        if str(row.get("hypothesis") or "").strip()
    ]
    evidence = " | ".join(evidence_bits) or "No experiments available yet."
    confidence = min(0.92, 0.58 + (0.07 * len(evidence_bits)))
    return {
        "evolution_id": f"evolution:{agent_slug}:{_stable_id(skill_area, evidence)}",
        "agent_slug": agent_slug,
        "skill_area": skill_area,
        "evidence": evidence,
        "recommendation": recommendation,
        "confidence": confidence,
        "payload": {
            "source": "experiment_memory_consolidation",
            "experiment_ids": [row.get("experiment_id") for row in experiments[:6]],
            "consolidated_at": _now(),
        },
    }


def _reflection_from_evolution(evolution: dict[str, Any]) -> dict[str, Any]:
    agent_slug = str(evolution.get("agent_slug") or "")
    skill_area = str(evolution.get("skill_area") or "")
    return {
        "reflection_id": f"reflection:{agent_slug}:skill-evolution:{_stable_id(skill_area, evolution.get('recommendation'))}",
        "agent_slug": agent_slug,
        "project_id": "",
        "title": f"{agent_slug.title()} skill evolution: {skill_area}",
        "content": str(evolution.get("recommendation") or ""),
        "lessons": [
            "experiments should alter future routing, verification, or closure behavior",
            "preserve the agent voice while making proof requirements sharper",
        ],
        "payload": {
            "source": "skill_evolution",
            "evolution_id": evolution.get("evolution_id"),
        },
    }


def consolidate_experiment_memory(root_dir: str | Path | None = None) -> dict[str, Any]:
    root = repo_root(root_dir)
    experiments = list_cognitive_records(root, "experiments", limit=80)
    persisted_evolutions: list[dict[str, Any]] = []
    persisted_reflections: list[dict[str, Any]] = []

    for spec in AGENT_SPECS:
        slug = spec.character_name.lower()
        evolution = _evolution_record(slug, experiments)
        persisted = upsert_cognitive_record(root, "skill_evolutions", evolution)
        persisted_evolutions.append(persisted)
        persisted_reflections.append(upsert_cognitive_record(root, "reflections", _reflection_from_evolution(persisted)))

    return {
        "generated_at": _now(),
        "experiment_count": len(experiments),
        "evolution_count": len(persisted_evolutions),
        "reflection_count": len(persisted_reflections),
        "skill_evolutions": persisted_evolutions,
    }
