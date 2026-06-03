# Decisions

PROVIDES the decision record lifecycle — creation and auditing of ADRs and PDRs
SO THAT all spec-tree projects
CAN govern architecture and product behavior through enforceable, auditable decision records

## Assertions

### Compliance

- ALWAYS: a decision record groups its rules under `## Verification` by verification type — `### Testing`, `### Eval`, `### Audit`; a `### Testing` rule carries a `/testing`-routed evidence type (scenario, mapping, conformance, property, compliance), an `### Eval` rule carries `[eval]`, and an `### Audit` rule carries `[audit]` — for subjects (Spec Tree decisions, specs, skills, agents) that admit no deterministic test ([audit])
