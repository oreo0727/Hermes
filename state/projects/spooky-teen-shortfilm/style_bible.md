# Style Bible v0 (Animated, Sub–Rated R)

Look Summary
- Stylized 3D NPR/toon with purposeful analog grit. Warm/cool split: campfire and lantern warms vs. moonlit cool blues. Clean shapes with readable silhouettes.
- Rating ceiling: PG-13; suspense-forward. No graphic gore.

Framing & Aspect
- Master at 16:9; maintain center-safe action for 9:16 and 1:1.
- Phone POV sequences framed to read even in vertical crop.

Palette (woods, inspired by ref)
- Sky night blue #0B2344; moon #D6E6FF; star specks #F7FAFF.
- Trees deep pine #233E31; trunks #5A412D; tent olive #556F4B.
- Fire core #FF8A2D; flame mid #FFB65A; ember #FF6A2B; ash glow #FFC97A.
- Lantern metal #1C6B64; lantern glass glow #FCE7A6.
- Ground mix granite gray #7A7C7B / cool shadow #4E555B; needles/browns #7B6A4A.
- Clothing base (camo/utility): dark olive #4D5A3E, mid olive #6E7756, khaki brown #7B6A4A; boots #3A2F24.

Animation Approach
- 12–24 fps mix: dialogue at 12–16 fps stepped; tension beats smoothed to 24 fps.
- Camera: medium-wides and inserts; subtle handheld noise on some CUs; gentle push-ins at key beats.
- Post: subtle grain; minimal chroma aberration; controlled bloom on fire/lantern.

Lighting & Materials (inspired by ref)
- Keys: Campfire (2100–2300K) as dominant; Lantern practical (2800–3000K, ~35% of fire) on left FG.
- Rim/Kicker: Moonlight (8000–9000K) from back-left/top; cool edge on hair/hoods/tent.
- Ambient/Sky: very low cool fill; maintain 6:1 key-to-fill; subject-to-background up to ~10:1 in shadows.
- Materials: NPR ramps per lookdev; retain headroom in warm highlights; animated normals/spec for flicker.

Set Silhouettes & Props
- Central fire + rock ring; two seating logs in semicircle; dome tent back-center; wood arrow sign on a tree (pine icon); lantern left FG; backpacks/bedrolls; roasting stick/marshmallow.

SFX & Music
- Signature motif: low drone + two-note cell; campfire crackle; insects cut to silence; lighter click button.
- Mix calibrated for headphones first.

Do / Don’t
- Do: preserve iconic warm/cool split, readable silhouettes, and practicals-as-anchors.
- Don’t: flatten backgrounds with over-ambient; avoid clipping in fire cores.

---

## Style Bible v1 (Photographic Styleframes Target)

Palette (hex)
- Fire warm ramp: #FF8A3C, #FFC27A, #FFD8A8
- Lantern warm: #F3B66B
- Moon/night ramp: #0A1220, #12233C, #214168, #6EA2FF
- Forest earth: #0E2A1F, #1B3A2E, #4B5A4F, #6B6F5C

Lens / DOF
- Ensembles (F05, F10): 28–35mm, f/2.8–4.0 (natural perspective, readable group)
- OTS phone (F07): ~50mm, f/1.8–2.0 (phones key the face/hands)
- Macro embers (F09): 85–100mm, f/4–5.6 (shallow but controlled)

Grain / Texture
- Fine 35mm grain (10–15% strength), subtle halation on warm practicals (fire, lantern, match/pocket glow)
- Light smoke/embers; avoid heavy chromatic aberration

Grade / LUT
- Base: ACEScct
- Creative: Orange/Teal split — warm pole limited to practicals/skin, cool pole for moonlit rims and shadows
- Highlights: protect fire cores; clamp/bloom gently; maintain skin texture

Lighting Beats (see lookdev/lighting_rigs.yaml)
- Fire key dominant in F02/F05; phones-only beats F07/F08 (lantern off, fire out); dawn pocket glow F10

Framing / Delivery
- Render at 1920×1088 then crop to 1920×1080 (top-crop 8px). Keep center-safe for 9:16 extracts.

Acceptance Anchors per Frame
- F02 First strike — Tent back-center; lantern left FG; right-side sign; central fire flare; warm key + cool rim
- F05 All together — Five teens readable; tent back-center; lantern left FG; sign right; central fire
- F07 Live photo find — OTS phone lights; tent silhouette; lantern off; deep cool rim only
- F08 Phones only — No fire/lantern; phones as keys; blue ambient rim
- F09 Almost ignition — Macro embers; shallow DOF; no characters
- F10 Dawn pocket glow — Pre-dawn cool; ember bed; lantern low; tent back-center


## Styleframes v1 — Lookdev Targets
- Palette: Fire Warmths #FF9E5E, #FFC48E; Moon Rims #89A7FF; Forest #0B3D2E, #2C3553; Night Skin #E7B8A0
- Lens: 35mm equivalent, f/2.8; phones-only beats use practicals + darkness.
- DOF: Mid-shallow; tent readable; teens grouped at fire.
- Grain: 0.6 (filmic, not CCTV).
- Grade/LUT: Teal-Orange filmic S-curve; preserve moon blues, avoid magenta cast.


---

## v1 Packaging Notes (current pass)
- Palette confirms: Fire #FF8A3C/#FFC27A/#FFD8A8; Moon #AFC8FF; Forest #0E2A1F/#1B3A2E; Night skin #E7B8A0
- Lens/DOF: Ensembles 28–35mm at f/2.8–4.0; phones-only OTS ~50mm at f/1.8–2.0
- Grain: fine 35mm, 10–15%; controlled halation on practicals
- Grade/LUT: ACEScct base; gentle teal/orange split; clamp fire cores; preserve moon blues
- Delivery: Render 1920×1088, crop to 1920×1080 (top-crop 8px)

(Updated: 2026-05-25T13:26:51.136121)
