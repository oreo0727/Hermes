"""Shared orchestration helpers for Hermes runs, dispatches, and monitoring."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re


QUALITY_GATE_HANDOFF_PHRASES = (
    "reply with approvals",
    "paste the error",
    "send a screenshot",
    "send a quick screenshot",
    "send a quick snap",
    "please do a hard refresh",
    "hard refresh and let me know",
    "if you want me to",
    "if you'd like me to",
    "what you should see now",
    "what you should see",
    "your call",
    "on your ok",
)
QUALITY_GATE_APPROVAL_THEATER_PHRASES = (
    "pending your approval",
    "requesting approval",
    "approve copying",
    "approve? yes/no",
    "approve? yes / no",
    "on your go",
    "on your ok, i'll",
    "after your quick thumbs-up",
    "reply \"proceed",
    "reply 'proceed",
    "once you confirm",
    "if approved",
)
QUALITY_GATE_INDECISION_PHRASES = (
    "i could either",
    "i can either",
    "i might just",
    "i think i might",
    "leave it as it is",
    "consider restarting",
)
QUALITY_GATE_EVIDENCE_MARKERS = (
    "implemented",
    "verified",
    "assumed",
    "target artifact",
    "checks run",
    "failing checks",
    "next unblocker",
)
QUALITY_GATE_VISUAL_SUCCESS_PHRASES = (
    "sprites are live",
    "your sprites are live",
    "using your sprites",
    "using the provided sprites",
    "your art is live",
    "rendering from your pngs",
    "rendering directly from your loose pngs",
)
QUALITY_GATE_VISUAL_HINTS = (
    "screenshot",
    "capture",
    "image",
    "visual",
    "sprite",
    "sprites",
    "render",
    "renderer",
    "hud",
    "ui",
    "maze",
    "game",
    "hero",
    "enemy",
    "portal",
    "trap",
    "item",
)
QUALITY_GATE_VISUAL_ROLE_HINTS = (
    "hero",
    "enemy",
    "enemies",
    "portal",
    "trap",
    "traps",
    "item",
    "items",
    "hud",
    "floor",
    "floors",
    "wall",
    "walls",
)
QUALITY_GATE_VISUAL_PROOF_PHRASES = (
    "visible",
    "visibly",
    "on screen",
    "shows",
    "showing",
    "drawn from",
    "rendered from",
    "renders from",
    "rendering from",
    "placeholder-free",
    "no placeholders",
)
QUALITY_GATE_VISUAL_CONTRADICTION_PHRASES = (
    "still finishing",
    "finishing the pass",
    "i'm finishing the pass",
    "if any specific role still",
    "if any role still",
    "if anything still",
    "still shows a letter",
    "stops falling back",
)
QUALITY_GATE_SUCCESS_PATTERN = re.compile(
    r"\b(fixed|resolved|complete|completed|shipped|verified|playable|working now|stable now|done)\b",
    re.IGNORECASE,
)
JSON_BLOCK_PATTERN = re.compile(r"```json\s*(\{.*?\})\s*```", re.IGNORECASE | re.DOTALL)
PATH_TOKEN_PATTERN = re.compile(
    r"(?:/home/[^\s,]+|https?://[^\s,]+|res://[^\s,]+|[A-Za-z0-9_./-]+\.(?:tscn|gd|js|html|css|json|md|zip|wasm))"
)
DELIVERY_LANE_ORDER = ("operator", "creative-dev", "game-dev", "app-dev")
LANE_LABELS = {
    "operator": "Lead",
    "creative-dev": "Creative",
    "game-dev": "Game Dev",
    "app-dev": "App Dev",
}
LANE_STAGE_GUIDANCE = {
    "operator": "Own scope, freeze the delivery target, and keep the handoffs honest.",
    "creative-dev": "Define the creative target, vision guardrails, and artifact acceptance language before implementation drifts.",
    "game-dev": "Own the playable build path and converge the actual game implementation on the chosen target artifact.",
    "app-dev": "Own the app, tooling, portal, and review-loop support needed to make the chosen artifact reviewable and repeatable.",
}
RESULT_ACTION_CHOICES = {
    "direct_execute",
    "dispatch_specialist",
    "close_slice",
    "update_project",
    "mark_blocked",
    "revise_dispatch",
    "promote_artifact",
    "archive_or_park",
    "request_decision",
    "escalate",
}
RESULT_CLOSURE_CHOICES = {
    "not_closing",
    "ready_to_close",
    "blocked",
    "needs_revision",
}
RESULT_PROOF_CHOICES = {
    "none",
    "claimed",
    "partial",
    "verified",
}
RESULT_VALID_LANES = {"operator", "creative-dev", "game-dev", "app-dev"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, ValueError, OSError):
            return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def minutes_since(value: object, *, now: datetime | None = None) -> float | None:
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    current = now or datetime.now(timezone.utc)
    return max(0.0, (current - parsed).total_seconds() / 60.0)


def contains_any(text: object, needles: tuple[str, ...]) -> bool:
    haystack = str(text or "").lower()
    return any(needle in haystack for needle in needles)


def _looks_like_visual_work(text: object) -> bool:
    return contains_any(text, QUALITY_GATE_VISUAL_HINTS)


def _has_visual_capture_reference(text: object) -> bool:
    haystack = str(text or "").lower()
    return "media:" in haystack or "screenshot" in haystack or "capture" in haystack


def _has_visual_role_proof(text: object) -> bool:
    return contains_any(text, QUALITY_GATE_VISUAL_ROLE_HINTS) and contains_any(
        text, QUALITY_GATE_VISUAL_PROOF_PHRASES
    )


def clip_text(value: object, limit: int = 320) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit - 1].rstrip()}…"


def _ordered_lane_rows(lanes: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for lane in DELIVERY_LANE_ORDER:
        if lane in lanes and lane not in seen:
            ordered.append(lane)
            seen.add(lane)
    for lane in lanes:
        if lane not in seen:
            ordered.append(lane)
            seen.add(lane)
    return ordered


def _objective_lane_hints(objective: str) -> list[str]:
    lowered = objective.lower()
    hinted: list[str] = []
    if any(
        token in lowered
        for token in (
            "vision",
            "visual",
            "style",
            "tone",
            "art",
            "narrative",
            "story",
            "ui",
            "hud",
            "feel",
        )
    ):
        hinted.append("creative-dev")
    if any(
        token in lowered
        for token in (
            "game",
            "maze",
            "playable",
            "enemy",
            "trap",
            "powerup",
            "power-up",
            "godot",
            "renderer",
            "movement",
            "build",
        )
    ):
        hinted.append("game-dev")
    if any(
        token in lowered
        for token in (
            "portal",
            "operator",
            "app",
            "tooling",
            "review loop",
            "review",
            "status",
            "service",
            "deploy",
            "api",
        )
    ):
        hinted.append("app-dev")
    return _ordered_lane_rows(hinted)


def derive_lane_sequence(
    *,
    profile_key: str,
    project: dict[str, object] | None,
    objective: str,
) -> list[str]:
    lanes: list[str] = []
    control = project.get("control") if isinstance(project, dict) and isinstance(project.get("control"), dict) else {}
    controlled_sequence = control.get("lane_sequence") if isinstance(control, dict) else ()
    explicit_sequence: list[str] = []
    if isinstance(controlled_sequence, list):
        explicit_sequence = [str(item).strip() for item in controlled_sequence if str(item).strip()]
        lanes.extend(explicit_sequence)
    if project:
        lanes.extend(str(item).strip() for item in project.get("specialists") or [] if str(item).strip())
    lanes.extend(_objective_lane_hints(objective))
    if profile_key == "operator" or project:
        lanes.insert(0, "operator")
    elif profile_key:
        lanes.append(profile_key)
    if profile_key and profile_key not in lanes:
        lanes.append(profile_key)
    if explicit_sequence:
        ordered: list[str] = []
        seen: set[str] = set()
        for lane in lanes:
            if lane and lane not in seen:
                ordered.append(lane)
                seen.add(lane)
        if "operator" in seen and ordered[0] != "operator":
            ordered = ["operator", *[lane for lane in ordered if lane != "operator"]]
        return ordered
    return _ordered_lane_rows(lanes)


def build_delivery_model(
    *,
    profile_key: str,
    project: dict[str, object] | None,
    objective: str,
) -> dict[str, object]:
    control = project.get("control") if isinstance(project, dict) and isinstance(project.get("control"), dict) else {}
    sequence = derive_lane_sequence(profile_key=profile_key, project=project, objective=objective)
    active_lane = profile_key if profile_key in sequence else (sequence[0] if sequence else profile_key)
    lead_lane = "operator" if "operator" in sequence else (sequence[0] if sequence else profile_key)
    primary_lane = str(control.get("primary_lane") or "").strip()
    if primary_lane and primary_lane not in sequence:
        primary_lane = ""
    if not primary_lane:
        non_operator = [lane for lane in sequence if lane != lead_lane]
        primary_lane = non_operator[0] if non_operator else lead_lane
    active_index = sequence.index(active_lane) if active_lane in sequence else 0
    next_lane = sequence[active_index + 1] if active_index + 1 < len(sequence) else ""
    specialist_sequence = [lane for lane in sequence if lane != lead_lane]
    handoff_contract = [
        "freeze one primary delivery target before downstream implementation expands scope",
        "treat creative-dev as the vision and acceptance guardrail for downstream lanes",
        "treat game-dev as the owner of the playable implementation path once the vision is frozen",
        "treat app-dev as the owner of portal, tooling, packaging, and review-loop support after the build path is clear",
        "require each lane to leave a concrete handoff for the next lane instead of sending the operator back into open-ended review",
    ]
    return {
        "strategy_key": "lead-creative-game-app",
        "strategy_label": "Lead -> Creative -> Game Dev -> App Dev",
        "lead_lane": lead_lane,
        "active_lane": active_lane,
        "primary_lane": primary_lane,
        "next_lane": next_lane,
        "lane_sequence": sequence,
        "specialist_sequence": specialist_sequence,
        "control_mode": str(control.get("control_mode") or "orchestrated").strip() or "orchestrated",
        "delivery_target": str(control.get("delivery_target") or "").strip(),
        "primary_artifact": str(control.get("primary_artifact") or "").strip(),
        "strict_dispatch": bool(control.get("strict_dispatch", False)),
        "acceptance": list(control.get("acceptance") or []) if isinstance(control.get("acceptance"), list) else [],
        "capability_gaps": list(control.get("capability_gaps") or []) if isinstance(control.get("capability_gaps"), list) else [],
        "stage_guidance": {
            lane: LANE_STAGE_GUIDANCE.get(lane, "")
            for lane in sequence
        },
        "handoff_contract": handoff_contract,
    }


def latest_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content") or "").strip()
    return ""


def _sanitize_line(value: str) -> str:
    text = re.sub(r"\s+", " ", value.strip())
    return text.strip("-* ").strip()


def _normalize_list(values: object) -> list[str]:
    if isinstance(values, list):
        rows = [_sanitize_line(str(item or "")) for item in values]
        return [row for row in rows if row]
    if isinstance(values, str):
        rows: list[str] = []
        for raw_line in values.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith(("- ", "* ")):
                rows.append(_sanitize_line(stripped[2:]))
            elif re.match(r"^\d+\.\s+", stripped):
                rows.append(_sanitize_line(re.sub(r"^\d+\.\s+", "", stripped)))
            else:
                rows.append(_sanitize_line(stripped))
        return [row for row in rows if row]
    return []


def extract_operator_request_text(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""

    if cleaned.startswith("[The user attached image"):
        if "\n\n" not in cleaned:
            return ""
        cleaned = re.sub(
            r"(?is)^\s*(?:\[The user attached image.*?\]\s*)+",
            "",
            cleaned,
        ).strip()

    if cleaned.startswith("Project context\nProject:") and "User request" not in cleaned and "Operator request" not in cleaned:
        return ""

    cleaned = re.sub(
        r"(?is)^\s*(?:\[The user attached image.*?\]\s*)+",
        "",
        cleaned,
    ).strip()
    if "\n\nUser request\n" in cleaned:
        cleaned = cleaned.split("\n\nUser request\n", 1)[1].strip()
    elif "Operator request:\n" in cleaned:
        cleaned = cleaned.split("Operator request:\n", 1)[1].strip()
    return cleaned


def _extract_named_section(text: str, names: tuple[str, ...]) -> tuple[str, bool]:
    if not text.strip():
        return "", False

    all_headers = (
        "Objective",
        "Summary",
        "Implemented",
        "What changed",
        "Actions taken",
        "Artifacts",
        "Artifacts created",
        "Verified",
        "Checks run",
        "Assumed",
        "Blocked",
        "Approvals needed",
        "Current risk",
        "Risks",
        "Next checkpoint",
        "Next",
        "Next moves",
        "Recommended next step",
        "Operator update",
        "What advanced",
    )
    for name in names:
        pattern = re.compile(
            rf"(?ims)^\s*(?:[#>*-]+\s*)?{re.escape(name)}\s*:?\s*(.*?)"
            rf"(?=^\s*(?:[#>*-]+\s*)?(?:{'|'.join(re.escape(item) for item in all_headers)})\b|\Z)"
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip(), True
    return "", False


def _section_items(section_text: str) -> list[str]:
    items = _normalize_list(section_text)
    if items:
        return items
    compact = " ".join(line.strip() for line in section_text.splitlines() if line.strip())
    return [compact] if compact else []


def _first_meaningful_line(text: str) -> str:
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", "-", "*")):
            stripped = stripped.lstrip("#*- ").strip()
        if stripped:
            return stripped
    return ""


def _strip_json_block(output: str) -> str:
    return JSON_BLOCK_PATTERN.sub("", output).strip()


def _extract_json_block(output: str) -> dict[str, object] | None:
    match = JSON_BLOCK_PATTERN.search(output)
    if match:
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            return payload

    cleaned = output.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _dedupe_list(values: list[str]) -> list[str]:
    rows: list[str] = []
    seen: set[str] = set()
    for item in values:
        normalized = item.strip().lower()
        if not normalized or normalized in seen:
            continue
        rows.append(item.strip())
        seen.add(normalized)
    return rows


def _find_artifacts(text: str) -> list[str]:
    return _dedupe_list([match.group(0) for match in PATH_TOKEN_PATTERN.finditer(text or "")])


def coerce_structured_result(payload: dict[str, object]) -> dict[str, object]:
    result = {
        "schema_version": str(payload.get("schema_version") or "1"),
        "summary": str(payload.get("summary") or "").strip(),
        "implemented": _normalize_list(payload.get("implemented")),
        "verified": _normalize_list(payload.get("verified")),
        "assumed": _normalize_list(payload.get("assumed")),
        "blocked": _normalize_list(payload.get("blocked")),
        "risks": _normalize_list(payload.get("risks")),
        "next_actions": _normalize_list(payload.get("next_actions")),
        "artifacts": _dedupe_list(_normalize_list(payload.get("artifacts"))),
    }
    action_taken = str(payload.get("action_taken") or "").strip().lower()
    if action_taken in RESULT_ACTION_CHOICES:
        result["action_taken"] = action_taken
    else:
        result["action_taken"] = ""

    focus_slice = str(payload.get("focus_slice") or "").strip()
    result["focus_slice"] = focus_slice

    owner_lane = str(payload.get("owner_lane") or "").strip().lower()
    if owner_lane in RESULT_VALID_LANES:
        result["owner_lane"] = owner_lane
    else:
        result["owner_lane"] = ""

    proof_status = str(payload.get("proof_status") or "").strip().lower()
    if proof_status in RESULT_PROOF_CHOICES:
        result["proof_status"] = proof_status
    else:
        result["proof_status"] = "none"

    closure_decision = str(payload.get("closure_decision") or "").strip().lower()
    if closure_decision in RESULT_CLOSURE_CHOICES:
        result["closure_decision"] = closure_decision
    else:
        result["closure_decision"] = "not_closing"

    dispatches = payload.get("dispatches")
    dispatch_rows: list[str] = []
    if isinstance(dispatches, list):
        dispatch_rows = _dedupe_list(_normalize_list(dispatches))
    result["dispatches"] = dispatch_rows[:8]

    project_update = payload.get("project_update")
    normalized_project_update: dict[str, object] = {}
    if isinstance(project_update, dict):
        for key in ("status", "now", "next", "delivery_target", "primary_artifact", "primary_lane"):
            value = str(project_update.get(key) or "").strip()
            if value:
                normalized_project_update[key] = value
        blocked = project_update.get("blocked")
        if isinstance(blocked, list):
            normalized_project_update["blocked"] = _normalize_list(blocked)[:6]
        done = project_update.get("done")
        if isinstance(done, list):
            normalized_project_update["done"] = _normalize_list(done)[:6]
    result["project_update"] = normalized_project_update

    handoff_needed = payload.get("handoff_needed")
    if isinstance(handoff_needed, bool):
        result["handoff_needed"] = handoff_needed
    else:
        result["handoff_needed"] = False
    if not result["artifacts"]:
        result["artifacts"] = _find_artifacts(" ".join(result["implemented"] + result["verified"] + [result["summary"]]))
    return result


def extract_structured_result(output: str) -> dict[str, object]:
    payload = _extract_json_block(output)
    if payload:
        return coerce_structured_result(payload)

    clean_output = output.strip()
    implemented_section, implemented_found = _extract_named_section(
        clean_output,
        ("Implemented", "What changed", "Actions taken", "Work completed", "What I changed", "Moves just completed"),
    )
    verified_section, verified_found = _extract_named_section(
        clean_output,
        ("Verified", "Checks run", "Verification I ran", "What I verified"),
    )
    assumed_section, assumed_found = _extract_named_section(clean_output, ("Assumed", "Assumptions"))
    blocked_section, blocked_found = _extract_named_section(clean_output, ("Blocked", "Approvals needed"))
    risks_section, risks_found = _extract_named_section(clean_output, ("Risks", "Current risk"))
    next_section, next_found = _extract_named_section(
        clean_output,
        ("Next checkpoint", "Next", "Next moves", "Recommended next step"),
    )
    artifacts_section, artifacts_found = _extract_named_section(clean_output, ("Artifacts", "Artifacts created", "Files touched"))
    summary_line = _first_meaningful_line(_strip_json_block(clean_output))

    structured = {
        "schema_version": "1",
        "summary": summary_line,
        "implemented": _section_items(implemented_section) if implemented_found else [],
        "verified": _section_items(verified_section) if verified_found else [],
        "assumed": _section_items(assumed_section) if assumed_found else [],
        "blocked": _section_items(blocked_section) if blocked_found else [],
        "risks": _section_items(risks_section) if risks_found else [],
        "next_actions": _section_items(next_section) if next_found else [],
        "artifacts": _section_items(artifacts_section) if artifacts_found else _find_artifacts(clean_output),
    }
    structured["handoff_needed"] = contains_any(clean_output, QUALITY_GATE_HANDOFF_PHRASES)
    return coerce_structured_result(structured)


def parse_assistant_output(output: str) -> tuple[str, dict[str, object]]:
    clean_display = _strip_json_block(str(output or "").strip())
    structured = extract_structured_result(output)
    if not structured.get("summary"):
        structured["summary"] = _first_meaningful_line(clean_display)
    return clean_display, structured


def execution_quality_issues(output: str) -> list[str]:
    text = str(output or "").strip()
    if not text:
        return ["No output was produced."]

    display_text, structured = parse_assistant_output(text)
    lowered = display_text.lower()
    issues: list[str] = []

    if any(phrase in lowered for phrase in QUALITY_GATE_HANDOFF_PHRASES):
        issues.append("The response still hands execution or verification back to the operator.")

    if any(phrase in lowered for phrase in QUALITY_GATE_APPROVAL_THEATER_PHRASES):
        issues.append("The response asks for approval before taking a safe next action.")

    if any(phrase in lowered for phrase in QUALITY_GATE_INDECISION_PHRASES):
        issues.append("The response stays indecisive instead of committing to the next action.")

    success_claimed = bool(QUALITY_GATE_SUCCESS_PATTERN.search(display_text)) or contains_any(
        lowered, QUALITY_GATE_VISUAL_SUCCESS_PHRASES
    )

    if success_claimed:
        evidence_hits = sum(1 for marker in QUALITY_GATE_EVIDENCE_MARKERS if marker in lowered)
        verified = structured.get("verified") if isinstance(structured.get("verified"), list) else []
        artifacts = structured.get("artifacts") if isinstance(structured.get("artifacts"), list) else []
        implemented = structured.get("implemented") if isinstance(structured.get("implemented"), list) else []
        if evidence_hits < 2 and (not verified or not (artifacts or implemented)):
            issues.append("The response claims success without enough artifact-specific verification evidence.")

        if _looks_like_visual_work(lowered):
            if not _has_visual_capture_reference(lowered):
                issues.append("The response claims visual success without citing a screenshot or capture.")
            if not _has_visual_role_proof(lowered):
                issues.append("The response claims visual success without naming what is visibly on screen.")
            if contains_any(lowered, QUALITY_GATE_VISUAL_CONTRADICTION_PHRASES):
                issues.append("The response contradicts its own visual success claim by admitting the pass is still incomplete.")
    return issues


def _acceptance_item_addressed(item: str, evidence_lines: list[str]) -> bool:
    lowered_item = str(item or "").strip().lower()
    if not lowered_item:
        return True
    evidence = " ".join(str(line or "").strip().lower() for line in evidence_lines if str(line or "").strip())
    if not evidence:
        return False
    if "no placeholder" in lowered_item or "no placeholders" in lowered_item:
        return any(
            phrase in evidence
            for phrase in ("no placeholder", "no placeholders", "placeholder-free", "without placeholders")
        )
    if lowered_item in evidence:
        return True
    tokens = [token for token in re.findall(r"[a-z0-9]+", lowered_item) if len(token) >= 4]
    if not tokens:
        return lowered_item in evidence
    hits = sum(1 for token in tokens if token in evidence)
    return hits >= max(1, min(len(tokens), 2))


def supervisor_review(
    *,
    profile_key: str,
    project: dict[str, object] | None,
    output: str,
) -> dict[str, object]:
    display_text, structured = parse_assistant_output(output)
    issues = execution_quality_issues(output)
    critique = list(issues)

    control = project.get("control") if project and isinstance(project.get("control"), dict) else {}
    acceptance = list(control.get("acceptance") or []) if isinstance(control.get("acceptance"), list) else []
    evidence_lines: list[str] = [display_text]
    for key in ("summary",):
        value = structured.get(key)
        if value:
            evidence_lines.append(str(value))
    for key in ("implemented", "verified", "assumed", "artifacts"):
        value = structured.get(key)
        if isinstance(value, list):
            evidence_lines.extend(str(item) for item in value if str(item or "").strip())

    unmet_acceptance = [item for item in acceptance if not _acceptance_item_addressed(str(item), evidence_lines)]
    if unmet_acceptance:
        critique.append(
            "The response did not yet close these project acceptance targets: "
            + "; ".join(str(item) for item in unmet_acceptance[:4])
        )

    if bool(structured.get("handoff_needed")):
        critique.append("The response still ends in a handoff instead of closing the assigned lane.")

    blocked = structured.get("blocked") if isinstance(structured.get("blocked"), list) else []
    if blocked and not issues:
        critique.append(
            "The response is still blocked and needs a concrete repair attempt instead of a status-only handoff."
        )

    decision = "accept"
    if critique:
        decision = "revise"

    return {
        "decision": decision,
        "retryable": decision == "revise",
        "issues": issues,
        "critique": critique,
        "unmet_acceptance": unmet_acceptance,
        "summary": str(structured.get("summary") or "").strip(),
        "artifacts": structured.get("artifacts") if isinstance(structured.get("artifacts"), list) else [],
        "structured_result": structured,
        "profile_key": profile_key,
    }


def closure_gate_review(
    *,
    project: dict[str, object] | None,
    structured_result: dict[str, object],
    action_type: str,
) -> dict[str, object]:
    control = project.get("control") if project and isinstance(project.get("control"), dict) else {}
    acceptance = list(control.get("acceptance") or []) if isinstance(control.get("acceptance"), list) else []
    artifacts = structured_result.get("artifacts") if isinstance(structured_result.get("artifacts"), list) else []
    blocked = structured_result.get("blocked") if isinstance(structured_result.get("blocked"), list) else []
    handoff_needed = bool(structured_result.get("handoff_needed"))

    evidence_lines: list[str] = []
    for key in ("summary",):
        value = structured_result.get(key)
        if value:
            evidence_lines.append(str(value))
    for key in ("implemented", "verified", "assumed", "artifacts"):
        value = structured_result.get(key)
        if isinstance(value, list):
            evidence_lines.extend(str(item) for item in value if str(item or "").strip())

    unmet_acceptance = [item for item in acceptance if not _acceptance_item_addressed(str(item), evidence_lines)]
    reasons: list[str] = []
    if action_type == "close_slice":
        if not artifacts:
            reasons.append("Close-slice work did not return any artifact paths.")
        if blocked:
            reasons.append("Close-slice work still reports blockers.")
        if handoff_needed:
            reasons.append("Close-slice work still ends in a handoff.")
        if str(structured_result.get("closure_decision") or "not_closing") != "ready_to_close":
            reasons.append("Close-slice work did not explicitly declare ready_to_close.")
        if unmet_acceptance:
            reasons.append(
                "Close-slice work still misses acceptance targets: "
                + "; ".join(str(item) for item in unmet_acceptance[:4])
            )

    return {
        "ready": not reasons,
        "reasons": reasons,
        "unmet_acceptance": unmet_acceptance,
        "artifacts": artifacts,
        "blocked": blocked,
        "action_type": action_type,
    }


def result_contract_review(
    *,
    profile_key: str,
    work_order: dict[str, object] | None,
    structured_result: dict[str, object],
) -> dict[str, object]:
    work_order = work_order if isinstance(work_order, dict) else {}
    expected_action = str(work_order.get("action_type") or "").strip().lower()
    required_fields = [
        "summary",
        "implemented",
        "verified",
        "assumed",
        "blocked",
        "risks",
        "next_actions",
        "artifacts",
        "handoff_needed",
    ]
    if profile_key == "operator":
        required_fields.extend(("action_taken", "focus_slice", "owner_lane", "proof_status", "closure_decision"))

    missing: list[str] = []
    for field in required_fields:
        value = structured_result.get(field)
        if field == "handoff_needed":
            if not isinstance(value, bool):
                missing.append(field)
            continue
        if isinstance(value, list) and field in {"implemented", "verified", "assumed", "blocked", "risks", "next_actions", "artifacts"}:
            continue
        if str(value or "").strip():
            continue
        if field == "blocked":
            continue
        missing.append(field)

    reasons: list[str] = []
    if missing:
        reasons.append("Structured result is missing required contract fields: " + ", ".join(missing))

    action_taken = str(structured_result.get("action_taken") or "").strip().lower()
    if profile_key == "operator":
        if action_taken and action_taken not in RESULT_ACTION_CHOICES:
            reasons.append(f"Operator action_taken is invalid: {action_taken}")
        if expected_action and action_taken and action_taken not in {expected_action, "mark_blocked", "escalate"}:
            reasons.append(
                f"Operator action_taken {action_taken} does not match expected work-order action {expected_action}."
            )
        if expected_action == "dispatch_specialist":
            dispatches = structured_result.get("dispatches") if isinstance(structured_result.get("dispatches"), list) else []
            if action_taken == "dispatch_specialist" and not dispatches:
                reasons.append("Dispatch-specialist turn did not report any specialist dispatch identifiers or outcomes.")
        if expected_action == "close_slice" and str(structured_result.get("closure_decision") or "") != "ready_to_close":
            reasons.append("Close-slice turn did not explicitly report ready_to_close.")
        if not str(structured_result.get("focus_slice") or "").strip():
            reasons.append("Operator turn did not restate the active focus slice.")
        if str(structured_result.get("owner_lane") or "").strip() not in RESULT_VALID_LANES:
            reasons.append("Operator turn did not declare a valid owner_lane.")
        if str(structured_result.get("proof_status") or "").strip() not in RESULT_PROOF_CHOICES:
            reasons.append("Operator turn did not declare a valid proof_status.")

    return {
        "ready": not reasons,
        "reasons": reasons,
        "expected_action": expected_action,
        "action_taken": action_taken,
        "profile_key": profile_key,
        "required_fields": required_fields,
    }


def supervisor_revision_prompt(
    *,
    prior_prompt: str,
    review: dict[str, object],
    attempt_number: int,
    max_attempts: int,
) -> str:
    critique = review.get("critique") if isinstance(review.get("critique"), list) else []
    bullets = "\n".join(f"- {str(item).strip()}" for item in critique[:6] if str(item).strip())
    unmet_acceptance = review.get("unmet_acceptance") if isinstance(review.get("unmet_acceptance"), list) else []
    acceptance_block = ""
    if unmet_acceptance:
        acceptance_lines = "\n".join(f"- {str(item).strip()}" for item in unmet_acceptance[:6] if str(item).strip())
        acceptance_block = (
            "\nAcceptance still not satisfied:\n"
            f"{acceptance_lines}\n"
        )
    return (
        f"{prior_prompt.strip()}\n\n"
        f"Supervisor revision attempt {attempt_number}/{max_attempts}.\n"
        "Your previous result was reviewed and rejected. Do not restate the old result.\n"
        "Repair the work directly in your lane, then return with fresh evidence.\n"
        "Review findings:\n"
        f"{bullets or '- The previous result did not meet the lane acceptance bar.'}\n"
        f"{acceptance_block}"
        "Response requirements:\n"
        "- Say exactly what you changed in this retry.\n"
        "- Say exactly what you verified yourself in this retry.\n"
        "- If anything is still blocked, name the blocker and the attempted repair already made.\n"
        "- Do not hand the task back for operator review or approval.\n"
        "- End with the required JSON block."
    ).strip()


def project_keyword_score(project: dict[str, object], text: str) -> int:
    project_id = str(project.get("project_id") or "").strip().lower()
    title = str(project.get("title") or "").strip().lower()
    summary = str(project.get("summary") or "").strip().lower()
    haystack = text.lower()
    score = 0

    exact_phrases = {
        project_id,
        project_id.replace("-", " "),
        title,
    }
    if project_id == "aetherion-maze":
        exact_phrases.update(
            {
                "maze forest",
                "maze-forest",
                "narrative maze",
                "narrative-maze",
                "maze game",
                "html5 maze",
            }
        )
    for phrase in exact_phrases:
        if phrase and phrase in haystack:
            score += 4

    tokens = {
        token
        for token in (
            project_id.replace("-", " ").split()
            + title.replace("-", " ").split()
            + summary.replace("-", " ").split()
        )
        if len(token) >= 4
    }
    if project_id == "aetherion-maze":
        tokens.update(
            {
                "maze",
                "forest",
                "narrative",
                "canvas",
                "enemy",
                "enemies",
                "trap",
                "traps",
                "powerup",
                "power-ups",
                "renderer",
                "rendering",
                "hud",
                "gameplay",
            }
        )
    for token in tokens:
        if token and token in haystack:
            score += 1

    return score


def infer_project_id(
    projects: list[dict[str, object]],
    *,
    profile_key: str,
    explicit_project_id: str,
    messages: list[dict[str, str]],
) -> str:
    if explicit_project_id.strip():
        return explicit_project_id.strip()
    if profile_key != "operator":
        return ""

    latest_message = extract_operator_request_text(latest_user_message(messages)).lower()
    if not latest_message:
        return ""
    if not projects:
        return ""

    scored = [(project, project_keyword_score(project, latest_message)) for project in projects]
    scored.sort(key=lambda item: item[1], reverse=True)
    if scored and scored[0][1] > 0:
        return str(scored[0][0].get("project_id") or "")

    active_project = next(
        (
            project
            for project in projects
            if bool(((project.get("portfolio") or {}).get("active")))
        ),
        None,
    )
    if active_project is not None:
        return str(active_project.get("project_id") or "")

    if len(projects) == 1 and any(
        token in latest_message for token in ("maze", "forest", "narrative", "game", "gameplay", "renderer", "hud", "canvas")
    ):
        return str(projects[0].get("project_id") or "")

    return ""


def _recommended_lanes(profile_key: str, project: dict[str, object] | None, objective: str) -> list[str]:
    delivery_model = build_delivery_model(profile_key=profile_key, project=project, objective=objective)
    sequence = delivery_model.get("lane_sequence") if isinstance(delivery_model.get("lane_sequence"), list) else []
    active_lane = str(delivery_model.get("active_lane") or "")
    return [str(lane) for lane in sequence if str(lane) and str(lane) != active_lane]


def _expected_deliverables(profile_key: str, objective: str) -> list[str]:
    lowered = objective.lower()
    deliverables: list[str] = []
    if any(token in lowered for token in ("fix", "implement", "refactor", "feature", "code", "bug")):
        deliverables.append("code changes")
    if any(token in lowered for token in ("build", "export", "ship", "release")):
        deliverables.append("artifact or build output")
    if any(token in lowered for token in ("review", "audit", "investigate")):
        deliverables.append("findings and recommended next actions")
    if any(token in lowered for token in ("storyboard", "creative", "brief", "visual", "asset")):
        deliverables.append("creative package or direction")
    if any(token in lowered for token in ("sprite", "spritesheet", "sprite sheet", "atlas", "tileset", "asset pack", "asset board")):
        deliverables.append("asset readiness verdict before integration")
    if not deliverables:
        deliverables.append("concrete progress in the bound workspace")
    if profile_key == "operator":
        deliverables.append("project state updates when work materially advances")
    return _dedupe_list(deliverables)


def _verification_requirements(objective: str) -> list[str]:
    lowered = objective.lower()
    checks = ["separate implemented, verified, and assumed"]
    if "localhost" in lowered or "127.0.0.1" in lowered or "url" in lowered:
        checks.append("preflight referenced local URLs before relying on them")
    if any(token in lowered for token in ("fix", "build", "implement", "export", "ship", "release")):
        checks.append("run the smallest local verification possible before claiming success")
    if any(token in lowered for token in ("sprite", "spritesheet", "sprite sheet", "atlas", "tileset", "asset pack", "asset board")):
        checks.extend(
            [
                "classify each referenced art input as reference board, loose sprites, uniform grid sheet, atlas plus manifest, or unknown before integrating it",
                "if an image includes labels, section dividers, notes, or a presentation background, state that it is a reference board and not a build-ready runtime sheet",
                "do not claim sprite integration is complete until a machine-usable artifact exists such as loose transparent sprites, a uniform grid sheet with proven cell geometry, or an atlas with manifest",
            ]
        )
    if "storyboard" in lowered or ("reference" in lowered and any(token in lowered for token in ("visual", "image", "sample", "mood", "board"))):
        checks.extend(
            [
                "for reference-driven storyboard work, either produce image-grounded frames or explicitly report that the lane is blocked; do not substitute abstract diagrams and call them done",
                "state whether the delivered artifact is a blocking diagram, placeholder board, clean storyboard, or image-grounded redraw",
                "do not mark storyboard work review-ready if the output is still circles, boxes, icons, or other schematic placeholders instead of visibly rendered figures, props, and lighting beats",
            ]
        )
    return _dedupe_list(checks)


def _is_progress_update_request(objective: str) -> bool:
    lowered = objective.lower()
    if not lowered.strip():
        return False
    progress_phrases = (
        "how's",
        "hows",
        "how is",
        "status",
        "progress",
        "update",
        "going",
        "where are we",
        "where's",
        "what's the status",
        "whats the status",
    )
    return any(phrase in lowered for phrase in progress_phrases)


def _infer_action_type(*, profile_key: str, objective: str) -> str:
    lowered = objective.lower()
    if any(token in lowered for token in ("archive", "park this", "pause this", "deprioritize")):
        return "archive_or_park"
    if any(token in lowered for token in ("mark blocked", "this is blocked", "set blocked", "declare blocked")):
        return "mark_blocked"
    if any(token in lowered for token in ("promote", "use the raws", "promote raw", "promote artifact")):
        return "promote_artifact"
    if any(token in lowered for token in ("dispatch", "delegate", "route to", "hand off to")):
        return "dispatch_specialist"
    if any(token in lowered for token in ("close this", "mark done", "close the slice", "ship it", "review-ready")):
        return "close_slice"
    if any(token in lowered for token in ("revise", "retry", "rework", "fix the previous")):
        return "revise_dispatch"
    if any(token in lowered for token in ("which should", "what should", "decide between", "choose between")):
        return "request_decision"
    if profile_key == "operator":
        return "direct_execute"
    return "direct_execute"


def _slice_key(project: dict[str, object] | None, objective: str) -> str:
    control = project.get("control") if project and isinstance(project.get("control"), dict) else {}
    project_id = str(project.get("project_id") or "").strip() if project else ""
    delivery_target = str(control.get("delivery_target") or "").strip()
    primary_artifact = str(control.get("primary_artifact") or "").strip()
    objective_hint = extract_operator_request_text(objective) or objective
    slice_label = delivery_target or primary_artifact or objective_hint
    slug = re.sub(r"[^a-z0-9]+", "-", slice_label.lower()).strip("-")
    slug = slug[:96] or "general"
    return f"{project_id}:{slug}" if project_id else slug


def _dispatch_readiness(
    *,
    project: dict[str, object] | None,
    verification_required: list[str],
    expected_deliverables: list[str],
) -> dict[str, object]:
    control = project.get("control") if project and isinstance(project.get("control"), dict) else {}
    reasons: list[str] = []
    caution: list[str] = []

    if not expected_deliverables:
        reasons.append("No expected deliverables were defined for this work order.")
    if not verification_required:
        reasons.append("No verification plan was defined for this work order.")

    strict_dispatch = bool(control.get("strict_dispatch", False))
    delivery_target = str(control.get("delivery_target") or "").strip()
    primary_artifact = str(control.get("primary_artifact") or "").strip()
    acceptance = list(control.get("acceptance") or []) if isinstance(control.get("acceptance"), list) else []
    capability_gaps = list(control.get("capability_gaps") or []) if isinstance(control.get("capability_gaps"), list) else []

    if strict_dispatch and not delivery_target:
        reasons.append("Strict dispatch is enabled but the delivery target is not frozen.")
    if strict_dispatch and not primary_artifact:
        reasons.append("Strict dispatch is enabled but the primary artifact is not named.")
    if strict_dispatch and not acceptance:
        reasons.append("Strict dispatch is enabled but acceptance criteria are missing.")
    if capability_gaps:
        caution.append("Capability gaps are recorded for this project and should be acknowledged before closure.")

    ready = not reasons
    verdict = "ready" if ready else "needs-contract"
    if not ready and capability_gaps:
        verdict = "needs-contract-with-gaps"
    return {
        "ready": ready,
        "verdict": verdict,
        "reasons": reasons,
        "caution": caution,
        "strict_dispatch": strict_dispatch,
    }


def build_work_order(
    *,
    profile_key: str,
    project: dict[str, object] | None,
    messages: list[dict[str, str]],
    source: str,
) -> dict[str, object]:
    raw_objective = latest_user_message(messages)
    objective = extract_operator_request_text(raw_objective) or raw_objective
    delivery_model = build_delivery_model(profile_key=profile_key, project=project, objective=objective)
    expected_deliverables = _expected_deliverables(profile_key, objective)
    verification_required = _verification_requirements(objective)
    action_type = _infer_action_type(profile_key=profile_key, objective=objective)
    slice_key = _slice_key(project, objective)
    progress_update_request = bool(project) and _is_progress_update_request(objective)
    if progress_update_request:
        expected_deliverables = _dedupe_list(
            [
                "bound project progress update grounded in live artifacts",
                *expected_deliverables,
            ]
        )
        verification_required = _dedupe_list(
            [
                "for bound-project progress questions, inspect tracking.now, tracking.next, blocked state, and the named primary artifact or latest live run before answering",
                "do not pivot to device connectivity, adb, ssh, or fastboot as the main update unless the user explicitly asks about access or flashing readiness",
                *verification_required,
            ]
        )
    dispatch_readiness = _dispatch_readiness(
        project=project,
        verification_required=verification_required,
        expected_deliverables=expected_deliverables,
    )
    result = {
        "schema_version": "1",
        "created_at": utc_now(),
        "source": source,
        "profile_key": profile_key,
        "project_id": str(project.get("project_id") or "") if project else "",
        "project_title": str(project.get("title") or "") if project else "",
        "project_root": str(project.get("root") or "") if project else "",
        "objective": objective,
        "action_type": action_type,
        "slice_key": slice_key,
        "autonomy_mode": "execute",
        "owner_lane": profile_key,
        "delivery_model": delivery_model,
        "lead_lane": str(delivery_model.get("lead_lane") or ""),
        "active_lane": str(delivery_model.get("active_lane") or ""),
        "next_lane": str(delivery_model.get("next_lane") or ""),
        "lane_sequence": list(delivery_model.get("lane_sequence") or []),
        "recommended_lanes": _recommended_lanes(profile_key, project, objective),
        "expected_deliverables": expected_deliverables,
        "verification_required": verification_required,
        "progress_update_request": progress_update_request,
        "dispatch_readiness": dispatch_readiness,
        "attempt_contract": {
            "single_owner_lane": True,
            "single_active_attempt_per_slice": True,
            "closure_requires_artifact_and_proof": True,
        },
        "response_contract": {
            "required_keys": [
                "summary",
                "implemented",
                "verified",
                "assumed",
                "blocked",
                "risks",
                "next_actions",
                "artifacts",
                "handoff_needed",
            ],
            "operator_required_keys": [
                "action_taken",
                "focus_slice",
                "owner_lane",
                "proof_status",
                "closure_decision",
                "dispatches",
                "project_update",
            ]
            if profile_key == "operator"
            else [],
        },
    }
    if project:
        result["project_status"] = str(project.get("status") or "")
        result["project_owner"] = str(project.get("owner") or "")
        result["project_now"] = str(project.get("now") or "")
        result["project_next"] = str(project.get("next") or "")
        control = project.get("control") if isinstance(project.get("control"), dict) else {}
        portfolio = project.get("portfolio") if isinstance(project.get("portfolio"), dict) else {}
        result["project_control"] = {
            "project_kind": str(control.get("project_kind") or ""),
            "control_mode": str(control.get("control_mode") or ""),
            "primary_lane": str(control.get("primary_lane") or ""),
            "lane_sequence": list(control.get("lane_sequence") or []) if isinstance(control.get("lane_sequence"), list) else [],
            "delivery_target": str(control.get("delivery_target") or ""),
            "primary_artifact": str(control.get("primary_artifact") or ""),
            "strict_dispatch": bool(control.get("strict_dispatch", False)),
            "acceptance": list(control.get("acceptance") or []) if isinstance(control.get("acceptance"), list) else [],
            "capability_gaps": list(control.get("capability_gaps") or []) if isinstance(control.get("capability_gaps"), list) else [],
        }
        result["portfolio"] = {
            "active": bool(portfolio.get("active")),
            "queue_position": int(portfolio.get("queue_position") or 0),
            "state": str(portfolio.get("state") or ""),
            "session_bindings": list(portfolio.get("session_bindings") or []) if isinstance(portfolio.get("session_bindings"), list) else [],
        }
    return result


def work_order_message(work_order: dict[str, object]) -> dict[str, str]:
    return {
        "role": "system",
        "content": (
            "Active work order for this turn. Treat it as the control-plane contract and keep your execution aligned to it.\n"
            f"```json\n{json.dumps(work_order, indent=2)}\n```"
        ),
    }


def project_context_message(project: dict[str, object] | None) -> dict[str, str] | None:
    if not project:
        return None
    control = project.get("control") if isinstance(project.get("control"), dict) else {}
    portfolio = project.get("portfolio") if isinstance(project.get("portfolio"), dict) else {}
    primary_lane = str(control.get("primary_lane") or "").strip() or "operator"
    delivery_target = str(control.get("delivery_target") or "").strip() or "not yet frozen"
    primary_artifact = str(control.get("primary_artifact") or "").strip() or "not yet named"
    queue_position = int(portfolio.get("queue_position") or 0)
    queue_text = f" Queue position: {queue_position}." if queue_position else ""
    return {
        "role": "system",
        "content": (
            f"Bound project context: {project.get('project_id')} / {project.get('title')}. "
            f"Summary: {project.get('summary') or 'n/a'}. "
            f"Project root: {project.get('root')}. "
            f"Primary specialist lane: {primary_lane}. "
            f"Delivery target: {delivery_target}. "
            f"Primary artifact: {primary_artifact}."
            f"{queue_text}"
            "Treat this as the canonical delivery target unless the user explicitly overrides it. "
            "If the user asks for progress or status in a vague way, default to the project's current build/delivery state first and cite the primary artifact or live run before pivoting to side blockers like device access."
        ),
    }


def runtime_contract_message(profile_key: str) -> dict[str, str]:
    base_lines = [
        "Execution contract for this turn:",
        "- Treat build, fix, create, debug, polish, and review requests as execution work, not just planning work.",
        "- The user's request is authorization for non-destructive work inside approved roots and the bound repo. Do not bounce the task back for more permission unless the action is destructive, irreversible, or changes product direction in a non-obvious way.",
        "- Use tools, inspect the real artifact, and run the smallest local verification you can before claiming success.",
        "- Before opening or relying on a localhost or 127.0.0.1 URL in the browser, preflight it with a lightweight command such as curl. If it is down, recover or restate the actual live path instead of waiting on a dead browser target.",
        "- Do not ask the user to run local commands, refresh pages, inspect files, or check localhost routes when you can do that yourself on this machine.",
        "- Never say fixed, complete, shipped, live, or verified unless you name the exact artifact and the checks you personally ran in this turn.",
        "- Always separate implemented, verified, and assumed.",
        "- Keep autonomous execution moving inside approved roots. These evidence requirements harden proof, not initiative, and are not a reason to pause on safe next actions.",
        "- When art or sprite inputs are involved, classify the asset package before integrating it. Reference boards, mood boards, screenshots, and labeled presentation sheets are not build-ready runtime atlases.",
        "- If a sprite image contains labels, section dividers, notes, or a baked presentation background, say that plainly, stop treating it as a runtime sheet, and state what production format is actually required.",
        "- For reference-driven storyboard or concept work, do not claim the result is grounded in the reference image unless the delivered frames visibly reflect the referenced subjects, props, composition, and lighting. Abstract diagrams must be labeled as placeholders, not review-ready boards.",
        "- For visual claims, name what is visibly on screen in the screenshot or capture. Runtime flags, cache-bust tokens, or atlas state are not enough proof by themselves.",
        "- If placeholders, letter tiles, or obviously wrong art are still visible, do not call the visual pass fixed, live, or complete.",
        "- Return a concise human summary followed by a machine-readable ```json``` block.",
        "- The JSON block must include: summary, implemented, verified, assumed, blocked, risks, next_actions, artifacts, handoff_needed.",
    ]
    if profile_key == "operator":
        base_lines.extend(
            [
                "- You are the orchestration layer. Default to routing, sequencing, and enforcing finish criteria instead of absorbing specialist implementation work yourself.",
                "- Treat the Hermes project portfolio as the control plane: keep multiple projects alive, but keep exactly one focus slice active at a time.",
                "- When a user asks to start, split, pause, archive, or switch projects, update the project record and the portfolio state explicitly instead of leaving it implicit in chat.",
                "- When specialist work is needed, route it explicitly and hold the result to the same execution and verification bar before reporting success.",
                "- Review specialist output like a lead: accept it, request a revision with concrete critique, or escalate it after repeated failures. Do not treat a weak specialist response as a final answer.",
                "- If strict dispatch is active for the bound project, keep lane ownership with the assigned specialist until the lane is exhausted or a capability gap is logged.",
                "- Do not defend a previous run that still looks wrong. Re-inspect the live artifact and call the drift honestly.",
                "- In the JSON block, also include: action_taken, focus_slice, owner_lane, proof_status, closure_decision, dispatches, project_update.",
                "- action_taken must be exactly one of: direct_execute, dispatch_specialist, close_slice, update_project, mark_blocked, revise_dispatch, promote_artifact, archive_or_park, request_decision, escalate.",
                "- proof_status must be exactly one of: none, claimed, partial, verified.",
                "- closure_decision must be exactly one of: not_closing, ready_to_close, blocked, needs_revision.",
                "- focus_slice must restate the single slice you are actively moving in this turn.",
                "- owner_lane must name the lane currently owning that slice.",
                "- If you dispatch a specialist, list the dispatch ids or lane outcomes in dispatches.",
                "- project_update should carry the truthful project state delta you just earned, such as status, now, next, primary_artifact, primary_lane, blocked, or done.",
                "- If the work order action is close_slice, do not use closure_decision=ready_to_close unless artifacts, proof, and acceptance are all truly satisfied in this turn.",
                "- If the contract is incomplete or the slice is still drifting, use action_taken=mark_blocked or escalate instead of pretending the work closed.",
            ]
        )
    elif profile_key == "game-dev":
        base_lines.extend(
            [
                "- Compare the served build, scene, and gameplay against the project brief, canon, roadmap, and any UI or visual spec tied to the request.",
                "- Prefer one converging implementation and identify deprecated or reference-only paths explicitly.",
            ]
        )
    elif profile_key == "app-dev":
        base_lines.append("- Ground the work in the real codebase and service outputs, not generic implementation advice.")
    elif profile_key == "creative-dev":
        base_lines.append("- Ground review and direction in the real references and live artifact, not only aspirational language.")
    return {"role": "system", "content": "\n".join(base_lines)}


def summarize_result_for_tracking(run_record: dict[str, object], structured_result: dict[str, object], output: str) -> str:
    objective = extract_operator_request_text(str(run_record.get("objective_preview") or "").strip())
    summary = str(structured_result.get("summary") or "").strip()
    implemented = structured_result.get("implemented") if isinstance(structured_result.get("implemented"), list) else []
    first_implemented = str(implemented[0]).strip() if implemented else ""
    if objective and summary and summary.lower() != objective.lower():
        return clip_text(f"{objective} -> {summary}", 220)
    if first_implemented:
        return clip_text(first_implemented, 220)
    if summary:
        return clip_text(summary, 220)
    first_line = _first_meaningful_line(output)
    return clip_text(objective or first_line or str(run_record.get("latest_checkpoint") or ""), 220)


def monitor_recommendation(kind: str, *, profile_key: str, project_id: str, subject: str) -> dict[str, str]:
    if kind == "stalled-run":
        return {
            "action_key": "inspect-run",
            "label": "Inspect run",
            "detail": f"Review run {subject} checkpoints, then retry with a tighter work order if it is truly stuck.",
        }
    if kind == "handoff-gap":
        return {
            "action_key": "retry-close-loop",
            "label": "Retry close loop",
            "detail": f"Re-run {subject} with the same project binding but require direct verification and no operator handoff.",
        }
    if kind == "stalled-dispatch":
        return {
            "action_key": "inspect-dispatch",
            "label": "Inspect dispatch",
            "detail": f"Check whether {profile_key or 'the specialist'} is still working or whether the bridge died before completion.",
        }
    if kind == "unbound-dispatch":
        return {
            "action_key": "bind-project",
            "label": "Bind project",
            "detail": "Attach this dispatch to the correct project so future coordination and artifact tracking stay coherent.",
        }
    if kind == "session-handoff":
        return {
            "action_key": "tighten-operator-loop",
            "label": "Tighten operator loop",
            "detail": "Have Sheldon close the loop directly or dispatch a specialist instead of pausing on operator approval language.",
        }
    return {
        "action_key": "review",
        "label": "Review",
        "detail": "Inspect this signal and decide whether it needs a retry, escalation, or portfolio update.",
    }
