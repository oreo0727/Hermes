# Hermes Discord-First Command Center — 2026-05-23

## Decision

Hermes should be operated Discord-first.

- Discord is the primary human-facing surface for Sheldon
- the browser portal is a thin command center, not the main conversation UI
- project state in Hermes remains the source of truth

## Why

The real operator workflow is happening on mobile through Discord.

That means the old portal shape was upside down:

- too much screen space was dedicated to browser chat
- the portal implied that the browser was the primary way to talk to Sheldon
- the real needs were queue visibility, proof visibility, run tracking, and quick recovery controls

## New Portal Role

The portal should answer:

- what is the one focused project right now
- what Discord session is bound to it
- what Hermes has accepted and what is still running
- which specialist lane owns the next move
- what evidence exists for the latest claim
- what needs intervention

The portal should not require the operator to chat there for normal work.

## UI Direction

The command center centers on:

- focused project
- project queue
- Discord binding and recent session visibility
- specialist lane health
- runs
- dispatches
- monitor alerts

Chat is intentionally de-emphasized.

## Backend Support

Minimal backend additions are enough for this phase:

- activate a project from the portal
- archive a project from the portal
- keep using the existing bootstrap snapshot, runs, dispatches, and monitor feeds

## Immediate Follow-On Work

- make Discord slash commands and natural-language controls the explicit operator playbook
- add portal actions for park/unpark and compact project updates if needed
- teach operator runs to prefer orchestration actions over one-shot prose
- add verifier passes for visual and artifact-sensitive work before closure claims
