#!/usr/bin/env python3
"""
Promote raw styleframe images (typically 1536x1024 or 1920x1088) to final 1920x1080 PNGs
with a center-crop and high-quality resize via Pillow, then replace the placeholder finals.

Usage:
  source /home/james/Hermes/state/projects/spooky-teen-shortfilm/.venv/bin/activate
  pip install --upgrade pillow
  python styleframes/tools/promote_raw_to_final.py --frames f07 f09

If --frames is omitted, the script promotes any *_raw.png in styleframes/v1.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image
except Exception as e:
    raise SystemExit("Pillow is required. Activate the project venv and `pip install pillow`.\n" + repr(e))

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "styleframes" / "v1"
TARGET = (1920, 1080)


def center_crop_to_16_9(img: Image.Image) -> Image.Image:
    w, h = img.size
    target_ratio = 16/9
    ratio = w / h
    if abs(ratio - target_ratio) < 1e-3:
        return img
    if ratio > target_ratio:
        new_w = int(round(h * target_ratio))
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    new_h = int(round(w / target_ratio))
    top = (h - new_h) // 2
    return img.crop((0, top, w, top + new_h))


def promote_one(frame_id: str) -> Path:
    raw = V1 / f"sf_{frame_id}_raw.png"
    out = V1 / f"sf_{frame_id}.png"
    if not raw.exists():
        raise FileNotFoundError(f"Raw not found: {raw}")
    img = Image.open(raw).convert("RGB")
    img = center_crop_to_16_9(img)
    img = img.resize(TARGET, Image.Resampling.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--frames", nargs="*", help="Optional list of frame IDs like f07 f09")
    args = p.parse_args(argv)

    frames = []
    if args.frames:
        frames = [f.strip().lower() for f in args.frames]
    else:
        for path in sorted(V1.glob("sf_f*_raw.png")):
            fid = path.stem.split("_")[-2]  # sf_f07_raw -> f07
            frames.append(fid)

    promoted = []
    for fid in frames:
        out = promote_one(fid)
        promoted.append(str(out))
        print(f"Promoted {fid} -> {out}")

    if not promoted:
        print("No raws found to promote.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
