# Decisions

PROVIDES the decision record lifecycle — creation, auditing, and downstream enforcement of ADRs and PDRs
SO THAT all spec-tree projects
CAN govern architecture and product behavior through enforceable, auditable decision records

## Assertions

### Compliance

- ALWAYS: a decision record's rules flow into spec assertions that enforce them somewhere in the governed subtree ([audit])
- ALWAYS: a decision record groups its rules under `## Verification` by verdict mode — `### Audit`, `### Eval`, `### Testing`; a `Testing` rule carries a `/testing`-routed claim-shape mode (scenario, mapping, conformance, property, compliance), and an `### Audit` or `### Eval` rule carries `[audit]` or `[eval]` for subjects — Spec Tree decisions, specs, skills, agents — that admit no deterministic test ([audit])
- NEVER: approve a decision record whose rules have zero downstream enforcement ([audit])
