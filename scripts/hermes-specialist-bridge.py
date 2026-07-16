#!/usr/bin/env python3
"""Bridge the operator lane to a live Hermes specialist API."""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hermes_stack.projects import discover_projects, repo_root, update_project  # noqa: E402
from hermes_stack.orchestration import (  # noqa: E402
    build_work_order,
    clip_text,
    execution_quality_issues,
    parse_assistant_output,
    result_contract_review,
    runtime_contract_message,
    supervisor_revision_prompt,
    supervisor_review,
    utc_now,
    work_order_message,
)
from hermes_stack.scaffold import hermes_state_dir, profiles_dir  # noqa: E402
from hermes_stack.state_store import list_dispatches as store_list_dispatches, upsert_dispatch as store_upsert_dispatch  # noqa: E402


VALID_PROFILES = ("app-dev", "game-dev", "creative-dev")
DEFAULT_TIMEOUT_SECONDS = 1800
DEFAULT_SUPERVISOR_MAX_ATTEMPTS = 3


def _utc_now() -> str:
    return utc_now()


def _clip_text(value: object, limit: int = 320) -> str:
    return clip_text(value, limit)


def _dispatch_dir(root_dir: Path) -> Path:
    path = hermes_state_dir(root_dir) / "specialist_dispatches"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _dispatch_path(root_dir: Path, dispatch_id: str) -> Path:
    return _dispatch_dir(root_dir) / f"{dispatch_id}.json"


def _write_dispatch(root_dir: Path, payload: dict[str, object]) -> None:
    store_upsert_dispatch(root_dir, payload)


def _sync_project_after_dispatch_failure(root_dir: Path, dispatch_record: dict[str, object]) -> None:
    project_id = str(dispatch_record.get("project_id") or "").strip()
    if not project_id:
        return

    try:
        project = _project_context(root_dir, project_id)
    except SystemExit:
        return

    control = project.get("control") if isinstance(project.get("control"), dict) else {}
    if not bool(control.get("strict_dispatch", False)):
        return

    structured_result = (
        dispatch_record.get("structured_result")
        if isinstance(dispatch_record.get("structured_result"), dict)
        else {}
    )
    summary = str(structured_result.get("summary") or dispatch_record.get("output_preview") or dispatch_record.get("prompt_preview") or "").strip()
    next_actions = structured_result.get("next_actions") if isinstance(structured_result.get("next_actions"), list) else []
    blocked_rows = structured_result.get("blocked") if isinstance(structured_result.get("blocked"), list) else []
    supervisor = dispatch_record.get("supervisor") if isinstance(dispatch_record.get("supervisor"), dict) else {}
    critique = supervisor.get("critique") if isinstance(supervisor.get("critique"), list) else []
    error_preview = str(dispatch_record.get("error_preview") or "").strip()
    primary_artifact = ""
    artifacts = structured_result.get("artifacts") if isinstance(structured_result.get("artifacts"), list) else []
    if artifacts:
        primary_artifact = ", ".join(str(item).strip() for item in artifacts[:3] if str(item).strip())

    merged_blocked = [
        *[str(item).strip() for item in blocked_rows if str(item).strip()],
        *[str(item).strip() for item in critique if str(item).strip()],
    ]
    if error_preview:
        merged_blocked.append(error_preview)

    deduped_blocked: list[str] = []
    seen: set[str] = set()
    for item in merged_blocked:
        normalized = item.lower()
        if not normalized or normalized in seen:
            continue
        deduped_blocked.append(item)
        seen.add(normalized)

    update_project(
        root_dir,
        project_id=project_id,
        status="blocked",
        owner=str(dispatch_record.get("profile") or "").strip() or None,
        now=summary or None,
        next_value=str(next_actions[0]).strip() if next_actions else None,
        blocked=tuple(deduped_blocked[:6]),
        primary_artifact=primary_artifact or None,
    )


def _existing_active_dispatch(
    root_dir: Path,
    *,
    profile: str,
    project_id: str,
    slice_key: str,
) -> dict[str, object] | None:
    for payload in store_list_dispatches(root_dir):
        if str(payload.get("status") or "") != "running":
            continue
        if str(payload.get("profile") or "") != profile:
            continue
        if str(payload.get("project_id") or "") != project_id:
            continue
        if str(payload.get("slice_key") or "") != slice_key:
            continue
        return payload
    return None


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _resolve_timeout_seconds(root_dir: Path, profile: str, requested_timeout: int) -> int:
    if requested_timeout > 0:
        return requested_timeout

    config_path = profiles_dir(root_dir) / profile / "config.yaml"
    if config_path.exists():
        match = re.search(
            r"(?m)^\s*gateway_timeout:\s*(\d+)\s*$",
            config_path.read_text(encoding="utf-8"),
        )
        if match:
            try:
                gateway_timeout = int(match.group(1))
            except ValueError:
                gateway_timeout = 0
            if gateway_timeout > 0:
                return max(DEFAULT_TIMEOUT_SECONDS, gateway_timeout + 300)

    return DEFAULT_TIMEOUT_SECONDS


def _fail_dispatch(root_dir: Path, dispatch_record: dict[str, object], error: object) -> None:
    dispatch_record["status"] = "failed"
    dispatch_record["updated_at"] = _utc_now()
    dispatch_record["completed_at"] = dispatch_record["updated_at"]
    dispatch_record["error_preview"] = _clip_text(error, 320)
    _write_dispatch(root_dir, dispatch_record)
    _sync_project_after_dispatch_failure(root_dir, dispatch_record)


def _project_context(root_dir: Path, project_id: str) -> dict[str, object]:
    for project in discover_projects(root_dir):
        if str(project.get("project_id")) == project_id:
            return project
    raise SystemExit(f"Unknown project_id: {project_id}")


def _bridge_system_prompt(profile: str) -> str:
    return str(runtime_contract_message(profile).get("content") or "")


def _execution_quality_issues(output: str) -> list[str]:
    return execution_quality_issues(output)


def _supervisor_max_attempts(project: dict[str, object] | None) -> int:
    control = project.get("control") if project and isinstance(project.get("control"), dict) else {}
    retry_budget = control.get("supervisor_max_attempts")
    try:
        value = int(retry_budget)
    except (TypeError, ValueError):
        value = DEFAULT_SUPERVISOR_MAX_ATTEMPTS
    return max(1, min(5, value))


def _build_user_prompt(prompt: str, project: dict[str, object] | None) -> str:
    if not project:
        return prompt.strip()
    return "\n".join(
        [
            f"Project ID: {project.get('project_id')}",
            f"Project Title: {project.get('title')}",
            f"Project Status: {project.get('status')}",
            f"Project Summary: {project.get('summary') or 'n/a'}",
            f"Progress Stage: {project.get('progress_stage')}",
            f"Progress Percent: {project.get('progress_percent')}%",
            f"Project Root: {project.get('root')}",
            "",
            "Operator request:",
            prompt.strip(),
        ]
    ).strip()


def _request_payload(
    profile: str,
    prompt: str,
    project: dict[str, object] | None,
    *,
    work_order: dict[str, object] | None = None,
) -> dict[str, object]:
    operator_message = {
        "role": "user",
        "content": _build_user_prompt(prompt, project),
    }
    if work_order is None:
        work_order = build_work_order(
            profile_key=profile,
            project=project,
            messages=[operator_message],
            source="specialist-bridge",
        )
    messages: list[dict[str, str]] = []
    messages.append(
        {
            "role": "system",
            "content": (
                "You are supporting Sheldon, the Hermes operator. "
                "Focus on the project context provided, do the specialist work directly, "
                "and answer with concrete artifacts, decisions, risks, and next steps. "
                "Treat the project brief, release criteria, and current artifact tree as the source of truth. "
                "If implementation drifted, name the drift explicitly. "
                "Do not say fixed, complete, live, shipped, or verified unless you name the exact artifact and the checks you personally ran. "
                "Always separate implemented, verified, and assumed. "
                "If scope changed, restate the new target and what previous path is now deprecated or reference-only. "
                "Prefer one converging implementation over multiple partial rebuilds. "
                f"{_bridge_system_prompt(profile)}"
            ),
        }
    )
    messages.append(work_order_message(work_order))
    messages.append(operator_message)
    return {
        "model": profile,
        "messages": messages,
        "stream": False,
        "work_order": work_order,
    }


def _dispatch_attempt(
    *,
    root_dir: Path,
    dispatch_record: dict[str, object],
    profile: str,
    prompt: str,
    project: dict[str, object] | None,
    timeout_seconds: int,
    work_order: dict[str, object],
) -> tuple[str, dict[str, object], dict[str, object]]:
    request_body = _request_payload(profile, prompt, project, work_order=work_order)
    dispatch_record["work_order"] = request_body.get("work_order") or {}
    env = _read_env_file(profiles_dir(root_dir) / profile / ".env")
    port = int(env.get("API_SERVER_PORT", "0") or 0)
    api_key = env.get("API_SERVER_KEY", "")
    if not port or not api_key:
        raise SystemExit(f"{profile} API server is not configured")

    request = Request(
        url=f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=max(1, timeout_seconds)) as response:
        raw = json.loads(response.read().decode("utf-8"))
    choices = raw.get("choices") or []
    content = ""
    if choices:
        content = str(((choices[0] or {}).get("message") or {}).get("content") or "").strip()
    display_content, structured_result = parse_assistant_output(content)
    return content, structured_result, {
        "raw": raw,
        "display_content": display_content,
        "work_order": request_body.get("work_order") or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", default=str(REPO_ROOT), help="Hermes repo root")
    parser.add_argument("--profile", required=True, choices=VALID_PROFILES, help="Specialist profile to call")
    parser.add_argument("--project-id", default="", help="Optional Hermes project id for context")
    parser.add_argument("--prompt", required=True, help="Instruction for the specialist")
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="HTTP timeout in seconds (0 uses the profile gateway timeout policy)",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON instead of plain text")
    args = parser.parse_args()

    root_dir = repo_root(args.root_dir)
    dispatch_id = f"dispatch_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    dispatch_record: dict[str, object] = {
        "dispatch_id": dispatch_id,
        "source": "operator-bridge",
        "profile": args.profile,
        "project_id": args.project_id.strip(),
        "status": "running",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "completed_at": "",
        "prompt_preview": _clip_text(args.prompt, 220),
        "output_preview": "",
        "error_preview": "",
        "supervisor": {
            "status": "running",
            "attempt_count": 0,
            "max_attempts": 0,
            "decision": "",
            "critique": [],
        },
        "attempts": [],
    }
    project = _project_context(root_dir, args.project_id.strip()) if args.project_id.strip() else None
    work_order = build_work_order(
        profile_key=args.profile,
        project=project,
        messages=[
            {
                "role": "user",
                "content": _build_user_prompt(args.prompt, project),
            }
        ],
        source="specialist-bridge",
    )
    dispatch_record["work_order"] = work_order
    dispatch_record["slice_key"] = str(work_order.get("slice_key") or "")
    dispatch_record["action_type"] = str(work_order.get("action_type") or "")
    dispatch_record["dispatch_readiness"] = work_order.get("dispatch_readiness") or {}

    readiness = work_order.get("dispatch_readiness") if isinstance(work_order.get("dispatch_readiness"), dict) else {}
    if not bool(readiness.get("ready", True)):
        dispatch_record["status"] = "failed"
        dispatch_record["updated_at"] = _utc_now()
        dispatch_record["completed_at"] = dispatch_record["updated_at"]
        dispatch_record["error_preview"] = _clip_text(" ".join(str(item) for item in readiness.get("reasons") or []), 320)
        _write_dispatch(root_dir, dispatch_record)
        raise SystemExit(
            "Dispatch contract is incomplete: "
            + "; ".join(str(item) for item in readiness.get("reasons") or [])
        )

    existing_dispatch = _existing_active_dispatch(
        root_dir,
        profile=args.profile,
        project_id=args.project_id.strip(),
        slice_key=str(work_order.get("slice_key") or ""),
    )
    if existing_dispatch is not None:
        dispatch_record["status"] = "failed"
        dispatch_record["updated_at"] = _utc_now()
        dispatch_record["completed_at"] = dispatch_record["updated_at"]
        dispatch_record["error_preview"] = _clip_text(
            f"Active dispatch {existing_dispatch.get('dispatch_id')} already owns this slice.",
            320,
        )
        _write_dispatch(root_dir, dispatch_record)
        raise SystemExit(
            f"Slice already has an active dispatch: {existing_dispatch.get('dispatch_id')}"
        )

    _write_dispatch(root_dir, dispatch_record)

    timeout_seconds = _resolve_timeout_seconds(root_dir, args.profile, args.timeout)
    env = _read_env_file(profiles_dir(root_dir) / args.profile / ".env")
    port = int(env.get("API_SERVER_PORT", "0") or 0)
    api_key = env.get("API_SERVER_KEY", "")
    if not port or not api_key:
        dispatch_record["status"] = "failed"
        dispatch_record["updated_at"] = _utc_now()
        dispatch_record["completed_at"] = dispatch_record["updated_at"]
        dispatch_record["error_preview"] = f"{args.profile} API server is not configured"
        _write_dispatch(root_dir, dispatch_record)
        raise SystemExit(f"{args.profile} API server is not configured")

    max_attempts = _supervisor_max_attempts(project)
    dispatch_record["supervisor"] = {
        "status": "running",
        "attempt_count": 0,
        "max_attempts": max_attempts,
        "decision": "",
        "critique": [],
    }
    _write_dispatch(root_dir, dispatch_record)

    current_prompt = args.prompt
    display_content = ""
    structured_result: dict[str, object] = {}
    raw: dict[str, object] = {}
    final_review: dict[str, object] = {}
    final_contract_review: dict[str, object] = {}

    for attempt_number in range(1, max_attempts + 1):
        dispatch_record["updated_at"] = _utc_now()
        dispatch_record["supervisor"] = {
            "status": "running",
            "attempt_count": attempt_number,
            "max_attempts": max_attempts,
            "decision": "",
            "critique": [],
        }
        _write_dispatch(root_dir, dispatch_record)
        try:
            content, structured_result, attempt_meta = _dispatch_attempt(
                root_dir=root_dir,
                dispatch_record=dispatch_record,
                profile=args.profile,
                prompt=current_prompt,
                project=project,
                timeout_seconds=timeout_seconds,
                work_order=work_order,
            )
            display_content = str(attempt_meta.get("display_content") or "").strip()
            raw = attempt_meta.get("raw") if isinstance(attempt_meta.get("raw"), dict) else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            _fail_dispatch(root_dir, dispatch_record, detail or str(exc))
            raise SystemExit(f"{args.profile} HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            _fail_dispatch(root_dir, dispatch_record, str(exc))
            raise SystemExit(
                f"{args.profile} is unreachable. Start it with ./scripts/run-hermes-gateway.sh {args.profile}"
            ) from exc
        except (TimeoutError, socket.timeout) as exc:
            message = f"{args.profile} timed out after {timeout_seconds} seconds: {exc}"
            _fail_dispatch(root_dir, dispatch_record, message)
            raise SystemExit(message) from exc
        except Exception as exc:
            _fail_dispatch(root_dir, dispatch_record, str(exc))
            raise

        review = supervisor_review(profile_key=args.profile, project=project, output=content)
        contract_review = result_contract_review(
            profile_key=args.profile,
            work_order=work_order,
            structured_result=structured_result,
        )
        final_contract_review = contract_review
        final_review = review
        attempts = dispatch_record.get("attempts")
        if not isinstance(attempts, list):
            attempts = []
        attempts.append(
            {
                "attempt_number": attempt_number,
                "prompt_preview": _clip_text(current_prompt, 220),
                "output_preview": _clip_text(display_content, 320),
                "structured_result": structured_result,
                "contract_review": contract_review,
                "review": review,
                "completed_at": _utc_now(),
            }
        )
        dispatch_record["attempts"] = attempts
        dispatch_record["output_preview"] = _clip_text(display_content, 320)
        dispatch_record["structured_result"] = structured_result
        dispatch_record["contract_review"] = contract_review
        dispatch_record["updated_at"] = _utc_now()
        dispatch_record["supervisor"] = {
            "status": "accepted" if str(review.get("decision") or "") == "accept" else "revision-requested",
            "attempt_count": attempt_number,
            "max_attempts": max_attempts,
            "decision": str(review.get("decision") or ""),
            "critique": list(review.get("critique") or []) if isinstance(review.get("critique"), list) else [],
        }
        _write_dispatch(root_dir, dispatch_record)

        if str(review.get("decision") or "") == "accept":
            dispatch_record["status"] = "completed"
            dispatch_record["updated_at"] = _utc_now()
            dispatch_record["completed_at"] = dispatch_record["updated_at"]
            _write_dispatch(root_dir, dispatch_record)
            break

        if attempt_number >= max_attempts:
            critique = review.get("critique") if isinstance(review.get("critique"), list) else []
            dispatch_record["status"] = "failed"
            dispatch_record["updated_at"] = _utc_now()
            dispatch_record["completed_at"] = dispatch_record["updated_at"]
            dispatch_record["error_preview"] = _clip_text(" ".join(str(item) for item in critique[:4]), 320)
            dispatch_record["supervisor"] = {
                "status": "failed",
                "attempt_count": attempt_number,
                "max_attempts": max_attempts,
                "decision": "escalate",
                "critique": critique,
            }
            _write_dispatch(root_dir, dispatch_record)
            raise SystemExit(
                f"{args.profile} failed supervised review after {attempt_number} attempt(s): "
                + " ".join(str(item) for item in critique[:4])
            )

        current_prompt = supervisor_revision_prompt(
            prior_prompt=args.prompt,
            review=review,
            attempt_number=attempt_number + 1,
            max_attempts=max_attempts,
        )

    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "dispatch_id": dispatch_id,
                    "profile": args.profile,
                    "project_id": args.project_id.strip(),
                    "content": display_content,
                    "structured_result": structured_result,
                    "contract_review": final_contract_review,
                    "supervisor_review": final_review,
                    "raw": raw,
                },
                indent=2,
            )
        )
        return 0

    print(display_content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
