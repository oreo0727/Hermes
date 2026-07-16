
# Midnight Signals — Styleframes v1 Brief (Placeholder)

This is a placeholder Styleframes v1 package derived from Storyboards v3. Image generation/editing tools are unavailable in this environment; therefore the contact sheet is a diagrammatic PNG with per‑tile overlays, and the manifest maps each tile to the exact board source.

Do not treat the contact sheet as final styleframes. It exists to lock tone, lighting, and lens/grade before animatic and image‑gen.

## Palette
- Fire warm: #FF8A3C, #FFC27A, #FFD8A8
- Lantern warm: #F3B66B
- Moon/night: #0A1220, #12233C, #214168, #6EA2FF
- Forest earth: #0E2A1F, #1B3A2E, #4B5A4F, #6B6F5C

## Lens / DOF
- 28–35mm for ensembles (f05, f10); 50mm OTS (f07); 85–100mm macro (f09)
- f/2.8–4 groups; f/1.8–2.0 OTS; f/4–5.6 macro. Shutter 1/48–1/60.

## Grain / Texture
- Subtle 10–15% film grain; add halation on warm sources (fire, lantern, match, pocket glow).

## Grade / LUT
- ACEScct base; creative Orange/Teal split: warm pole limited to practicals/skin, cool pole to moonlit rims/shadows; clamp highlights to preserve texture.

## Layer Cues by Frame
- f02 First strike — Warm flare bloom on faces; cool moon fill on tent/trees; wisp of smoke.
- f05 All together — Five teens clear; lantern left; sign right; warm fire key + cool moon rim.
- f07 Live Photo find — OTS phone cool key; keep device UI legible; treeline silhouette appears on phone.
- f08 Phones only — Phones are the only keys; fire/lantern off; deep blue ambient rim; sign/tent silhouettes.
- f09 Almost ignition — Macro embers/sparks; shallow DOF; no characters.
- f10 Dawn pocket glow — Pre‑dawn cool ambient; subtle warm pocket glow; lantern low; ember bed.

## Acceptance Cross‑check (current run)
- Status: All six styleframes are present at 1920x1080 (IHDR‑verified) at styleframes/v1/ (f02,f05,f07,f08,f09,f10). Contact sheet remains a labeled PLACEHOLDER 2x3 grid pending thumbnail embed.
- Evidence: Visual verification performed on sf_f07_raw.png (1536x1024) — OTS phone lock screen (10:12, Tuesday, April 23), tent left, lantern glowing left, central campfire with group, right‑side wooden sign, cool ambient rim; matches anchors and lens for f07. Vision analyzer rejected cropped finals (1920x1080) with a parser error, so we used the raw for evidence while retaining the 1920x1080 finals.
- Five teens rendered as characters: Reads in f05 (five teens around central fire) and f10 (group silhouettes with pocket glow). f02 shows a close group around a match flare. f08 intentionally minimizes group visibility with phones‑only keys.
- Camp anchors (tent back‑center, lantern left FG, right‑side sign, central fire): Present/readable in f05 and f10; silhouettes/placements read in f08; f02 shows tent/lantern contextually.
- Lighting beats: f02 match flare bloom on faces; f08 phones‑only darkness with deep blue ambient rim; f10 subtle pocket glow at pre‑dawn with low lantern and ember bed; f05 warm fire key plus cool moon rim.

Next: Optionally re‑encode cropped finals with Pillow for analyzer compatibility and refresh the 2x3 contact sheet with real thumbnails once Pillow is available in /home/james/Hermes/state/projects/spooky-teen-shortfilm/.venv.
