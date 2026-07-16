# Hermes v2 Capability Matrix — 2026-05-26

## Purpose

This matrix translates the Vision v1 doc into an implementation-facing v2 reference.

It answers, for each primary agent:

- who they are
- what they own
- what they can do today
- what is still missing
- what proof they must return
- what closure rule should govern their work

This is the bridge between:

- character
- lane ownership
- real capability
- verification
- orchestration behavior

## Character Rule

Personality is allowed.
Truth is mandatory.

Hard precedence:

1. truth layer beats personality layer
2. verification layer beats confidence
3. project state beats chat tone

## Agent Model

Each v2 agent should be defined by:

- character name
- lane
- voice
- tools allowed
- skills installed
- project memory
- artifact types produced
- acceptance criteria
- verification method
- closure rule

## v2 Matrix

| Character | Lane | Core job | Owns | Can do today | Missing capability / gap | Proof required | Closure rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sheldon | Operator | Control plane, routing, truth, status, escalation | Project focus, queue, dispatch, recovery, honest reporting | Discord-first operator flow, project activation/binding, specialist dispatch, status synthesis, recovery framing, portfolio control | Explicit action/state machine, duplicate-attempt prevention, stale-run cleanup, stronger closure gating, voice layer later | Updated project state, dispatch record, proof links, artifact paths, status tied to live state | A slice is only closed when the owning lane's artifact exists, proof is attached, project state is updated, and no conflicting active attempts remain |
| Penny | Creative Dev | Storyboards, prompt packs, styleframes, visual QA, art direction | Visual development lane for concept/story/brand/artifacts | Storyboard generation, storyboard QA, reference-grounded storyboard flow, styleframe fallback packaging, raw-to-final promotion workflows, animatic-support packaging | More robust image/video runtime alignment, stronger promotion logic, consistent visual verification, less fallback dependence, reference memory across projects | Contact sheets, final frame paths, visual notes naming what is on screen, blocker docs when applicable, review-ready artifact list | Creative work closes only when visible outputs match the request, placeholders are not masquerading as finals, and visual verification is recorded |
| Raj | App Dev | Web/app/backend/features, integrations, deployment support | Portal, backend, integrations, implementation and release support | App/portal implementation, Godot web review-lane support, integration and release cleanup | Broader app-specific skill library, stronger automated test/release checklists, richer deployment verification, more reusable integration playbooks | Changed files, test results, service checks, release/recovery notes, exact routes/endpoints or integrations verified | App work closes only when code changed, verification ran, and the target route/service/integration is confirmed working |
| Leonard | Game Dev | Unity/Godot gameplay prototypes and fixes | Playable implementation lane | Godot web fixes, HTML5/gameplay implementation, renderer/HUD/tileset/input work, export-path support | Cleaner Unity-specific coverage, stronger engine templates, more standardized build/export validation, clearer gameplay acceptance contracts | Build/export results, gameplay capture or direct runtime verification, exact asset/build paths, test/check script output | Game work closes only when the playable artifact runs, the requested mechanic/fix is visible in runtime, and build/export verification passes |

## What This Means Operationally

### Sheldon

Should not absorb specialist work by default.

He should:

- decide the next action
- pick the owning lane
- define what artifact must come back
- define how it will be verified
- refuse fake closure

### Penny

Should not be reduced to prompt-writing only.

She should own:

- visual artifact generation
- visual review and mismatch calling
- handoff-ready visual packages
- truth about placeholder vs final status

### Raj

Should own software delivery slices, not vague engineering advice.

He should leave:

- code changes
- test evidence
- integration checks
- deployment/release support notes

### Leonard

Should own playable implementation slices.

He should leave:

- working builds or scenes
- mechanic/fix proof
- export validation
- exact build/runtime artifact paths

## Current v2 Priorities By Agent

### Sheldon priorities

1. Move from prompt-led orchestration to explicit action/state transitions.
2. Prevent retry loops and overlapping lane attempts.
3. Enforce proof before closure.

### Penny priorities

1. Stabilize image/video generation runtimes.
2. Promote real outputs cleanly from raw to final.
3. Separate blocked, placeholder, and review-ready visual states.

### Raj priorities

1. Expand the app-dev skill library beyond the current review lane.
2. Standardize app verification and release checklists.
3. Strengthen backend/integration delivery patterns.

### Leonard priorities

1. Formalize gameplay/build/export validation.
2. Improve reusable engine-specific templates and scripts.
3. Tighten proof for runtime-visible fixes.

## First End-to-End v2 Reference Loop

The first loop to harden should be:

1. Discord request arrives
2. Sheldon creates or updates a project slice
3. Sheldon assigns one lane owner
4. The owner produces an artifact
5. Verification runs
6. Sheldon reports proof
7. Project state updates
8. Slice closes or blocks honestly

That loop should work cleanly before expanding personality, voice, or additional surfaces.

## Design Test

Hermes v2 is aligned when each character can remain distinct in voice while still being predictable in ownership, evidence, and closure behavior.
