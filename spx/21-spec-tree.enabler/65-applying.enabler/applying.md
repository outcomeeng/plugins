# Applying

PROVIDES an 8-phase TDD flow (architect, test, code + audit gates) extended by a conditional whole-changeset review and a terminal merge-lifecycle gate, driven by spec assertions
SO THAT all implementation agents
CAN produce implementations that conform to their governing specs on the first pass

## Assertions

### Compliance

- ALWAYS: invoke `/contextualize` for the work item before any implementation — the flow loads node context before code is written ([audit])
- ALWAYS: write tests before implementation — tests derive from spec assertions, not from code ([review])
- ALWAYS: run all three audit gates after implementation — skipping gates produces unverified evidence ([review])
- ALWAYS: when an audit gate returns REJECT, attempt remediation before proceeding — the gate verdict governs progression ([audit])
- ALWAYS: when the change touches files or specs beyond the target node, run a whole-changeset review (the `changes-reviewer` agent or `/review-changes`) over the full diff and point the language audit gates at the whole changeset before declaring the flow complete — per-node gates miss cross-node effects ([audit])
- ALWAYS: for default-branch work, the flow is incomplete until the change reaches the default branch on origin through `/merge`; an approved code audit, a converged whole-changeset review, passing tests, and a clean committed branch are local readiness, not completion — the flow continues into `/merge` unless the user explicitly scoped the work to a proposal, analysis, review, or local-only change, or an explicit lifecycle gate blocks with no independent local action remaining, per `spx/15-merging.pdr.md` and the `/understand` default-branch completion boundary ([audit])
- NEVER: modify a spec assertion to make a failing test pass — the declaration governs ([review])
- NEVER: a runtime hook enforces the audit gates — the gate reminders are skill prose, and the spec-tree plugin ships no `PostToolUse` hook (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); enforcement is the flow's own discipline, not a hook ([review])
