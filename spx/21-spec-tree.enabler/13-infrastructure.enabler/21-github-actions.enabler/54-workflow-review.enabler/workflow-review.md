# Workflow Review

PROVIDES static and semantic audit of existing workflow files against the design model, safety policy, and observed repository state
SO THAT workflow-evolution surfaces
CAN identify drift, fragility, and bad structure that justify rearchitecture or maintenance work

## Assertions

### Compliance

- ALWAYS: audit covers triggers, permissions, event trust, third-party action pinning, secrets, OIDC, caches, artifacts, runner trust, environments, concurrency, validation commands, dependency freshness, and maintainability boundaries — partial audits hide drift ([audit])
- ALWAYS: an audit compares workflow files against `21-platform-boundary` guidance, `32-workflow-safety` policy, `43-workflow-design` patterns, and observed repository state from `32-workflow-observability` when state is available — siblings are the audit's reference set ([audit])
- ALWAYS: an audit verdict names each non-conforming workflow file by path, the violated rule (citing the specific safety or design assertion), and the location within the file (job, step, line) — drive-by feedback is forbidden ([audit])
- ALWAYS: an audit distinguishes correctness failures, security failures, maintainability debt, and operational fragility — workflow evolution chooses the right kind of fix from this categorization ([audit])
- ALWAYS: an audit produces a structured verdict (APPROVED / REJECTED with itemized findings) rather than narrative prose — verdicts are consumed by `65-workflow-evolution` as decision input ([audit])
- NEVER: an audit modifies workflow files — review produces verdicts, not edits ([audit])
