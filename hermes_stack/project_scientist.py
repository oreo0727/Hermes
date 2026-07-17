"""Autonomous experiment proposal loop for Hermes projects."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib

from hermes_stack.projects import discover_projects
from hermes_stack.state_store import list_cognitive_records, repo_root, upsert_cognitive_record


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(part or "").strip() for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _experiment(
    *,
    project_id: str,
    hypothesis: str,
    metric: str,
    risk: str,
    confidence: float,
    source: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "experiment_id": f"experiment:{_stable_id(project_id, hypothesis, metric)}",
        "project_id": project_id,
        "hypothesis": hypothesis,
        "metric": metric,
        "status": "proposed",
        "risk": risk,
        "confidence": confidence,
        "result": {},
        "payload": {
            "source": source,
            "proposed_at": _now(),
            **(payload or {}),
        },
    }


def propose_experiments(root_dir: str | Path | None = None, *, limit: int = 8) -> list[dict[str, Any]]:
    root = repo_root(root_dir)
    projects = discover_projects(root)
    recent_activations = list_cognitive_records(root, "activations", limit=12)
    experiments: list[dict[str, Any]] = []

    for project in projects:
        project_id = str(project.get("project_id") or "").strip()
        if not project_id:
            continue
        title = str(project.get("title") or project_id)
        blocked = [str(item).strip() for item in project.get("blocked") or [] if str(item).strip()]
        done = [str(item).strip() for item in project.get("done") or [] if str(item).strip()]
        status = str(project.get("status") or "active").strip()

        if blocked:
            experiments.append(
                _experiment(
                    project_id=project_id,
                    hypothesis=f"If Sheldon isolates the first blocker for {title}, the project can regain a concrete next move.",
                    metric="blocked_count decreases or tracking.next changes after the next operator pass",
                    risk="low",
                    confidence=0.78,
                    source="blocked_project_scan",
                    payload={"blocked": blocked[:3], "status": status},
                )
            )
        if not done:
            experiments.append(
                _experiment(
                    project_id=project_id,
                    hypothesis=f"If {title} gets a proof target before execution, closure claims will become more reliable.",
                    metric="project tracking.done gains a concrete artifact or verification note",
                    risk="low",
                    confidence=0.72,
                    source="proof_gap_scan",
                    payload={"status": status},
                )
            )
        if str(project.get("primary_artifact") or "").strip() == "":
            experiments.append(
                _experiment(
                    project_id=project_id,
                    hypothesis=f"If {title} names one primary artifact, routing drift will drop for specialist work.",
                    metric="control.primary_artifact is populated and future work orders reference it",
                    risk="medium",
                    confidence=0.66,
                    source="artifact_anchor_scan",
                    payload={"specialists": list(project.get("specialists") or [])},
                )
            )

    activation_text = " ".join(str(row.get("query") or "") for row in recent_activations).lower()
    if any(token in activation_text for token in ("chat", "slow", "portal", "gateway", "status")):
        experiments.append(
            _experiment(
                project_id="",
                hypothesis="If quick portal questions use the fast cognitive router, Sheldon feels present without sacrificing deep execution quality.",
                metric="safe portal chat responses return via fast_path while heavy requests still escalate",
                risk="low",
                confidence=0.84,
                source="activation_pattern_scan",
                payload={"recent_activation_count": len(recent_activations)},
            )
        )

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for experiment in experiments:
        experiment_id = str(experiment.get("experiment_id") or "")
        if experiment_id in seen:
            continue
        deduped.append(experiment)
        seen.add(experiment_id)
        if len(deduped) >= max(1, limit):
            break
    return deduped


def run_experiment_cycle(root_dir: str | Path | None = None, *, limit: int = 8) -> dict[str, Any]:
    root = repo_root(root_dir)
    proposed = propose_experiments(root, limit=limit)
    persisted = [upsert_cognitive_record(root, "experiments", row) for row in proposed]
    return {
        "generated_at": _now(),
        "proposed_count": len(proposed),
        "persisted_count": len(persisted),
        "experiments": persisted,
    }
