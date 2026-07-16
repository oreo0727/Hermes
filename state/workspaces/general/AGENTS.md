# Operator Workspace

This workspace is the default artifact root for the `operator` specialist.

## Paths

- Approved artifact root: `/home/james/Hermes/state/workspaces/general`
- Project root: `/home/james/Hermes`

## Rules

- Put generated artifacts in this workspace unless the operator explicitly asks for another approved destination.
- Treat the project root as reference context and integration target.
- Call out any write that would leave the approved workspace before doing it.
- End each run with a short artifact summary, risks, and next actions.
