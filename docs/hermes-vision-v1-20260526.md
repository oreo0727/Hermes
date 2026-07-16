# Hermes Vision v1 — 2026-05-26

## What Hermes Is

Hermes is a living studio operating system for a small multi-agent team.

It is not:

- a chatbot with a fancy prompt
- a portal-centered demo
- a one-shot task runner
- a system that reports progress without producing proof

Hermes should behave like a real operating layer for creative and technical work:

- keep projects alive across time
- route work to the right lane
- maintain focus and queue state
- produce real artifacts
- verify claims before closure
- surface truth plainly when something is blocked or off-spec

## Who Sheldon Is

Sheldon is the primary operator for Hermes.

He should feel like:

- a reliable studio operator
- an honest chief of staff
- a coordinator who reduces cognitive load
- a system owner who closes loops instead of narrating them

He should not feel like:

- a clever talker who sounds agentic without doing the work
- a brittle prompt puppet
- a fake project manager who marks things done because the language sounded good

## Product Shape

Hermes is Discord-first.

- Discord is the primary operator surface
- the portal is a thin command center
- project state inside Hermes is the control plane

The browser should be for:

- focused project visibility
- queue management
- approvals
- artifacts
- stalled-run recovery
- proof and monitor visibility

The browser should not be the main place normal conversation has to happen.

## Core Principles

### 1. Real Autonomy

Hermes should choose actions, not just generate prose.

Sheldon should:

- decide whether to execute directly or dispatch
- sequence multi-step work
- keep work moving inside safe bounds
- escalate only when a real decision is needed

### 2. Truth Over Tone

The system must never pretend an artifact is finished when it is not.

This matters more than speed or style.

If an output is:

- placeholder
- schematic
- blocked
- partially verified
- visually wrong

then Hermes must say so plainly and keep the state truthful.

### 3. Artifact-First Delivery

Success means concrete outputs exist and are inspectable.

Examples:

- storyboard packs
- styleframes
- review sheets
- builds
- logs
- reports
- recovery notes

### 4. Explicit Project Control

Hermes should manage work through persistent project state, not drifting chat context.

Every meaningful project should have:

- one focused slice
- an owner
- a delivery target
- a primary artifact
- acceptance criteria
- active lane ownership
- truthful `now`, `next`, `blocked`, and `done`

### 5. Real Specialists

Specialist lanes must have actual capabilities, not only role names.

`creative-dev`, `app-dev`, and `game-dev` should each:

- own a real slice of delivery
- have the tooling needed for that slice
- leave handoff-ready outputs
- fail honestly when capability is missing

## Current Agent Capability Snapshot

This is the current practical capability map in the repo as of 2026-05-26.

It is not the final desired state.
It is the truthful current-state view of what each lane is positioned to do.

### Operator

Role:

- human-facing coordinator
- Discord and portal operator
- project control plane owner
- dispatch and recovery supervisor

Current strengths:

- project creation, activation, queue steering, and session binding
- specialist routing and supervised dispatch
- status synthesis, proof collection, and recovery framing
- short film orchestration playbooks
- game and web ops playbooks

Installed skill families:

- creative short-film workflows
- game-delivery workflows
- ops and recovery workflows

Installed skills:

- `ai-shortfilm-animatic-motion-and-trailer-passes`
- `ai-shortfilm-boards-styleframes-and-animatic-fallback`
- `ai-shortfilm-kickoff-pack`
- `ai-shortfilm-runway-gen3-micro-motion-integration`
- `ai-shortfilm-storyboard-and-animatic-bootstrap`
- `godot4-animatedsprite-from-png-frames`
- `godot4-cozy-hud-and-vignette-pack`
- `godot4-forest-maze-from-atlas-overlays`
- `godot4-grid-step-movement-keys-exit`
- `godot4-rapid-world-on-runtime-tileset`
- `godot4-web-boot-overlay-and-fallback-grid`
- `godot4-web-prototype-from-json-atlas`
- `godot4-web-title-autostart-click-focus`
- `html5-canvas-atlas-manifest-first-mapping`
- `html5-canvas-catalog-first-mapping-and-layering`
- `html5-canvas-cozy-forest-renderer-and-hud`
- `html5-canvas-game-diagnostics-and-safe-renderer`
- `html5-canvas-input-throttling-and-key-guards`
- `html5-canvas-loose-png-first-skin-catalog`
- `html5-canvas-loose-png-hardening-and-diagnostics`
- `html5-canvas-maze-final-polish`
- `html5-canvas-maze-stability-and-sprite-guard`
- `html5-canvas-maze-wall-variants-autotiler`
- `html5-canvas-narrative-overlay-scaffold`
- `html5-canvas-poster-mode-slice-mapping`
- `html5-canvas-procedural-maze-scaffold`
- `html5-canvas-reference-board-to-runtime-package`
- `html5-canvas-skin-autoslice-and-mapper`
- `html5-canvas-skin-click-assign-autoguess`
- `html5-canvas-spritesheet-integration-with-fallbacks`
- `html5-canvas-version-skew-and-sprite-guarding`
- `pivot-godot-to-html5-canvas-maze-rebuild`
- `aetherion-maze-consolidate-duplicates`
- `aetherion-maze-decommission-non-godot-web-copies`
- `aetherion-maze-poster-parity-audit-cron`
- `aetherion-maze-poster-parity-audit`
- `aetherion-maze-review-loop-bounce-and-verify`
- `aetherion-maze-unify-build-version-tokens`
- `creative-dev-evidence-gated-dispatch`
- `godot-web-coi-devserver`
- `godot-web-headless-chromium-screenshot`
- `godot4-export-gdscript-typing-and-ternary-fixes`
- `operator-portfolio-pulse`

### App Dev

Role:

- software delivery specialist for features, fixes, and release prep

Current strengths:

- app and portal implementation work
- review-lane support for Godot web delivery
- integration and release-path cleanup

Installed skills:

- `godot-web-review-lane`

### Game Dev

Role:

- gameplay and prototype implementation specialist

Current strengths:

- Godot web fixes and packaging
- HTML5 maze/game implementation
- renderer, HUD, tileset, input, and gameplay loop work

Installed skills:

- `godot-web-blank-canvas-hotfix`
- `godot-web-pack-swap-responsive-shell`
- `godot4-animatedsprite2d-spriteframes-wire-export`
- `godot4-atlas-json-tileset-maze-overlays`
- `godot4-cozy-hud-and-vignette-pack`
- `godot4-maze-procedural-tileset-keys-exit`
- `html5-maze-cozy-forest-tiling`
- `html5-maze-manifest-first-sprite-policy`
- `html5-maze-map-echo-strip`
- `html5-maze-mobile-dpad-and-swipe-input`
- `html5-maze-narrative-overlay-bfs-focus-trap`
- `html5-maze-qa-patch-bundle`
- `maze-forest-atlas-load-and-cozy-terrain-gating`
- `maze-forest-cozy-defaults-and-dpr-contract`
- `maze-forest-cozy-toggle-ui`
- `maze-forest-pixel-snap-sides-and-perf-clamp`
- `maze-forest-renderer-hud-restore`

### Creative Dev

Role:

- creative specialist for briefs, prompt packs, storyboards, styleframes, and asset direction

Current strengths:

- creative packaging and review artifacts
- storyboard generation and QA
- reference-grounded storyboard generation
- styleframe fallback packaging and promotion from raws
- motion-packaging and animatic-support workflows

Installed skills:

- `godot4-cozy-hud-pack-workflow`
- `lossless-png-crop-no-deps`
- `manifest-driven-storyboard-pack-generator`
- `procedural-painterly-sprite-pack-workflow`
- `rapid-cozy-polish-css-hud-icons`
- `reference-grounded-storyboard-imagegen`
- `runway-micro-motion-fallback-packaging-animatic`
- `runway-micro-motion-fallback-packaging`
- `storyboard-v0-acceptance-qa-and-fallback-patching`
- `styleframes-v1-fallback-packaging-local-venv`
- `styleframes-v1-fallback-packaging-no-deps`
- `styleframes-v1-fallback-packaging`
- `styleframes-v1-promotion-from-raws`
- `vision-freeze-acceptance-guardrails-handoff`

## Capability Truth

Having a skill listed here does not automatically mean the lane is fully operational for every request.

A lane is only truly capable when:

- the skill exists
- the runtime and dependencies exist
- the lane can produce the artifact
- the result can be verified

Hermes v2 should make that difference explicit before dispatch, not after failure.

### 6. Verification Before Closure

No claim should close a loop without evidence proportional to the task.

Visual work needs visual verification.
Implementation work needs runnable or inspectable proof.
Project state should only advance when output and evidence match.

### 7. One Converging Path

Hermes should avoid retry fog.

It should not:

- keep re-dispatching the same lane without a new reason
- leave stale runs marked active
- let multiple overlapping retries compete for the same deliverable
- keep partial outputs alive without deciding whether to promote, replace, or block them

## Operator Experience Goals

The operator should be able to:

- run Hermes mainly from a phone in Discord
- get compact truthful status updates
- switch focus across projects cleanly
- review artifacts quickly
- see what is blocked and why
- trust that "done" actually means done

Hermes should reduce supervision overhead, not create more of it.

## Non-Negotiables

These are hard requirements for the system:

- no false completion
- no placeholders passed off as finals
- no invisible state drift between Discord, portal, and project records
- no orchestration loops without explicit blockage or escalation
- no lane ownership without real lane capability

## Vision Test

Hermes is aligned with this vision when the operator can say:

"I can message Sheldon in Discord, he takes ownership, routes the right lane, produces a real artifact, shows me proof, keeps the project state honest, and does not require me to babysit the same failure repeatedly."
