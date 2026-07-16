# Creative Dev Workspace

This workspace is the default artifact root for the `creative-dev` specialist.

## Paths

- Approved artifact root: `/home/james/Hermes/state/workspaces/creative-dev`
- Project root: `/home/james/Hermes`

## Rules

- Put generated artifacts in this workspace unless the operator explicitly asks for another approved destination.
- Active project artifact folders under `/home/james/Hermes/state/projects/<project_id>/...` are also approved destinations when the task is project-bound.
- Treat the project root as reference context and integration target.
- Call out any write that would leave the approved workspace or active project artifact roots before doing it.
- End each run with a short artifact summary, risks, and next actions.
