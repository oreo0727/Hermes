# Shader Ramps v0 (Eevee NPR)

Skin Ramp (diffuse)
- Stops: 0.00 #0D0D12 (shadow), 0.35 #343446 (mid), 0.65 #6C6C86 (lit), 0.92 #D7C8B8 (key)
- Spec Ramp: 0.70 #111317, 0.88 #3A404B, 0.96 #9DA6B6

Cloth Ramp (hoodie/flannel)
- Hoodie: #0A1B2A -> #1C3A52 -> #386A89 -> #7DB3D1
- Flannel: #25181A -> #4D2E33 -> #86464D -> #D68A84

Bark/Tree Ramp
- #080C0E -> #16242B -> #2F3E43 -> #596C6F

Stone Ramp
- #0E1216 -> #1E2A33 -> #3A4A55 -> #6A7E8F

Rim/Kicker
- Cool rim: #7EB7FF at 0.15 strength; Warm fire rim: #FFB168 at 0.25 strength (animated)

Fire/Emissive
- Fire emissive: #FFB168 -> #FF7A3C -> #FF3C1E (noise-driven)
- Coals: blackbody gradient 800K600K with sporadic spikes

Post
- Film grain subtle; chromatic aberration 0.0015; vignetting 0.12; glare for match whoosh only
