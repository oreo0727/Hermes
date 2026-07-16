#!/usr/bin/env python3
"""Apply repo-managed browser tool patches to the installed Hermes package."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _venv_dir(root_dir: Path) -> Path:
    raw = (
        os.environ.get("HERMES_STACK_VENV")
        or os.environ.get("OPENCLAW_HERMES_VENV")
        or str(root_dir / "state" / "hermes" / "venv")
    )
    return Path(raw).expanduser().resolve()


def _browser_tool_path(venv_dir: Path) -> Path:
    matches = sorted(venv_dir.glob("lib/python*/site-packages/tools/browser_tool.py"))
    if not matches:
        raise FileNotFoundError(f"Could not find tools/browser_tool.py under {venv_dir}")
    return matches[0]


def _patch_browser_tool(text: str) -> tuple[str, bool]:
    if "_get_local_browser_args" in text and 'launch_args = ["--args", ",".join(local_browser_args)]' in text:
        return text, False

    updated = text

    cache_anchor = "_cached_command_timeout: Optional[int] = None\n_command_timeout_resolved = False\n"
    cache_insert = (
        "_cached_command_timeout: Optional[int] = None\n"
        "_command_timeout_resolved = False\n"
        "_cached_local_browser_args: Optional[List[str]] = None\n"
        "_local_browser_args_resolved = False\n"
    )
    if cache_anchor in updated:
        updated = updated.replace(cache_anchor, cache_insert, 1)
    else:
        raise RuntimeError("Could not find browser_tool cache anchor")

    function_anchor = "\n\ndef _get_vision_model() -> Optional[str]:\n"
    function_insert = """


def _get_local_browser_args() -> List[str]:
    \"\"\"Return extra CLI flags for local agent-browser launches.

    Reads ``config["browser"]["local_args"]`` once and caches the parsed
    result. Accepts either a YAML list or a comma/newline-separated string.
    \"\"\"
    global _cached_local_browser_args, _local_browser_args_resolved
    if _local_browser_args_resolved:
        return list(_cached_local_browser_args or [])

    _local_browser_args_resolved = True
    result: List[str] = []
    try:
        from hermes_cli.config import read_raw_config
        cfg = read_raw_config()
        raw = cfg.get("browser", {}).get("local_args", [])
        if isinstance(raw, str):
            normalized = raw.replace("\\n", ",")
            result = [part.strip() for part in normalized.split(",") if part.strip()]
        elif isinstance(raw, list):
            result = [str(part).strip() for part in raw if str(part).strip()]
    except Exception as e:
        logger.debug("Could not read local browser args from config: %s", e)

    _cached_local_browser_args = result
    return list(result)
"""
    if function_anchor in updated:
        updated = updated.replace(function_anchor, function_insert + function_anchor, 1)
    else:
        raise RuntimeError("Could not find browser_tool function anchor")

    command_variants = [
        (
            """    if session_info.get("cdp_url"):
        # Cloud mode — connect to remote Browserbase browser via CDP
        # IMPORTANT: Do NOT use --session with --cdp. In agent-browser >=0.13,
        # --session creates a local browser instance and silently ignores --cdp.
        backend_args = ["--cdp", session_info["cdp_url"]]
    else:
        # Local mode — launch a headless Chromium instance
        backend_args = ["--session", session_info["session_name"]]

    # Keep concrete executable paths intact, even when they contain spaces.
    # Only the synthetic npx fallback needs to expand into multiple argv items.
    cmd_prefix = ["npx", "agent-browser"] if browser_cmd == "npx agent-browser" else [browser_cmd]

    cmd_parts = cmd_prefix + backend_args + [
        "--json",
        command
    ] + args
""",
            """    if session_info.get("cdp_url"):
        # Cloud mode — connect to remote Browserbase browser via CDP
        # IMPORTANT: Do NOT use --session with --cdp. In agent-browser >=0.13,
        # --session creates a local browser instance and silently ignores --cdp.
        backend_args = ["--cdp", session_info["cdp_url"]]
        launch_args: List[str] = []
    else:
        # Local mode — launch a headless Chromium instance
        backend_args = ["--session", session_info["session_name"]]
        launch_args = []
        local_browser_args = _get_local_browser_args()
        if local_browser_args:
            launch_args = ["--args", ",".join(local_browser_args)]

    # Keep concrete executable paths intact, even when they contain spaces.
    # Only the synthetic npx fallback needs to expand into multiple argv items.
    cmd_prefix = ["npx", "agent-browser"] if browser_cmd == "npx agent-browser" else [browser_cmd]

    cmd_parts = cmd_prefix + backend_args + launch_args + [
        "--json",
        command
    ] + args
""",
        ),
        (
            """    if session_info.get("cdp_url"):
        # Cloud mode — connect to remote Browserbase browser via CDP
        # IMPORTANT: Do NOT use --session with --cdp. In agent-browser >=0.13,
        # --session creates a local browser instance and silently ignores --cdp.
        backend_args = ["--cdp", session_info["cdp_url"]]
    else:
        # Local mode — launch a headless Chromium instance
        backend_args = ["--session", session_info["session_name"]]

    # Lightpanda engine injection (local mode only, agent-browser v0.25.3+).
    # Use the resolved session backend rather than global cloud-provider state:
    # hybrid private-URL routing can create a local sidecar while a cloud
    # provider remains configured for public URLs.
    engine = _engine_override or _get_browser_engine()
    if engine != "auto" and not _is_camofox_mode() and not session_info.get("cdp_url"):
        backend_args += ["--engine", engine]

    # Keep concrete executable paths intact, even when they contain spaces.
    # Only the synthetic npx fallback needs to expand into multiple argv items.
    # shutil.which resolves npx → npx.cmd on Windows; bare "npx" stays on POSIX.
    if browser_cmd == "npx agent-browser":
        _npx_bin = shutil.which("npx") or "npx"
        cmd_prefix = [_npx_bin, "agent-browser"]
    else:
        cmd_prefix = [browser_cmd]

    cmd_parts = cmd_prefix + backend_args + [
        "--json",
        command
    ] + args
""",
            """    if session_info.get("cdp_url"):
        # Cloud mode — connect to remote Browserbase browser via CDP
        # IMPORTANT: Do NOT use --session with --cdp. In agent-browser >=0.13,
        # --session creates a local browser instance and silently ignores --cdp.
        backend_args = ["--cdp", session_info["cdp_url"]]
        launch_args: List[str] = []
    else:
        # Local mode — launch a headless Chromium instance
        backend_args = ["--session", session_info["session_name"]]
        launch_args = []
        local_browser_args = _get_local_browser_args()
        if local_browser_args:
            launch_args = ["--args", ",".join(local_browser_args)]

    # Lightpanda engine injection (local mode only, agent-browser v0.25.3+).
    # Use the resolved session backend rather than global cloud-provider state:
    # hybrid private-URL routing can create a local sidecar while a cloud
    # provider remains configured for public URLs.
    engine = _engine_override or _get_browser_engine()
    if engine != "auto" and not _is_camofox_mode() and not session_info.get("cdp_url"):
        backend_args += ["--engine", engine]

    # Keep concrete executable paths intact, even when they contain spaces.
    # Only the synthetic npx fallback needs to expand into multiple argv items.
    # shutil.which resolves npx → npx.cmd on Windows; bare "npx" stays on POSIX.
    if browser_cmd == "npx agent-browser":
        _npx_bin = shutil.which("npx") or "npx"
        cmd_prefix = [_npx_bin, "agent-browser"]
    else:
        cmd_prefix = [browser_cmd]

    cmd_parts = cmd_prefix + backend_args + launch_args + [
        "--json",
        command
    ] + args
""",
        ),
    ]
    for command_anchor, command_insert in command_variants:
        if command_anchor in updated:
            updated = updated.replace(command_anchor, command_insert, 1)
            break
    else:
        raise RuntimeError("Could not find browser_tool command anchor")

    cleanup_variants = [
        (
            """    global _cached_agent_browser, _agent_browser_resolved
    global _cached_command_timeout, _command_timeout_resolved
    _cached_agent_browser = None
    _agent_browser_resolved = False
    _discover_homebrew_node_dirs.cache_clear()
    _cached_command_timeout = None
    _command_timeout_resolved = False
""",
            """    global _cached_agent_browser, _agent_browser_resolved
    global _cached_command_timeout, _command_timeout_resolved
    global _cached_local_browser_args, _local_browser_args_resolved
    _cached_agent_browser = None
    _agent_browser_resolved = False
    _discover_homebrew_node_dirs.cache_clear()
    _cached_command_timeout = None
    _command_timeout_resolved = False
    _cached_local_browser_args = None
    _local_browser_args_resolved = False
""",
        ),
        (
            """    global _cached_agent_browser, _agent_browser_resolved
    global _cached_command_timeout, _command_timeout_resolved
    global _cached_chromium_installed
    global _cached_browser_engine, _browser_engine_resolved
    _cached_agent_browser = None
    _agent_browser_resolved = False
    _discover_homebrew_node_dirs.cache_clear()
    # Flip the resolved flag BEFORE nulling the cache so a concurrent
    # reader never sees ``resolved=True`` with ``cache=None`` (#14331).
    _command_timeout_resolved = False
    _cached_command_timeout = None
    _cached_chromium_installed = None
    global _chromium_autoinstall_attempted
    _chromium_autoinstall_attempted = False
    _cached_browser_engine = None
    _browser_engine_resolved = False
""",
            """    global _cached_agent_browser, _agent_browser_resolved
    global _cached_command_timeout, _command_timeout_resolved
    global _cached_local_browser_args, _local_browser_args_resolved
    global _cached_chromium_installed
    global _cached_browser_engine, _browser_engine_resolved
    _cached_agent_browser = None
    _agent_browser_resolved = False
    _discover_homebrew_node_dirs.cache_clear()
    # Flip the resolved flag BEFORE nulling the cache so a concurrent
    # reader never sees ``resolved=True`` with ``cache=None`` (#14331).
    _command_timeout_resolved = False
    _cached_command_timeout = None
    _cached_local_browser_args = None
    _local_browser_args_resolved = False
    _cached_chromium_installed = None
    global _chromium_autoinstall_attempted
    _chromium_autoinstall_attempted = False
    _cached_browser_engine = None
    _browser_engine_resolved = False
""",
        ),
    ]
    for cleanup_anchor, cleanup_insert in cleanup_variants:
        if cleanup_anchor in updated:
            updated = updated.replace(cleanup_anchor, cleanup_insert, 1)
            break
    else:
        raise RuntimeError("Could not find browser_tool cleanup anchor")

    if updated == text:
        return text, False
    return updated, True


def main() -> int:
    root_dir = _repo_root()
    venv_dir = _venv_dir(root_dir)
    target = _browser_tool_path(venv_dir)
    original = target.read_text(encoding="utf-8")
    patched, changed = _patch_browser_tool(original)
    if changed:
        target.write_text(patched, encoding="utf-8")
        print(f"Patched browser tool: {target}")
    else:
        print(f"Browser tool already patched: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
