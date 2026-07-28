# Apply

PROVIDES the apply lifecycle — selecting the next executable observable slice, then driving each node in that slice through the per-node TDD flow — bounded by a whole-changeset review and a terminal merge-lifecycle gate
SO THAT all implementation agents
CAN turn an implementation plan into demonstrable value merged to the default branch, with each node conforming to its governing spec on the first pass

The assertions below govern the lifecycle as a whole — how the work queue is formed and dispatched, and the cross-cutting properties that hold across the slice: the whole-changeset review that gates flow completion, the delivered-value boundary that holds until the change reaches the default branch, and the gate-enforcement model.

## Assertions

### Compliance

- ALWAYS: with a canonical full `spx/...` node-path argument the work queue is that single node, and with no argument it is derived from the conversation, falling back to the paths stored relative to `spx/` in `spx/EXCLUDE` after converting each one to its canonical full `spx/...` address ([audit])
- NEVER: the apply lifecycle delegates its per-node authoring and implementation work to a separate agent — the main conversation runs the per-node flow itself and dispatches only the auditor and reviewer agents its gates require ([audit])
- ALWAYS: a multi-node work queue runs in ascending numeric-index order, removing each node from `spx/EXCLUDE` before its flow and preserving each stabilized gate subject in a local checkpoint commit whose recorded verification state is `passing`, `failing`, or `not-run`; agentic gate dispatch still requires deterministic passing, and a node whose flow cannot converge stops the queue with the remaining nodes left in `spx/EXCLUDE` ([audit])
- ALWAYS: every persisted audit or review gate binds to an exact committed head after deterministic verification passes; a rejected finding is repaired in a new local checkpoint before the gate reruns, while an audit over modified or untracked files is advisory and never satisfies a gate ([audit])
- ALWAYS: when the repository requires the full deterministic gate, run `just check-full` only after every applicable evidence audit, implementation audit, and whole-changeset review has converged, and run no agentic verification after it; any change after the full gate invalidates it and requires the agentic gates to converge again before a new full-gate run ([audit])
- ALWAYS: when the change touches files or specs beyond the target node, run required evidence-auditor gates for touched `[test]` and `[eval]` evidence before the whole-changeset review, run the whole-changeset review through the `changes-reviewer` agent over the full diff, and point all audit handoffs at the whole changeset before declaring the flow complete — per-node gates miss cross-node effects ([audit])
- ALWAYS: for default-branch work, the flow is incomplete until the change reaches the default branch on origin through `/merge`; an approved code audit, a converged whole-changeset review, passing tests, and a clean committed branch are local readiness, not completion — the flow continues into `/merge` unless the user explicitly scoped the work to a proposal, analysis, review, or local-only change, or an explicit lifecycle gate blocks with no independent local action remaining, per `spx/15-merging.pdr.md` and the `/understand` default-branch completion boundary ([audit])
- NEVER: a runtime hook enforces the audit gates — the gate reminders are skill prose, and the spec-tree plugin ships no `PostToolUse` hook (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); enforcement is the flow's own discipline, not a hook ([audit])
