# Maze Forest Asset Pack (Cozy Painterly)

This pack provides painterly, rounded, cozy-forest sprites for a 64x64 base grid (with optional @2x). Assets are hand-crafted via procedural brushes to match a soft, fantasy style with gentle ambient occlusion and readable gameplay silhouettes.

Contents
- sheets/spritesheet.png and sheets/spritesheet@2x.png
- sheets/spritesheet.json (atlas with origin [0.5,0.5], animations listed as <name>.anim entries)
- sprites/ (individual PNGs; each tile includes a 2 px transparent safe border)
- meta/swatches.png and meta/swatches.json (approx palette)

Style and tech
- Painterly textures, rounded forms, soft top-left lighting, AO under walls/props.
- Hazards use higher-contrast/specular metals; magic items glow (purple/blue); loot is warm gold.
- Transparent PNGs, neutral gamma. Padding: 2 px inner safe border and 2 px sheet spacing to avoid atlas bleeding.
- Anchors: centered ([0.5, 0.5]) for all entries.

Naming
- Kebab-case per directories (terrain/, pickups/, hazards/, player/, enemies/, fx/, ui/).
- Animated sequences exported as name-1..N. Atlas also includes <base>.anim with frames[].

Licensing
- Original work by Creative Dev for Project Aetherion.
- Royalty-free, perpetual license for Project Aetherion use across platforms.
- Redistribution outside Project Aetherion permitted only with this README and attribution to Project Aetherion (optional but appreciated).

Usage notes
- Use additive blending for fx/glow_*.
- Animated items are 4–8 frames, loop at 8–12 FPS for cozy feel (portal at ~10–12 FPS).
- Tile-lightning includes base + 2 pulse frames. Spikes-plate is a 4f raise/lower loop; spikes-plate-half is a low-profile static variant.
- Player/enemy sprites are chibi silhouettes with strong separation from greens for readability.

Attribution
- Palette approximations based on provided color guidance.
