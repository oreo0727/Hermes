# 3D Pipeline & Lookdev Plan  Campfire Repeat

Goal: Fast, stylized 3D short (57 min) with repeatable NPR look. Prioritize iteration speed and consistent mood.

Core Stack
- DCC: Blender 4.x
- Renderer: Eevee (real-time), with selective Cycles stills if needed for hero frames.
- Shading: NPR/toon (diffuse ramp, spec ramp), rim/kicker lights, screen-space AO, subtle film grain in comp.
- FX: Ember particles, fog volumes (fog cards + low-density world volume), match-flare glare.

Environment
- Forest: Geometry Nodes to scatter stylized conifers/deciduous on a low-poly terrain. LODs for depth. Add star dome + crescent moon.
- Camp Set: Fire ring (stones), logs/chairs, backpacks, tent (olive dome), wood arrow sign on tree (pine icon), lantern practical L/FG, mugs, bedroll; hero props with baked normals for detail at low poly.
- Lighting: HDRI moonlight base (0.12), key from fire (animated area/mesh + emissive), lantern practical (~35% of fire), blue env fill; cool rim from back-left moon; contact shadows around rock ring.

Characters
- Style: Mid-poly stylized teens (NPR-friendly). Simple facial rigs (brows/mouth shapes).
- Rigs: Mixamo auto-rig + Blender retarget or Rigify-lite. Emphasis on seated/standing, handheld phone holds.
- Costumes: Distinct silhouettes (hoodie, beanie, flannel, puffer, varsity jacket) with readable color accents.

Cameras
- 35mm/50mm primaries; occasional 24mm wide for environment. Handheld noise (subtle). DOF for phone inserts.
- Phone POV: Emulated sensor (1/50, slight rolling-shutter feel), UI overlays added in comp.

Lookdev Checklist
- Shader ramp tables locked (skin, cloth, bark, stone).
- Fire look: Sprite flipbook + emissive bloom + light flicker driver (sine + noise). Coals: blackbody gradient.
- Volumetrics: Light fog planes between tree rows; avoid heavy world volumes for Eevee speed.

Editorial & Audio
- Edit in Resolve or Blender VSE. 24 fps timeline. Export 16:9 master with 9:16 centersafe guide.
- SFX: wind, insects on/off, ember crackle, lighter, breath. Music: low drones + two-note motif. Headphone-first mix.

AI Assist (ethical, disclosed)
- Storyboards/styleframes: image gen for exploration; final look locked in 3D.
- Texture assists: generate stylized bark/cloth bases for later baking.
- VO: TTS for animatic; swap to recorded or premium TTS for final.

Schedule (indicative)
- Day 1: Boards + lookdev sprint (shader ramps, fire, fog). Block camp set.
- Day 2: Character proxy rigs, layout, first animatic pass (phones as light).
- Day 3: Lighting polish, ember/fog passes, loop montage edit.
- Day 4: Final animation tweaks, comp, grade, rough mix.
- Day 5: Polish mix, captions, exports (16:9 + verticals).

Acceptance Gates
- SubRated R guardrails respected (no gore).
- Battery-persistence visual beat clearly readable.
- Loop rule visually legible by beat 4.
- 16:9 master with vertical-safe action.
