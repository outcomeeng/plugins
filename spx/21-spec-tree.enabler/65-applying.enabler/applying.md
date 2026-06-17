# Applying

PROVIDES an 8-phase TDD flow (architect, test, code + audit gates) driven by spec assertions
SO THAT all implementation agents
CAN produce implementations that conform to their governing specs on the first pass

## Assertions

### Compliance

- ALWAYS: invoke `/contextualize` for the work item before any implementation — the flow loads node context before code is written ([audit])
- ALWAYS: write tests before implementation — tests derive from spec assertions, not from code ([review])
- ALWAYS: run all three audit gates after implementation — skipping gates produces unverified evidence ([review])
- ALWAYS: when an audit gate returns REJECT, attempt remediation before proceeding — the gate verdict governs progression ([audit])
- ALWAYS: when the change touches files or specs beyond the target node, run a whole-changeset review (the `changes-reviewer` agent or `/review-changes`) over the full diff and point the language audit gates at the whole changeset before declaring the flow complete — per-node gates miss cross-node effects ([audit])
- NEVER: modify a spec assertion to make a failing test pass — the declaration governs ([review])
- NEVER: a runtime hook enforces the audit gates — the gate reminders are skill prose, and the spec-tree plugin ships no `PostToolUse` hook (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); enforcement is the flow's own discipline, not a hook ([review])
