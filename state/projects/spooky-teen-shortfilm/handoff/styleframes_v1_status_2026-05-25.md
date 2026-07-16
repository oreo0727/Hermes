# Styleframes v1 — Lane Status (2026-05-25)

Artifacts ready for review
- Storyboards v3 contact: /home/james/Hermes/state/projects/spooky-teen-shortfilm/storyboards/storyboard_contact_v3.png
- Animatic v3 (no audio): /home/james/Hermes/state/projects/spooky-teen-shortfilm/artifacts/animatic_v3_noaudio.mp4
- Styleframes v1 contact (current): /home/james/Hermes/state/projects/spooky-teen-shortfilm/styleframes/styleframes_contact_v1.png

What is visibly on screen
- Storyboards v3: Clear anchors across frames — lantern left foreground, tent back-center, right-side wooden camp sign, central fire ring; phones-only light in F08; Live Photo OTS in F07; macro embers in F09.
- Styleframes v1: 3×2 grid labeled F02, F05, F07, F08, F09, F10 with yellow PLACEHOLDER / WIP markers and repeated "WIP" text; no rendered characters or camp elements yet.

Creative-dev dispatch outcome
- Multiple supervised attempts failed the evidence gate (responses did not name what is visibly on screen). Current tiles remain WIP placeholders.

Known blockers (from lane)
- Prior: OpenAI/httpx 'proxies' kwarg mismatch; project venv pins now applied: httpx==0.27.2, httpcore==1.0.4, openai==1.16.1.
- Practical: No ffmpeg/ImageMagick on host (not required for image-gen, only for mux/cropping).
- Procedural: Lane replies fail the "name visible evidence" check.

Proposed next actions (pick one)
1) Evidence-wrapper fix (preferred): add a small operator wrapper that auto-attaches a contact + one sf_* PNG and asserts a vision-derived evidence line before the lane reply is accepted.
2) Accept WIP placeholders for now: proceed with timing review on animatic v3; pause styleframes until a working image-gen path is confirmed.
3) Approve alt image-gen path: provide access to a known-good image-gen environment or container; re-dispatch creative-dev there.
4) Optional: approve ffmpeg install to enable subtitle mux/cropping convenience.

Owner: operator
Status: paused on creative-dev evidence gate; no further dispatch loops until an unblock is approved.
