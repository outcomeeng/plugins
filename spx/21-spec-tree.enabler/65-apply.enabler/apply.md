# Apply

PROVIDES the apply lifecycle — selecting the next executable observable slice, then driving each node in that slice through the per-node TDD flow — bounded by a whole-changeset review and a terminal merge-lifecycle gate
SO THAT all implementation agents
CAN turn an implementation plan into demonstrable value merged to the default branch, with each node conforming to its governing spec on the first pass

The assertions below govern the lifecycle as a whole — how the work queue is formed and dispatched, and the cross-cutting properties that hold across the slice: the whole-changeset review that gates flow completion, the delivered-value boundary that holds until the change reaches the default branch, and the gate-enforcement model.

## Assertions

### Compliance

- ALWAYS: the apply instructions select the detected language's configured Go,
  Rust, or TypeScript simplifier after implementation and before the final
  implementation and evidence audits. The launch receives only the committed
  scope selector. The main conversation integrates the result, verifies every
  resulting change, and checkpoints it before Verifier dispatch; a language
  without a declared simplifier skips this stage ([audit])

- ALWAYS: each audit or review step explicitly selects its exact configured subagent and
  supplies only the target path or scope. The skill owns these invocation
  instructions and does not obtain a role-specific prompt from the root guide,
  per `spx/15-subagent-execution.pdr.md`. Accepted requirements are persisted in
  decisions and specs before dispatch. Each Verifier starts without authoring
  history and independently reads the target and configured instructions;
  the calling skill never appends an author-written context packet ([audit]).
- ALWAYS: invocation guidance requires exactly one native launch and analysis and
  reporting of a failed launch or unusable result without retry or substitution.
  Completed audit verdicts follow the existing gate and repair workflows ([audit]).

- ALWAYS: with a canonical full `spx/...` node-path argument the work queue is that single node, and with no argument it is derived from the conversation, falling back to the paths stored relative to `spx/` in `spx/EXCLUDE` after converting each one to its canonical full `spx/...` address ([audit])
- ALWAYS: the main conversation runs per-node authoring and implementation, delegates the declared behavior-preserving simplification stage, and dispatches the auditors and reviewers its gates require ([audit])
- ALWAYS: a multi-node work queue runs in ascending numeric-index order, removing each node from `spx/EXCLUDE` before its flow and preserving each stabilized gate subject in a local checkpoint commit whose recorded verification state is `passing`, `failing`, or `not-run`; agentic gate dispatch still requires deterministic passing, and a node whose flow cannot converge stops the queue with the remaining nodes left in `spx/EXCLUDE` ([audit])
- ALWAYS: every persisted audit or review gate binds to an exact committed head after deterministic verification passes; a rejected finding is repaired in a new local checkpoint before the gate reruns, while an audit over modified or untracked files is advisory and never satisfies a gate ([audit])
- ALWAYS: the apply lifecycle treats a started-run implementation-audit `BLOCKED` diagnostic carrying none of the three command-evidence shapes — an exit code with stderr, a named termination with stderr, or a harness-tool failure with the tool's name and error text — as an unusable result under its launch contract: the invocation stops, entering neither the repair loop nor a workflow relaunch, the result is reported to the operator or the orchestrating agent session standing in for the operator, and only that word authorizes one fresh dispatch as a new launch, while a complete diagnostic naming a failed command or a preparation failure keeps its repair path ([audit])
- ALWAYS: when the repository requires the full deterministic gate, run `just check-full` only after every applicable evidence audit, implementation audit, and whole-changeset review has converged, and run no agentic verification after it; any change after the full gate invalidates it and requires the agentic gates to converge again before a new full-gate run ([audit])
- ALWAYS: when the change touches files or specs beyond the target node, run required evidence-auditor gates for touched `[test]` and `[eval]` evidence before the whole-changeset review, run the whole-changeset review through the `changes-reviewer` agent over the full diff, and point all audit handoffs at the whole changeset before declaring the flow complete — per-node gates miss cross-node effects ([audit])
- ALWAYS: for default-branch work, the flow is incomplete until the change reaches the default branch on origin through `/merge`; an approved code audit, a converged whole-changeset review, passing tests, and a clean committed branch are local readiness, not completion — the flow continues into `/merge` unless the user explicitly scoped the work to a proposal, analysis, review, or local-only change, or an explicit lifecycle gate blocks with no independent local action remaining, per `spx/15-merging.pdr.md` and the `/understand` default-branch completion boundary ([audit])
- NEVER: a runtime hook enforces the audit gates — the gate reminders are skill prose, and the spec-tree plugin ships no `PostToolUse` hook (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); enforcement is the flow's own discipline, not a hook ([audit])
- ALWAYS: every per-node and whole-changeset Verifier dispatch the apply lifecycle makes is preceded by the readiness record bound to the exact clean committed head, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: the apply lifecycle invokes `/sync-base` before every deterministic verification command and before every Verifier dispatch, records the `already_current` or `rebased` result for the exact head in the readiness record, and treats a Verifier's `stale-base` block as no verdict — it synchronizes, re-establishes the deterministic results on the rebased head, and dispatches again, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: a Verifier rejection belonging to a previously recorded defect class stops the work queue at the node that raised it until the widened repair, same-class scan, and governing-workflow, standard, or source-contract amendment land, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: the apply lifecycle carries only the bounded projection of each Verifier result — the result reference, exact head, verdict, finding identifiers, defect classes, and next required action — reopening the complete result by reference, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: the apply lifecycle finishes every independent Author-side inspection, repair, same-class scan, deterministic check, readiness-record update, and required commit before it starts a blocking check or Verifier wait, per `spx/15-merging.pdr.md` ([audit])
