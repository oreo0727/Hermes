# Sheldon Troubleshooting Left-Off

Last updated: 2026-05-13

## Goal

Keep Sheldon usable as the primary operator contact in the Hermes portal while we continue Maze-related work.

## Current state

- Hermes operator gateway is the live Sheldon backend.
- Hermes operator portal is the UI surface at `http://127.0.0.1:8799/`.
- Current Aetherion review build is being served locally at `http://127.0.0.1:8000/godot-web/`.
- The project currently being routed through Sheldon is `aetherion-maze`.

## What was fixed

### Timeout and stuck-run behavior

- The portal foreground chat path was effectively too fragile for long operator requests.
- The specialist bridge could leave dispatch records stuck in `running` if a timeout or unexpected exception happened outside the narrow handled cases.
- We updated:
  - `hermes_stack/operator_portal/server.py`
  - `scripts/hermes-specialist-bridge.py`
- Result:
  - Portal uses the profile-aware timeout path instead of an overly short fixed request window.
  - Specialist dispatches now finalize as `failed` on timeout/error instead of hanging forever.
  - Old stale dispatch records from 2026-05-12 were cleaned up.

### Portal quick-chat reliability

- The Sheldon quick chat in the portal was producing `TypeError: Failed to fetch` during execution-heavy requests.
- The main mitigation was in:
  - `hermes_stack/operator_portal/static/app.js`
- Result:
  - Heavy operator requests such as “restart”, “fix”, “work on”, “coordinate”, “use other agents”, or long prompts now auto-route to the background-run endpoint instead of the fragile foreground chat path.

### Sheldon quick-chat usability

- The Sheldon docked chat was too small and hard to read.
- We updated:
  - `hermes_stack/operator_portal/static/index.html`
  - `hermes_stack/operator_portal/static/styles.css`
  - `hermes_stack/operator_portal/static/app.js`
- Result:
  - Quick chat has an `Expand` toggle.
  - Docked mode is wider by default.
  - Expanded mode is much larger and persists via local storage.

### Sheldon response verbosity

- Sheldon was writing overly long responses.
- We updated the operator persona prompt in:
  - `hermes_stack/operator_portal/static/app.js`
- Result:
  - Shorter default responses.
  - Important info first.
  - Long answers should only happen when explicitly requested.

### Project tracking visibility

- Hermes project cards did not expose a clear “where are we now?” view.
- We updated:
  - `hermes_stack/projects.py`
  - `hermes_stack/operator_portal/static/app.js`
  - `hermes_stack/operator_portal/static/styles.css`
  - `state/projects/aetherion-maze/project.json`
- Result:
  - Project cards now show:
    - `Now`
    - `Next`
    - `Owner`
    - `Blocked`
    - `Done`
    - `Percent`

## Current Aetherion tracking state

- Project: `aetherion-maze`
- Owner: `game-dev`
- Now: Polish the live Maze Forest review build and keep the web review loop stable in the portal.
- Next: Push Godot TileMap and actor polish to the web export, then review parity against the Maze Forest reference build.
- Blocked:
  - Need visual review feedback on the current Maze Forest pass to decide what to tune next.
- Done:
  - Maze Forest and Narrative Maze reviewable web builds exist under the project root.
  - Sheldon background runs, specialist dispatch tracking, and quick-chat ergonomics were stabilized in the portal.
- Percent: `72`

## Files touched during troubleshooting

- `hermes_stack/operator_portal/server.py`
- `scripts/hermes-specialist-bridge.py`
- `hermes_stack/operator_portal/static/app.js`
- `hermes_stack/operator_portal/static/index.html`
- `hermes_stack/operator_portal/static/styles.css`
- `hermes_stack/projects.py`
- `tests/test_projects.py`
- `state/projects/aetherion-maze/project.json`

## Fast resume checklist

1. Check portal:
   - `systemctl --user status hermes-operator-portal.service --no-pager -l`
2. Check Sheldon backend:
   - `systemctl --user status hermes-operator-gateway.service --no-pager -l`
3. Check project/lane summary:
   - `python3 ./scripts/hermes-run-status.py --project-id aetherion-maze`
4. Check portal bootstrap payload:
   - `curl -sS http://127.0.0.1:8799/api/bootstrap`
5. Check Maze review server:
   - `curl -i http://127.0.0.1:8000/maze-forest/`

## Known good URLs

- Portal: `http://127.0.0.1:8799/`
- Aetherion review build: `http://127.0.0.1:8000/godot-web/`

## Known tests/verification already run

- `python3 -m unittest /home/james/Hermes/tests/test_projects.py`
- `node --check /home/james/Hermes/hermes_stack/operator_portal/static/app.js`
- Portal bootstrap confirmed new tracking fields after portal restart.

## Likely next troubleshooting targets

- If Sheldon quick chat still feels unreliable, inspect whether the specific request is incorrectly going through `/api/chat` instead of `/api/runs`.
- If background operator runs feel slow or too wordy, tighten the operator prompt further in `hermes_stack/operator_portal/static/app.js`.
- If project tracking drifts, add a real status-update flow so Sheldon can write back `Now/Next/Blocked/Done` automatically after major runs.
- If Maze work resumes, use the `Projects` tab plus `Sheldon Runs` and `Specialist Dispatches` together instead of relying on chat history alone.

## If picking this up cold

Start here:

1. Hard refresh the portal at `http://127.0.0.1:8799/`.
2. Open `Projects` and confirm `aetherion-maze` still shows the tracking block.
3. Open Sheldon quick chat and confirm:
   - it is wider,
   - `Expand` works,
   - replies are shorter.
4. If troubleshooting continues, compare portal UI behavior against:
   - `/api/bootstrap`
   - `/api/runs`
   - `/api/chat`
