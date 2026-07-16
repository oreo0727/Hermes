# Asset Package Readiness Contract

Use this before Sheldon, `creative-dev`, or `game-dev` treats an art input as shippable runtime data.

## Classification

Every referenced sprite-related input must be classified as exactly one of:

- `reference-board`
- `loose-sprites`
- `uniform-grid-sheet`
- `atlas-plus-manifest`
- `unknown`

## Immediate rejection rules

If any of these are true, the input is **not** build-ready and must be called out plainly:

- labels or captions are baked into the image
- section dividers or presentation panels are visible
- notes, legends, or sizing callouts are included
- a mood-board or screenshot background is baked in
- animation frames are shown for humans but no machine-readable packing is provided
- grid size, cell geometry, or atlas coordinates are unknown

In those cases, classify it as `reference-board` unless a stronger category is proven.

## Accepted production formats

An input is build-ready only if it is one of:

- `loose-sprites`
  - separate transparent assets with stable names
- `uniform-grid-sheet`
  - one sheet with known rows, columns, and cell size
- `atlas-plus-manifest`
  - one image plus machine-readable coordinates or frame names

## Required behavior from Sheldon and specialists

- Say the classification explicitly before claiming integration is possible.
- If the asset is not build-ready, stop the bad integration path instead of guessing.
- Name the missing production artifact exactly.
- Route `creative-dev` to packaging or extraction work when needed.
- Route `game-dev` only against machine-usable art.

## Example verdict for the Discord board

Classification: `reference-board`

Why:

- labeled sections
- baked presentation background
- human-readable notes
- no runtime atlas manifest
- no proof of uniform machine-usable grid geometry

Result:

- valid as visual/spec reference
- invalid as direct game runtime sheet
