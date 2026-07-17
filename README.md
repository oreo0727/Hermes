# Hermes

Standalone Hermes control plane for the living specialist-agent stack.

This top-level project exists so the Hermes runtime, portal, workspaces, and
profile homes can live independently of `openclaw` and `openclaw-next`.

## What Lives Here

- Hermes profile homes for:
  - `operator`
  - `app-dev`
  - `game-dev`
  - `creative-dev`
- persistent project roots under `state/projects/`
- standalone workspaces under `state/workspaces/`
- standalone policy file under `config/policies/workspace-roots.json`
- repo-managed Hermes virtualenv under `state/hermes/venv`
- repo-level runtime storage config under `state/hermes/runtime.env`
- Discord-first command center for multi-agent oversight
- bootstrap logic that can import existing OpenAI and Discord credentials from
  `openclaw-next` one time, then run independently

## Layout

```text
Hermes/
├── README.md
├── Makefile
├── config/
│   └── policies/
│       └── workspace-roots.json
├── docs/
│   ├── hermes-upgrade-blueprint.md
│   ├── hermes-vision-v1-20260526.md
│   ├── hermes-v2-agent-contract-20260526.md
│   ├── hermes-v2-capability-matrix-20260526.md
│   └── hermes-v2-outline-20260526.md
├── agents/
│   ├── sheldon/
│   ├── penny/
│   ├── raj/
│   └── leonard/
├── hermes_stack/
│   ├── __init__.py
│   ├── agents.py
│   ├── scaffold.py
│   └── operator_portal/
│       ├── __init__.py
│       ├── server.py
│       └── static/
│           ├── app.js
│           ├── index.html
│           └── styles.css
├── scripts/
│   ├── bootstrap-hermes.sh
│   ├── install-hermes.sh
│   ├── run-hermes.sh
│   ├── run-hermes-dashboard.sh
│   ├── run-hermes-gateway.sh
│   └── run-operator-portal.sh
└── state/
    ├── projects/
    ├── hermes/
    └── workspaces/
```

## Bootstrap

```bash
cd /home/james/Hermes
./scripts/bootstrap-hermes.sh
./scripts/install-hermes.sh
```

The install step also prepares PostgreSQL support for the Hermes control plane.

The bootstrap script seeds new standalone profile homes and can optionally
import existing local OpenAI and Discord secrets from:

- `/home/james/openclaw-next/config/env/local/`

Only import from an old repo if you explicitly point at it:

```bash
HERMES_SEED_SOURCE=/home/james/openclaw-next ./scripts/bootstrap-hermes.sh
```

## Run

Start the living-agent stack:

```bash
./scripts/run-hermes-gateway.sh operator
./scripts/run-hermes-gateway.sh app-dev
./scripts/run-hermes-gateway.sh game-dev
./scripts/run-hermes-gateway.sh creative-dev
./scripts/run-operator-portal.sh
```

For an always-on setup that survives terminal closes and automatically restarts
Sheldon if the operator gateway crashes or the portal stops responding, install the
user services:

```bash
make services-install
```

That installs and starts:

- `hermes-operator-gateway.service`
- `hermes-operator-portal.service`
- `hermes-operator-watchdog.timer`

Check them with:

```bash
systemctl --user status hermes-operator-gateway.service
systemctl --user status hermes-operator-portal.service
```

If you want Hermes to come back after a reboot even before you log in, enable
linger for your user:

```bash
sudo loginctl enable-linger $USER
```

Optional dashboards:

```bash
./scripts/run-hermes-dashboard.sh operator
./scripts/run-hermes-dashboard.sh app-dev
./scripts/run-hermes-dashboard.sh game-dev
./scripts/run-hermes-dashboard.sh creative-dev
```

## Projects

Hermes now treats projects as first-class state alongside profile homes.

Create a project root with the built-in scaffold:

```bash
python3 -m hermes_stack.scaffold --root-dir . create-project \
  --project-id ember-atlas \
  --title "Ember Atlas" \
  --summary "Story, app, and game development workspace for the Ember Atlas universe." \
  --specialists operator,creative-dev,game-dev,app-dev
```

Or use `make`:

```bash
make create-project PROJECT_ID=ember-atlas TITLE="Ember Atlas" SPECIALISTS=operator,creative-dev,game-dev,app-dev
```

Update a project as work moves:

```bash
python3 -m hermes_stack.scaffold --root-dir . update-project \
  --project-id ember-atlas \
  --owner game-dev \
  --status active \
  --now "Finish the first playable combat loop." \
  --next "Package a review build and collect operator feedback." \
  --blocked "Need final enemy sprite direction." \
  --done "Project scaffold created." \
  --percent 18 \
  --priority 72
```

Or use `make`:

```bash
make update-project PROJECT_ID=ember-atlas OWNER=game-dev STATUS=active NOW="Finish the first playable combat loop." NEXT="Package a review build and collect operator feedback." BLOCKED="Need final enemy sprite direction." DONE="Project scaffold created." PERCENT=18 PRIORITY=72
```

Each project gets:

- `brief.md`
- `canon.md`
- `roadmap.md`
- `app/`
- `game/`
- `creative/`
- `artifacts/`
- `runs/`

Hermes is designed so Sheldon can use these project records as the studio control plane:

- bind incoming work to an existing or new project
- route specialists against the bound project id
- keep `owner`, `now`, `next`, `blocked`, `done`, `status`, and `percent` current
- manage multiple projects without losing continuity in chat history

## Command Center

The local portal runs at:

- `http://127.0.0.1:8799`

Hermes is now meant to be operated Discord-first:

- Discord is the primary conversation surface for Sheldon
- the browser is a character-led management deck for oversight, queue steering, proof, and recovery
- the portal should not be the place where normal work has to happen

The command deck shows:

- the focused slice and proof state
- the v2 agent team and lane ownership
- portfolio queue and project focus controls
- recent runs, dispatches, and monitor alerts
- proof, artifacts, and recovery context when something drifts

## Vision

The current north-star docs live here:

- `docs/hermes-vision-v1-20260526.md`
- `docs/hermes-v2-agent-contract-20260526.md`
- `docs/hermes-v2-capability-matrix-20260526.md`
- `docs/hermes-v2-outline-20260526.md`

## Operator Helpers

Sheldon can delegate into the specialist lanes directly from the operator lane:

```bash
python3 ./scripts/hermes-specialist-bridge.py --profile app-dev --project-id my-project --prompt "Ship the next implementation slice."
python3 ./scripts/hermes-specialist-bridge.py --profile game-dev --project-id my-project --prompt "Build the next playable loop slice."
python3 ./scripts/hermes-specialist-bridge.py --profile creative-dev --project-id my-project --prompt "Draft the next creative package."
```

For portal and Discord status updates, Sheldon can inspect live lane health plus
background runs:

```bash
python3 ./scripts/hermes-run-status.py
python3 ./scripts/hermes-run-status.py --project-id my-project
```

## Postgres Control Plane

Hermes can store its control-plane metadata in PostgreSQL instead of JSON files
for:

- project manifests
- portfolio state
- portal runs
- specialist dispatches
- agent memory nodes and synapses

Project artifacts, workspace outputs, and larger source trees still stay on
disk.

Switch this repo to Postgres mode:

```bash
make configure-postgres
```

That writes the runtime config to `state/hermes/runtime.env`. By default Hermes
uses the local Unix-socket database URL:

```bash
postgresql:///hermes_control
```

You can override it:

```bash
make configure-postgres DATABASE_URL="postgresql://user:pass@host:5432/hermes_control"
```

On first use, Hermes auto-creates the Postgres schema and imports the current
JSON control-plane records. The old files are left in place as a rollback
safety net.

## Agent Memory Graph

Sheldon, Penny, Raj, and Leonard keep their existing personality and lane
definitions as identity anchors. Hermes now seeds a SQL-backed memory graph
around those anchors:

- `hermes_agents` stores each character's stable identity, lane, voice, role,
  tools, artifacts, verification method, and closure rule.
- `hermes_memory_nodes` stores durable facts such as SOUL contracts, system
  prompts, profile memories, operator preferences, memory buckets, and project
  context.
- `hermes_memory_synapses` stores weighted relationships between those nodes,
  such as `expresses_personality`, `governs_behavior`,
  `serves_operator_preference`, and `recalls_project_context`.

Seed or refresh the memory graph:

```bash
make seed-memory
```

Inspect one agent's graph:

```bash
make memory-summary PROFILE=sheldon
make memory-summary PROFILE=operator
```

## Cognitive Kernel

The memory graph stores what the agents know. The cognitive kernel records how
that knowledge gets used over time:

- `hermes_cognitive_events` stores meaningful observations and state changes.
- `hermes_cognitive_facts` stores structured beliefs about agents, projects,
  user preferences, and closure rules.
- `hermes_cognitive_procedures` stores reusable playbooks for each lane.
- `hermes_cognitive_reflections` stores lessons after work changes future
  behavior.
- `hermes_cognitive_activations` records which memories, facts, and procedures
  fired for a query.
- `hermes_agent_beliefs` stores agent-specific confidence-weighted beliefs.
- `hermes_cognitive_contradictions` stores conflicts that need resolution.
- `hermes_dream_jobs` stores idle cognition passes.
- `hermes_council_records` stores multi-agent deliberation and the final
  arbitration decision.
- `hermes_experiments` stores autonomous project-scientist hypotheses, metrics,
  risk, confidence, and results.
- `hermes_skill_evolutions` stores agent-specific learning distilled from
  experiments.
- `hermes_autonomy_decisions` stores confidence-gated approvals, council
  reviews, and operator-escalation decisions.

Seed the cognitive kernel:

```bash
make seed-cognition
```

Activate an agent's cognition for a request:

```bash
make activate-cognition PROFILE=sheldon QUERY="How should we route this blocked build?"
```

Run the experimental idle-thinking and council loops:

```bash
make dream-cycle
make experiment-cycle
make evolve-skills
make autonomy-decision QUERY="refresh the active project status" RISK=low CONFIDENCE=0.9
make council TOPIC="What is the safest next slice for the active project?"
```

Inspect current cognitive state:

```bash
make cognition-summary
```

## Notes

- This project owns its own workspaces and does not require any OpenClaw repo
  after bootstrap.
- Discord access still needs allowlists or pairing configuration before outside
  users can talk to the operator bot.
- If Docker becomes available later, re-running bootstrap will switch the
  generated config to a safer Docker backend automatically.
