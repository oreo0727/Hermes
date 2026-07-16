# Hermes Upgrade Blueprint

This blueprint replaces the custom OpenClaw runtime path with a Hermes-first
architecture while preserving the original goal:

- long-lived specialist agents
- natural-language access at any time
- real artifact production
- visible security guardrails
- a real operator portal

The target is not "migrate the old system into Hermes."

The target is "use Hermes as the living-agent substrate and keep only the
custom layers that still create clear product value."

## Success Criteria

The new system should feel like an upgrade in practice, not just in code:

- `app-dev`, `game-dev`, and `creative-dev` feel like reachable living agents
- each specialist can be contacted from CLI, portal, or messaging
- each specialist can resume context and continue prior work
- each specialist can produce artifacts in approved workspaces
- security and approval boundaries are enforced by runtime controls
- the operator can see status, activity, artifacts, and approvals in one place

## Non-Goals

- rebuilding a second custom gateway when Hermes already has one
- preserving the typed-job router just because we already started it
- keeping a custom admin UI if Hermes plus a thin operator portal is enough
- allowing prompts alone to define security-sensitive behavior

## Core Principles

### 1. Hermes Owns the Runtime

Hermes should own:

- sessions
- memory
- skills
- gateway connectivity
- cron and background automation
- provider and model routing
- subagent delegation
- terminal execution backends
- baseline dashboard and API surfaces

OpenClaw Next should stop rebuilding those layers unless Hermes proves
insufficient in a specific area.

### 2. Specialists Replace Factories as the User-Facing Model

Users should talk to living specialists, not to an abstract router.

The primary identities become:

- `operator`
- `app-dev`
- `game-dev`
- `creative-dev`

These are durable Hermes profiles, not temporary worker prompts.

### 3. Policy Lives in the System Shape

Security should be enforced through:

- constrained toolsets
- fixed execution backends
- approved workspace roots
- approval modes
- user/channel allowlists
- audit events
- artifact validation

Prompts can explain policy, but they should not be the only policy layer.

### 4. Custom Code Must Earn Its Keep

We should only keep custom code for:

- workspace and artifact policy enforcement
- specialist identity design
- operator portal UX
- domain-specific workflow logic that Hermes skills/plugins cannot model well

## Target Architecture

## Layers

### 1. Hermes Substrate

Hermes is the base control plane for:

- CLI chat
- messaging gateway
- session persistence
- persistent memory
- skill loading
- cron jobs
- model and tool configuration
- background execution

### 2. Specialist Profiles

Each living specialist is a Hermes profile with its own:

- `SOUL.md`
- memory
- skills
- toolsets
- model defaults
- cron jobs
- channel bindings
- execution backend settings

### 3. Policy Layer

A thin custom policy layer sits on top of Hermes through plugins, hooks, or a
small sidecar service.

It owns:

- workspace-root enforcement
- artifact contract enforcement
- audit event shaping
- high-risk action policy
- portal-facing status summaries

### 4. Operator Portal

A dedicated portal sits above Hermes and the policy layer.

It is the main operator surface for:

- agent status
- routing chats to specialists
- reviewing approvals
- browsing artifacts
- monitoring runs
- editing schedules
- managing channel bindings
- seeing audit history

### 5. Approved Workspaces

All artifact creation happens under approved roots only.

The portal and policy layer should treat workspaces as first-class records with:

- workspace id
- root path
- owning specialist
- active tasks
- recent artifacts
- policy state

## Specialist Model

## `operator`

Purpose:

- human-facing coordinator
- intake triage
- task handoff
- portfolio-level oversight
- escalation and approval review

Should be able to:

- answer status questions
- route work to specialists
- request summaries
- trigger follow-ups
- review artifacts and risks

Should not be the default executor for deep domain work.

## `app-dev`

Purpose:

- software feature work
- bug fixing
- refactors
- repo setup
- code review and release prep

Default strengths:

- file editing
- terminal work
- web research
- debugging
- structured artifact output

## `game-dev`

Purpose:

- gameplay engineering
- prototypes
- content pipelines
- build/test loops
- design-to-playable iteration

Default strengths:

- code and file work
- tool-driven iteration
- build verification
- asset and content workflow coordination

## `creative-dev`

Purpose:

- storyboards
- prompt packs
- creative briefs
- visual direction
- asset planning and review

Default strengths:

- research
- writing
- multimodal workflows
- packaging handoff-ready creative artifacts

## Tooling Policy by Specialist

This is the starting posture, not the final config.

- `operator`
  - allow: messaging, session search, summaries, skills, light file access
  - restrict: wide terminal authority by default
- `app-dev`
  - allow: file, terminal, web, delegation, approved browser tools
  - restrict: messaging side effects except through explicit flows
- `game-dev`
  - allow: file, terminal, web, delegation
  - restrict: wide external delivery unless approved
- `creative-dev`
  - allow: file, web, image workflows, writing skills, selected terminal
  - restrict: broad execution rights unless needed for packaging

## Artifact Contract

Every specialist run should end with a structured artifact record.

Minimum fields:

- `request_id`
- `specialist`
- `workspace_id`
- `workspace_root`
- `goal`
- `status`
- `artifacts_created`
- `artifacts_updated`
- `artifacts_reviewed`
- `decisions`
- `risks`
- `approval_events`
- `next_actions`
- `completed_at`

This replaces the old typed-job outcome idea with a thinner, Hermes-native
result envelope.

Artifacts should be persisted in the workspace and indexed by the portal.

## Security Blueprint

## Non-Negotiable Rules

- no artifact writes outside approved roots
- no prompt text may directly override runtime paths
- dangerous commands stay behind Hermes approvals
- destructive operations remain blocked or approval-gated
- each specialist gets only the toolsets it actually needs
- external messaging access uses allowlists and channel binding rules
- high-risk flows emit audit events

## Execution Backends

Default backend policy:

- use isolated execution for specialists that can edit or build
- prefer Docker or SSH-style isolation for artifact-producing specialists
- reserve local-host execution for explicitly trusted cases

The backend decision is part of the specialist contract, not an ad hoc choice.

## Approval Model

Baseline posture:

- `operator` can review and approve
- specialists can request risky actions
- dangerous command execution is visible in CLI, portal, or messaging
- repeated permanent allowlisting should be rare and intentional

## Audit Model

Every meaningful run should emit:

- who initiated it
- which specialist handled it
- which channel or interface it came from
- which workspace it touched
- which artifacts changed
- which approvals were triggered
- final result state

## Portal Blueprint

The stock Hermes dashboard is useful, but it should not be treated as the final
operator portal.

Reasons:

- it is localhost-first
- it has no built-in auth for network exposure
- it is a control dashboard, not a purpose-built operations surface

We should build a thin operator portal on top of Hermes APIs and plugin hooks.

## Portal MVP Pages

### 1. Overview

Show:

- all specialists
- current status
- last activity
- active runs
- pending approvals
- recent artifacts

### 2. Unified Inbox

Show:

- current conversations by specialist
- quick routing to `operator`, `app-dev`, `game-dev`, or `creative-dev`
- conversation resume and handoff context

### 3. Workspaces

Show:

- approved workspaces
- active tasks per workspace
- artifact history
- owning specialist
- last policy event

### 4. Approvals

Show:

- pending risky actions
- command details
- affected workspace
- requesting specialist
- one-time or scoped approval actions

### 5. Artifacts

Show:

- files created or updated
- artifact summaries
- latest deliverables per specialist
- quick links into workspace paths

### 6. Schedules

Show:

- cron jobs by specialist
- health and last run state
- next run time
- pause, resume, trigger-now actions

### 7. Audit

Show:

- run history
- approval events
- policy violations
- routing and handoff trail

## Portal Integration Options

Primary path:

- build a custom portal against Hermes API surfaces and the policy layer

Secondary path:

- extend the Hermes dashboard where doing so is cheaper than duplicating work

Decision rule:

- use Hermes dashboard for low-level control and diagnostics
- use the custom operator portal for daily multi-agent operations

## Messaging Model

Messaging should map cleanly to specialist identity.

Recommended pattern:

- `operator` receives broad intake
- each specialist gets a dedicated route:
  - Discord channel
  - Discord thread
  - command alias
  - future web chat entrypoint

The user should be able to message the specialist directly and receive work
product without needing to understand the routing internals.

## Skill Strategy

Skills should carry most reusable workflow knowledge.

Good Hermes skill candidates:

- planning
- code review
- release prep
- game build pipeline
- storyboard breakdown
- prompt pack generation
- asset checklisting
- creative review
- handoff packaging

Specialist identity should stay in profile-level context.

Reusable procedures should move into skills.

Strict policy should not live only in skills.

## Delegation Strategy

Delegation is for bounded side work, not for durable identities.

Use delegation for:

- parallel research
- isolated debugging
- fresh-context review passes
- limited subtask execution

Do not use delegated subagents as substitutes for `app-dev`, `game-dev`, or
`creative-dev`.

## What Gets Replaced

These `openclaw-next` concerns should be replaced by Hermes unless proven
otherwise:

- session handling
- memory system
- messaging gateway
- model/provider plumbing
- cron runtime
- baseline dashboard functions
- ad hoc multi-agent runtime scaffolding

## What Stays Custom

These concerns likely remain, but in thinner form:

- workspace-root policy
- artifact contract validation
- specialist definitions and identities
- operator portal
- domain-specific workflow packaging
- high-signal audit summaries

## Rollout Plan

## Phase 1 - Blueprint Freeze

Define and approve:

- specialist list
- workspace policy
- artifact contract
- toolset posture
- portal MVP scope
- approval model

No implementation until this is stable.

## Phase 2 - Hermes Pilot

Stand up:

- `operator` profile
- one specialist profile
- gateway connectivity
- basic portal stub or dashboard usage

Prove:

- session continuity
- messaging reachability
- artifact creation in approved roots
- visible approval flow

## Phase 3 - Policy Layer

Implement:

- workspace-root checks
- artifact result envelope
- audit shaping
- portal-facing run summaries

This is the point where we validate whether Hermes plugins/hooks are enough.

## Phase 4 - Portal MVP

Ship:

- overview
- inbox
- approvals
- workspaces
- artifacts
- schedules

The portal becomes the daily operator surface.

## Phase 5 - Full Specialist Set

Add:

- `app-dev`
- `game-dev`
- `creative-dev`

Tune:

- toolsets
- skills
- model defaults
- schedules
- channel bindings

## Phase 6 - Retirement

Archive or remove custom runtime pieces from `openclaw-next` once Hermes and
the thin custom layer are stable.

Retire platform code only after the operator portal and policy layer are
working.

## Decision Gates

We proceed with full replacement only if the pilot proves:

- Hermes specialists feel more alive than the current factory path
- artifact production is cleaner and more reliable
- approvals are visible and trustworthy
- the operator portal gives better control than the current admin UI path
- remaining custom code is clearly smaller than the runtime we retire

If those conditions are not met, we stop and reassess before broad migration.

## Final Recommendation

The likely end state is:

- Hermes as the living-agent substrate
- one durable profile per specialist
- a thin policy layer for workspace and artifact guarantees
- a custom operator portal for multi-agent oversight
- retirement of most custom runtime and gateway code in `openclaw-next`

This keeps the original OpenClaw Next ambition, but finally aligns the system
shape with it.
