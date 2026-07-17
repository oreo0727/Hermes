#!/usr/bin/env python3
"""Select a no-cost video provider for a Hermes creative project."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hermes_stack.projects import update_project


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _has_env(*names: str) -> bool:
    return any(bool(os.getenv(name)) for name in names)


def _has_nvidia_gpu() -> bool:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def _run(cmd: list[str], *, cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def _builder_python(project_root: Path) -> str:
    for candidate in (
        project_root / ".venv" / "bin" / "python",
        _repo_root() / "state" / "hermes" / "venv" / "bin" / "python",
    ):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def _verify_video(path: Path, *, python_executable: str) -> tuple[bool, str]:
    if not path.exists():
        return False, f"missing: {path}"
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result = None
        ffprobe_error = str(exc)
    else:
        ffprobe_error = result.stderr.strip() if result.returncode != 0 else ""
    if result is not None and result.returncode == 0:
        duration = result.stdout.strip()
        return True, f"duration={duration}s"

    fallback = subprocess.run(
        [
            python_executable,
            "-c",
            (
                "import imageio.v3 as iio, sys; "
                "p=sys.argv[1]; "
                "frame=iio.imread(p, index=0); "
                "print(f'first_frame_size={frame.shape[1]}x{frame.shape[0]}')"
            ),
            str(path),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=40,
    )
    if fallback.returncode == 0:
        note = fallback.stdout.strip()
        return True, f"{note}; ffprobe unavailable, verified first frame with imageio"
    if ffprobe_error:
        return False, f"ffprobe unavailable: {ffprobe_error}; imageio failed: {fallback.stderr.strip()}"
    return False, fallback.stderr.strip() or "video verification failed"


def select_provider(project_root: Path) -> dict[str, object]:
    """Return the first usable no-cost video lane for this host."""
    local_motionfx = project_root / "artifacts" / "animatic_v3_motionfx.mp4"
    local_motion = project_root / "artifacts" / "animatic_v3_motion.mp4"
    motionfx_builder = project_root / "tools" / "build_motion_animatic_fx.py"
    motion_builder = project_root / "tools" / "build_motion_animatic.py"

    if motionfx_builder.exists():
        return {
            "provider": "local_motionfx",
            "cost": "free",
            "artifact": local_motionfx,
            "builder": motionfx_builder,
            "reason": "Local procedural motion/flicker/glow builder is available and needs no external account.",
        }
    if local_motionfx.exists():
        return {
            "provider": "local_motionfx_existing",
            "cost": "free",
            "artifact": local_motionfx,
            "builder": None,
            "reason": "Existing local motionfx artifact is available and needs no external account.",
        }
    if motion_builder.exists():
        return {
            "provider": "local_motion",
            "cost": "free",
            "artifact": local_motion,
            "builder": motion_builder,
            "reason": "Local Ken Burns/motion builder is available and needs no external account.",
        }
    if local_motion.exists():
        return {
            "provider": "local_motion_existing",
            "cost": "free",
            "artifact": local_motion,
            "builder": None,
            "reason": "Existing local motion artifact is available and needs no external account.",
        }
    if _has_env("HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        return {
            "provider": "huggingface_remote",
            "cost": "account-dependent",
            "artifact": project_root / "artifacts" / "animatic_v3_hf.mp4",
            "builder": None,
            "reason": "Hugging Face token is present; remote image-to-video can be attempted next.",
        }
    if _has_nvidia_gpu():
        return {
            "provider": "huggingface_local_gpu",
            "cost": "free-runtime",
            "artifact": project_root / "artifacts" / "animatic_v3_hf_local.mp4",
            "builder": None,
            "reason": "NVIDIA GPU is visible; local Diffusers image-to-video can be configured.",
        }
    if _has_env("OPENAI_API_KEY"):
        return {
            "provider": "openai_sora_experimental",
            "cost": "paid-api",
            "artifact": project_root / "artifacts" / "animatic_v3_sora.mp4",
            "builder": None,
            "reason": "OpenAI API key is present, but Sora is treated as optional because the Videos API is deprecated.",
        }
    return {
        "provider": "manual_dropbox",
        "cost": "free-manual",
        "artifact": project_root / "artifacts" / "animatic_v3_motionfx.mp4",
        "builder": None,
        "reason": "No external video credentials or GPU are available; use local/manual artifacts only.",
    }


def write_status(project_root: Path, selection: dict[str, object], verification: str) -> Path:
    status_path = project_root / "artifacts" / "video_provider_status.md"
    artifact = Path(selection["artifact"])
    lines = [
        "# Video provider status",
        "",
        f"Updated: {datetime.now(timezone.utc).isoformat()}",
        f"Selected provider: `{selection['provider']}`",
        f"Cost posture: `{selection['cost']}`",
        f"Primary artifact: `{artifact.relative_to(project_root)}`",
        "",
        "Why:",
        f"- {selection['reason']}",
        "",
        "Fallback order:",
        "- `local_motionfx` first because it is free, reproducible, and available on this host.",
        "- `huggingface_remote` when a token/quota is present.",
        "- `huggingface_local_gpu` when a suitable GPU is visible.",
        "- `openai_sora_experimental` only as an optional paid/deprecated API experiment.",
        "- `manual_dropbox` for user-generated clips dropped into the project artifacts.",
        "",
        "Verification:",
        f"- {verification}",
    ]
    status_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return status_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", default="spooky-teen-shortfilm")
    parser.add_argument("--root-dir", default=str(_repo_root()))
    parser.add_argument("--execute", action="store_true", help="Run the selected free local builder when available.")
    parser.add_argument("--update-project", action="store_true", help="Update Hermes project state after selection.")
    args = parser.parse_args()

    root = Path(args.root_dir).resolve()
    project_root = root / "state" / "projects" / args.project_id
    if not project_root.exists():
        raise SystemExit(f"Project not found: {project_root}")

    selection = select_provider(project_root)
    builder = selection.get("builder")
    if args.execute and builder:
        _run([_builder_python(project_root), str(builder)], cwd=project_root)

    artifact = Path(selection["artifact"])
    project_python = _builder_python(project_root)
    ok, verification = _verify_video(artifact, python_executable=project_python)
    status_path = write_status(project_root, selection, verification)

    if args.update_project:
        blocked = [] if ok and str(selection["provider"]).startswith("local_") else [verification]
        done = [
            "Video lane switched away from Runway-only blocking to a provider adapter with local no-cost fallback first.",
            f"Selected {selection['provider']} and verified {artifact.relative_to(project_root)} ({verification}).",
        ]
        update_project(
            root,
            project_id=args.project_id,
            status="active",
            owner="creative-dev",
            now=f"Unblocked on {selection['provider']}: {artifact.relative_to(project_root)}.",
            next_value="Review the free local motion pass for story quality; optionally upgrade later with Hugging Face or another provider if credentials/GPU become available.",
            blocked=blocked,
            done=done,
            percent=65 if ok else 40,
            delivery_target="free local motion animatic with optional provider upgrades",
            primary_artifact=f"{artifact.relative_to(project_root)}, {status_path.relative_to(project_root)}",
            capability_gaps=[],
        )

    print(f"provider={selection['provider']}")
    print(f"artifact={artifact}")
    print(f"status={status_path}")
    print(f"verified={'yes' if ok else 'no'} {verification}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
