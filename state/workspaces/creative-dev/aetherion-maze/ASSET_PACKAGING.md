Aetherion Maze — Asset Packaging Plan (HTML5 Canvas Loader)

Verdict: The provided composite image is a labeled reference board, not runtime-ready art. It contains mixed scales, presentation layout, and likely baked labels/backgrounds; none of these are suitable for direct loading. We will convert the board into a catalog-first package per this plan.

Primary target (preferred default)
- Option A — Loose transparent PNGs organized in folders (64×64 base). This is the canonical delivery format for game-dev.

Alternate targets (supported via the same manifest schema)
- Option B — Uniform 64×64 grid atlas (power-of-two canvas) + atlas JSON (rects implied by grid).
- Option C — Texture atlas PNG (arbitrary rects) + atlas JSON (explicit rects).

Global specs (apply to all options)
- Tile size: 64×64 px.
- Color: 32-bit RGBA, premultiplied alpha not required (straight alpha preferred).
- Safe border: 2 px transparent padding around every sprite to prevent bleed.
- Spacing on atlases: 2 px between cells if using B/C.
- Anchors: origin (0.5, 0.5) center for all sprites unless noted.
- Naming: kebab-case with numeric frame suffixes starting at 0 (e.g., hero-walk-n-0). Do not mix underscores.
- Animation grouping: frames share the same base key; order is numeric ascending.
- Layers/roles: only floor and walls are TileMap tiles. All others are entities/effects/UI layers.
- Folder root: assets/painted/… under the project repo.

Folder layout (Option A)
- assets/painted/
  - tilemap/
    - ground/
      - dirt/
        - dirt-0.png
      - grass/
        - grass-0.png
    - walls/
      - wall-h.png
      - wall-v.png
      - wall-tl.png
      - wall-tr.png
      - wall-bl.png
      - wall-br.png
      - wall-endcap.png
      - wall-door.png
  - decorations/
    - tree-cluster.png
    - rock-cluster.png
    - bush.png
    - flowers.png
  - hero/
    - idle/
      - hero-idle-n-0.png
      - hero-idle-e-0.png
      - hero-idle-s-0.png
      - hero-idle-w-0.png
    - walk/
      - hero-walk-n-0.png
      - hero-walk-n-1.png
      - hero-walk-e-0.png
      - hero-walk-e-1.png
      - hero-walk-s-0.png
      - hero-walk-s-1.png
      - hero-walk-w-0.png
      - hero-walk-w-1.png
  - enemies/
    - skeleton/
      - skeleton-idle-0.png
      - skeleton-walk-0.png
      - skeleton-walk-1.png
    - goblin/
      - goblin-idle-0.png
      - goblin-walk-0.png
      - goblin-walk-1.png
  - items/
    - chest.png
    - key.png
    - potion.png
    - shield.png
    - crystal.png
  - traps/
    - spikes.png
  - effects/
    - portal-0.png
    - portal-1.png
    - portal-2.png
    - portal-3.png
    - speed-bolt.png
    - magic-orb.png
  - ui/
    - heart.png
    - coin.png
    - key-icon.png
    - shield-icon.png

Roles and layers
- TileMaps (grid-aligned): tilemap/ground/* (layer: tilemap-floor), tilemap/walls/* (layer: tilemap-walls)
- Entities (spawned objects): hero/*, enemies/*, items/*, traps/* (layer: entities)
- Effects: effects/* (layer: fx)
- UI: ui/* (layer: ui)

Acceptance checklist (Option A)
- Each PNG is 64×64 with 2 px transparent safe border; alpha silhouettes are clean (no matte halos).
- Filenames are kebab-case, frames 0-indexed, directions in {n,e,s,w} suffix order.
- Only tilemap/* assets are grid tiles; others are free-positioned entities.
- Anchors default to center; characters/effects visually rest on ground with baked AO.

Atlas options (B/C) — explicit JSON schema
- File: assets/painted/atlases/atlas-64.png (+ optional @2x variant) and assets/painted/atlases/atlas-64.json
- Schema (see atlas_spec_template.json for a complete template):
  {
    "meta": {
      "image": "assets/painted/atlases/atlas-64.png",
      "tile_size": 64,
      "type": "uniform-grid" | "rects",
      "power_of_two": true,
      "grid": {"cols": N, "rows": N, "padding": 2, "spacing": 2},
      "origin": [0.5, 0.5],
      "version": "1.0"
    },
    "frames": {
      "<canonical-id>": {
        "rect": [x, y, w, h],
        "layer": "tilemap-floor" | "tilemap-walls" | "entities" | "fx" | "ui",
        "type": "tile" | "entity" | "effect" | "ui",
        "tags": ["ground", "grass"],
        "pivot": [0.5, 0.5],
        "collider": null | {"shape": "rect", "x": 0, "y": 48, "w": 64, "h": 16}
      }
    },
    "animations": {
      "hero-walk-n": {"frames": ["hero/walk/hero-walk-n-0", "hero/walk/hero-walk-n-1"], "fps": 8, "loop": true}
    },
    "aliases": {}
  }

Required role coverage
- walls: h, v, tl, tr, bl, br, endcap, door
- ground: dirt, grass
- decorations: tree-cluster, rock-cluster, bush, flowers
- hero: idle (n,e,s,w), walk (n,e,s,w)
- enemies: skeleton (idle, walk), goblin (idle, walk)
- items: chest, key, potion, shield, crystal
- traps: spikes
- effects: portal, speed-bolt, magic-orb
- ui: heart, coin, key-icon, shield-icon

Submission
- Deliver Option A by default under assets/painted/… matching the folder layout above. If delivering B/C, also include assets/painted/atlases/atlas-64.png and atlas-64.json conforming to the schema.
