# Video provider status

Updated: 2026-07-17T20:13:32.909413+00:00
Selected provider: `local_motionfx`
Cost posture: `free`
Primary artifact: `artifacts/animatic_v3_motionfx.mp4`

Why:
- Local procedural motion/flicker/glow builder is available and needs no external account.

Fallback order:
- `local_motionfx` first because it is free, reproducible, and available on this host.
- `huggingface_remote` when a token/quota is present.
- `huggingface_local_gpu` when a suitable GPU is visible.
- `openai_sora_experimental` only as an optional paid/deprecated API experiment.
- `manual_dropbox` for user-generated clips dropped into the project artifacts.

Verification:
- first_frame_size=1920x1080; ffprobe unavailable, verified first frame with imageio
