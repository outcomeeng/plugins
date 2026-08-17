# Change Coordination

Loaded by `/pickup` and `/handoff` when present. It names where this repository's Changes and Handoffs live, per methodology `versions/next/11-coordination.md` and the GitHub realization it cites. Values only; the workflow is the skill's.

## Change store

- Repository: `outcomeeng/changes` (one issue per Change; issues only)
- Project: owner `outcomeeng`, number `1` (`https://github.com/orgs/outcomeeng/projects/1`)
- Product: `plugins` — the `Product` field value for every Change this repository picks up or hands off
- Fields: `Product` (methodology | spx | plugins), `Maturity` (Proposed | Framed | Sliced | Executable), `Status` projects Lifecycle (Available | Claimed | Applied | Refined | Abandoned)

## Legacy queue

`.spx/sessions/todo` and `.spx/sessions/doing` are received input awaiting a Change. A file becomes a Change only when `/pickup` claims it: the whole file is the Change's received input, and the file is archived once the Change exists. No bulk migration.
