"""Confidence-gated autonomy decisions for Hermes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib

from hermes_stack.cognitive_kernel import activate_cognition
from hermes_stack.state_store import repo_root, upsert_cognitive_record


RISK_WEIGHTS = {
    "low": 0.08,
    "medium": 0.22,
    "high": 0.42,
    "critical": 0.62,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(part or "").strip() for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_risk(risk: str) -> str:
    normalized = str(risk or "medium").strip().lower()
    return normalized if normalized in RISK_WEIGHTS else "medium"


def decide_autonomy(
    root_dir: str | Path | None,
    *,
    objective: str,
    project_id: str = "",
    risk: str = "medium",
    confidence: float | None = None,
) -> dict[str, Any]:
    root = repo_root(root_dir)
    clean_objective = " ".join(str(objective or "").split())
    if not clean_objective:
        raise ValueError("objective is required")

    normalized_risk = _normalize_risk(risk)
    activation = activate_cognition(
        root,
        query=clean_objective,
        agent_slug="sheldon",
        project_id=project_id,
        limit=6,
    )
    activation_confidence = float(activation.get("confidence") or 0.0)
    base_confidence = activation_confidence if confidence is None else max(0.0, min(1.0, float(confidence)))
    adjusted_confidence = max(0.0, min(1.0, base_confidence - RISK_WEIGHTS[normalized_risk]))

    reasons: list[str] = [
        f"activation_confidence={activation_confidence:.2f}",
        f"risk={normalized_risk}",
        f"adjusted_confidence={adjusted_confidence:.2f}",
    ]
    if normalized_risk in {"high", "critical"}:
        decision = "ask_operator"
        reasons.append("high-risk work requires explicit operator approval")
    elif adjusted_confidence >= 0.72:
        decision = "auto_execute"
        reasons.append("confidence clears low-risk autonomy threshold")
    elif adjusted_confidence >= 0.46:
        decision = "council_review"
        reasons.append("confidence is workable but needs multi-agent review")
    else:
        decision = "ask_operator"
        reasons.append("confidence is below autonomous execution threshold")

    record = {
        "decision_id": f"autonomy:{_stable_id(project_id, clean_objective, normalized_risk, _now()[:13])}",
        "project_id": project_id,
        "objective": clean_objective,
        "risk": normalized_risk,
        "confidence": adjusted_confidence,
        "decision": decision,
        "reasons": reasons,
        "payload": {
            "source": "confidence_gated_autonomy",
            "base_confidence": base_confidence,
            "activation_id": activation.get("activation_id"),
            "chosen_action": activation.get("chosen_action"),
            "decided_at": _now(),
        },
    }
    return upsert_cognitive_record(root, "autonomy_decisions", record)
