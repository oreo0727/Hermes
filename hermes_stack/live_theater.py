"""Live agent theater snapshot for the operator portal."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hermes_stack.agents import AGENT_SPECS
from hermes_stack.state_store import list_cognitive_records, repo_root


def _first(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def _confidence(*values: object) -> float:
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    if not numeric:
        return 0.5
    return round(max(0.0, min(1.0, sum(numeric) / len(numeric))), 2)


def build_live_theater(root_dir: str | Path | None = None) -> list[dict[str, Any]]:
    root = repo_root(root_dir)
    recent_decision = _first(list_cognitive_records(root, "autonomy_decisions", limit=1))
    rows: list[dict[str, Any]] = []

    for spec in AGENT_SPECS:
        slug = spec.character_name.lower()
        activation = _first(list_cognitive_records(root, "activations", agent_slug=slug, limit=1))
        reflection = _first(list_cognitive_records(root, "reflections", agent_slug=slug, limit=1))
        evolution = _first(list_cognitive_records(root, "skill_evolutions", agent_slug=slug, limit=1))
        thought = str(activation.get("query") or reflection.get("title") or spec.role_summary).strip()
        learning = str(evolution.get("recommendation") or reflection.get("content") or spec.closure_rule).strip()
        confidence = _confidence(activation.get("confidence"), evolution.get("confidence"), recent_decision.get("confidence"))
        rows.append(
            {
                "agent_slug": slug,
                "character_name": spec.character_name,
                "profile_key": spec.profile_key,
                "title": spec.title,
                "avatar_path": spec.avatar_path,
                "accent": spec.accent,
                "status": "watching",
                "current_thought": thought[:220],
                "working_on": spec.owns[0],
                "learning": learning[:240],
                "confidence": confidence,
                "next_move": str(recent_decision.get("decision") or activation.get("chosen_action") or "observe_and_update"),
                "proof_gate": spec.verification_method,
            }
        )
    return rows
