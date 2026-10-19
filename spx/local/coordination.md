# Change Coordination

Loaded by `/claim-change`, `/release-change`, `/close-change`, and `/author-change` when present. It names where this repository's Changes and Handoffs live, per methodology `versions/4.0/methodology/change/changes.md` and the GitHub realization it cites. Values only; the workflow is the skill's.

## Change store

- Repository: `outcomeeng/changes` (one issue per Change; issues only)
- Product: `plugins` — the `Product` field value for every Change this repository picks up or hands off
- Fields: the `outcomeeng` organization issue fields `Product` (methodology | spx | plugins), `Maturity` (Proposed | Framed | Sliced | Executable), `Lifecycle` (Available | Claimed | Submitted | Applied | Abandoned), the text issue field `Predecessors`, and the number issue field `Parent`; no project field holds a Change field
- Priority: the `outcomeeng` single-select issue field `Priority`, whose order from first to last is Blocker, Urgent, Normal, Deferred; a Change with no value stands with Deferred
