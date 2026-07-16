# Hermes v2 Outline — 2026-05-26

## Goal

Build Hermes v2 around the Vision v1 north star:

- Discord-first control
- truthful multi-lane orchestration
- artifact-first delivery
- explicit project state
- anti-loop closure rules

Supporting design docs:

- `docs/hermes-vision-v1-20260526.md`
- `docs/hermes-v2-capability-matrix-20260526.md`

## v2 Product Definition

Hermes v2 should be:

- a Discord-first operating layer
- a project/state-driven orchestration engine
- a specialist system with real capabilities
- a thin portal command center for visibility and recovery

## Main Problems v2 Must Solve

### 1. Prompted orchestration without enforced state transitions

Current behavior can still devolve into:

- prose instead of actions
- repeated retries
- weak closure logic

v2 should move to explicit orchestration actions and stage transitions.

### 2. Specialist capability mismatch

Some lanes know what they should not do, but still lack the tooling to do the right thing.

v2 should align:

- lane identity
- installed skills
- runnable tools
- verification methods

### 3. False or weak closure

The system can still confuse:

- output exists
- output is truthful
- output is review-ready
- output is verified

v2 should separate those states.

### 4. Retry loops and stale active work

The system currently allows:

- duplicate dispatches
- stale `running` records
- orphaned worker processes
- repeated retries on the same deliverable

v2 should treat these as first-class orchestration failures.

## v2 Architecture

### A. Operator State Machine

Replace prompt-only orchestration with explicit action types.

Suggested operator actions:

- `direct_execute`
- `dispatch_specialist`
- `revise_dispatch`
- `promote_artifact`
- `mark_blocked`
- `request_decision`
- `archive_or_park`
- `close_slice`

Each action should update project state and leave an audit trail.

### B. Delivery Slice Model

Every active slice should declare:

- project id
- current lane owner
- delivery target
- primary artifact
- acceptance criteria
- evidence required for closure
- active attempt id
- retry count

Only one active attempt per lane/deliverable should exist at a time.

### C. Closure Gate

Before marking a slice complete, require:

- artifact exists
- artifact path recorded
- verification performed
- state updated
- no conflicting active attempts

For visual work, the gate should require visible evidence, not text summary alone.

### D. Retry Guardrails

Add hard protections:

- no dispatching a new attempt while another attempt for the same slice is running
- stale attempts auto-expire into `failed` or `interrupted`
- retries require a new reason:
  - new prompt
  - new tool
  - new env fix
  - explicit escalation
- repeated identical retries create a capability gap instead of another retry

### E. Capability Registry

Each lane should expose a practical registry of:

- skills
- tools
- runtimes
- output formats it can actually produce
- known blockers

This should be used in dispatch planning before a lane is assigned work.

## v2 Surfaces

### Discord

Primary operator surface.

Support:

- project focus and switching
- status and blockers
- handoff summaries
- artifact delivery
- approvals
- compact recovery commands

### Portal

Secondary command center.

Focus on:

- active project
- queue
- lane ownership
- active attempts
- proofs and artifacts
- stale/retrying runs
- recovery actions

Portal chat should remain de-emphasized.

## v2 Specialist Contract

Each specialist response should clearly separate:

- implemented
- verified
- assumed
- blocked
- next actions
- artifacts

And each lane should either:

- deliver a real artifact
- revise a real artifact
- fail honestly with a capability gap

The current target character/lane mapping is:

- Sheldon = Operator
- Penny = Creative Dev
- Raj = App Dev
- Leonard = Game Dev

## v2 Milestones

### Milestone 1: Honest Control Plane

- add attempt-level state to dispatches
- prevent duplicate active dispatches
- auto-resolve stale `running` records
- make project state the source of truth for current slice ownership

### Milestone 2: Discord-First Operator Loop

- tighten Discord commands and natural-language controls
- bind sessions to projects automatically when confidence is high
- improve compact status formatting for phone use

### Milestone 3: Specialist Capability Alignment

- audit each lane’s real tooling
- install missing system and local skills where needed
- make capability gaps explicit in dispatch planning

### Milestone 4: Closure and Verification

- enforce artifact-plus-evidence closure
- add visual verifier flows for creative work
- add implementation verifier flows for app/game work

### Milestone 5: Recovery and Recovery UX

- add portal actions for:
  - stop retry loop
  - mark blocked
  - promote artifact
  - close stale attempts
  - reassign lane

## First Concrete v2 Worklist

1. Fix dispatch lifecycle so completed attempts cannot remain `running`.
2. Add single-owner/single-attempt enforcement per deliverable slice.
3. Teach operator routing to stop retrying identical failed creative-dev jobs.
4. Add promotion logic for “raw exists, final still placeholder” cases.
5. Add a portal panel for stale attempts and loop warnings.
6. Add lane capability checks before dispatch.
7. Align `creative-dev` around real reference-grounded generation and promotion flows.

## Success Criteria

Hermes v2 is working when:

- Discord is enough for normal operation
- the portal is useful without being required for chat
- Sheldon routes and closes work instead of narrating it
- specialists have real, inspectable capabilities
- retries converge or escalate quickly
- "done" means artifact plus proof plus truthful state
