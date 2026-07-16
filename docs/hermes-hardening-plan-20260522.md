# Hermes Hardening Plan — 2026-05-22

## Purpose

Use `aetherion-maze` as the pilot project to harden Hermes until it can:

- keep one converging delivery path
- route work through the right specialist lanes
- verify visual claims against the real artifact
- avoid false "fixed/live" closure in Discord and the portal
- preserve enough session continuity that long runs do not drift

This plan treats the maze failure as a stack-hardening problem, not just a bad
single-project outcome.

## Decision

For this machine, this is primarily a Hermes issue.

- OpenClaw is not the active runtime here.
- Hermes is the active gateway, portal, session, and specialist stack.
- Some failure patterns may be shared with historical OpenClaw behavior, but
  the current pilot hardening work belongs in Hermes.

## Pilot Failure Modes To Eliminate

1. Claims of "live", "fixed", or "using the provided sprites" before the
   screenshot actually proves it.
2. Verification that proves pipeline state (`src=loose`, cache-bust, no atlas)
   instead of user-visible rendering.
3. Operator lane doing direct game implementation instead of routing to
   `game-dev` and holding it to evidence.
4. Multiple partial implementations or stale targets surviving too long.
5. Session compression and mirror behavior making long Discord work harder to
   audit.
6. Skills encoding incomplete verification criteria and teaching the model the
   wrong proof standard.

## Hardening Scope

### Autonomy Guardrail

This hardening work must increase trust in autonomous execution, not reduce the
amount of autonomous work Hermes can do.

Guardrails:

- agents should still act end-to-end inside approved roots without waiting for
  unnecessary confirmation
- specialists should still implement, verify, and recover issues directly when
  the next action is safe
- evidence requirements should harden proof and reporting, not create new
  approval theater
- quality gates should block false closure, not block legitimate autonomous
  progress
- when the system cannot verify a visual claim strongly enough, it should avoid
  the claim and keep working rather than pausing by default

Non-goal of this plan:

- turning Hermes into a hesitant or approval-heavy workflow

### 1. Evidence Gate

Hermes must reject outcome claims unless the response includes:

- target artifact path or URL
- checks run
- failing checks
- next unblocker
- at least one artifact-specific proof for visual work

For visual/game/UI work, "artifact-specific proof" means:

- screenshot path or browser capture
- explicit statement of what is visibly on screen
- confirmation of required roles, not just runtime flags

Runtime flags alone are not sufficient proof.

Examples of insufficient proof:

- `src=loose`
- `rects=0`
- `tex=empty`
- cache-busted URL only
- "the atlas is retired"

### 2. Visual Acceptance Gate

Add a visual gate for maze-groundup and future visual projects:

- if the screenshot still shows placeholder letters like `H`, `E`, `P`, `T`,
  `I`, the run must be treated as failed
- if the assistant says "sprites are live" while also saying "still finishing
  the pass", the run must be treated as failed
- if the screenshot does not show the user-requested asset class on screen, the
  run cannot claim success

For `aetherion-maze`, the pilot acceptance check is:

- hero visible from provided art
- enemies visible from provided art
- portal visible from provided art
- traps/items visible from provided art
- floor/walls visible from intended terrain path
- HUD readable and not diagnostic-only

### 3. Operator Lane Discipline

Tighten the operator role from "sometimes implements" to "routes and verifies".

Rules:

- operator owns intake, scope, convergence, and final evidence
- `game-dev` owns game implementation
- `creative-dev` owns asset readiness and packaging when art inputs are not yet
  machine-usable
- operator should not improvise renderer patches in Discord unless it is a
  narrow unblocker and the specialist lane is unavailable

Add a hard preference:

- for Maze, renderer, sprite, HUD, gameplay, or browser-game issues, operator
  dispatches `game-dev` first and only reports back after specialist evidence is
  reviewed

### 4. Project Convergence

Hermes must keep one active delivery target per project slice.

Required behavior:

- each project record names one primary artifact
- all other variants are explicitly marked `reference-only`, `legacy`,
  `deprecated`, `parked`, or `_archive`
- responses must state which artifact is primary before claiming progress

For the maze pilot:

- one active build path only
- one active review URL only
- old or alternate builds archived or clearly labeled

### 4A. Portfolio Control Plane

Hermes must treat multiple projects as first-class operating state, not as one
long chat thread.

Required behavior:

- keep a persistent portfolio queue with one focused project slice at a time
- support creating, activating, parking, and archiving projects explicitly
- bind Discord/operator sessions to the correct project when the lane is clear
- store per-project orchestration control including:
  - primary specialist lane
  - lane sequence
  - delivery target
  - primary artifact
  - acceptance list
  - capability gaps

Done when:

- Sheldon can keep multiple live projects without forgetting which one is in
  focus or improvising folder clones as a fake project system

### 5. Session Continuity And Auditability

Session continuity is good enough only if a reviewer can reconstruct what
happened without guessing.

Hardening targets:

- surface session split events caused by compression in the operator portal
- show current session id, previous session id, and split reason
- expose whether the latest reply came from a continued session or a split one
- make Discord DM/thread origin visible in the portal run metadata
- fix stale or misleading thread mirrors so current work is not hidden in a
  different session path than expected

### 6. Skill Hygiene

Skills must not encode weak proof standards.

Review and patch:

- `html5-canvas-loose-png-first-skin-catalog`
- any related maze stability / sprite guard / catalog-first skills

Required changes:

- move verification from pipeline-state checks to visible-role checks
- require confirming real on-screen roles after a screenshot
- explicitly forbid calling Option A "live" unless placeholders are gone for
  required roles

### 7. Quality Gate Tightening

The quality gate should fail responses that:

- claim success with only code inspection
- claim success with only diagnostics overlay values
- ignore a user report that the screenshot still looks wrong
- present incomplete work as completed

Add explicit heuristics for contradiction detection:

- "it is live" plus "still finishing"
- "using your sprites" plus screenshot still showing placeholders
- "verified" without naming the actual artifact inspected

## Workstreams

### Workstream A — Prompt And Policy Enforcement

Owner: Hermes

Tasks:

- strengthen operator and specialist runtime contracts
- make the evidence block mandatory for visual work
- add explicit anti-false-closure language to the quality gate

Done when:

- a bad screenshot cannot pass with a "live" claim

### Workstream B — Portal Evidence UX

Owner: Hermes portal / app-dev

Tasks:

- show target artifact
- show latest screenshot path if one exists
- show checks run / failing checks / next unblocker
- show session split warnings
- show latest specialist dispatches and whether any are stale

Done when:

- an operator can audit a bad run from the portal without reading raw logs

### Workstream C — Session And Mirror Reliability

Owner: Hermes runtime

Tasks:

- inspect DM vs thread mirroring behavior
- reduce stale mirror confusion
- surface session compression transitions
- ensure the latest conversation is discoverable from one obvious place

Done when:

- "where are today's messages?" is answerable from one canonical surface

### Workstream D — Maze Pilot Acceptance Harness

Owner: game-dev + app-dev

Tasks:

- create a repeatable review checklist for maze-groundup
- add a screenshot-based placeholder regression check
- record one known-good screenshot set for comparison

Done when:

- the maze can be used as a stable acceptance fixture for future projects

### Workstream E — Supervisor Loop And Discord Control

Owner: operator + gateway

Tasks:

- turn specialist dispatch into a supervised review loop with revision retries
- keep lane ownership with the assigned specialist unless the lane is exhausted
  or a capability gap is recorded
- expose Discord project controls for list, create, switch, and archive actions
- block "operator-side takeover" language when a specialist lane should still
  own the work

Done when:

- Sheldon behaves like a lead reviewing specialists instead of a one-shot
  task router

## Near-Term Sequence

1. Tighten the response quality gate for visual/game claims.
2. Patch the relevant sprite workflow skills.
3. Add portal visibility for session splits, screenshots, and failing checks.
4. Add a maze placeholder-regression acceptance check.
5. Add the supervisor loop and Discord project control.
6. Re-run the maze pilot until it passes the new gate.

## Acceptance Criteria For Hermes Hardening

Hermes is hardened enough for the next pilot project when all are true:

- operator responses for visual work always include target artifact, checks run,
  failing checks, and next unblocker
- no response can call a visual fix complete if placeholders remain on screen
- operator routes implementation to the correct specialist lane by default
- operator can keep multiple Discord project lanes alive and switch them
  explicitly
- specialist work is reviewed and revised in-lane before operator takes over
- project state names one primary artifact and does not drift silently
- session splits and current conversation location are visible to the operator
- the maze pilot passes the new gate without the user having to point out that
  the screenshot is wrong

## Non-Goals

- rebuilding OpenClaw on this machine
- solving every historical gateway behavior before the next Hermes improvement
- making the maze itself perfect before the Hermes stack is trustworthy

## First Concrete Deliverables

- quality-gate patch for false visual closure
- skill patch for visible-role verification
- portal UI patch for evidence and session-split visibility
- maze pilot regression checklist
- supervisor-loop and Discord project-control patch
