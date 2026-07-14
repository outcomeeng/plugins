# Aligning

PROVIDES systematic consistency checking across the spec tree — structural conformance, atemporal voice, and content placement
SO THAT all spec authors
CAN detect contradictions, gaps, and content misplacement before they reach implementation

## Assertions

### Scenarios

- Given a branch whose remote-tracking base contains changes already merged from the branch, when alignment derives changeset scope, then it reports the configured base and only the branch's complete canonical changed-file set ([test](tests/test_alignment_scope.scenario.l1.py))
- Given a repository without a configured remote default branch, when alignment derives changeset scope, then it exits nonzero with structured remediation rather than guessing a base ([test](tests/test_alignment_scope.scenario.l1.py))

### Compliance

- ALWAYS: check specs against all ancestor ADRs/PDRs — decision records win by hierarchy ([review])
- ALWAYS: when checking a changeset, report a product spec, ADR, PDR, or ancestor spec change that lacks both aligned first affected lower specs and first-affected-node `PLAN.md` grounding, deriving the changed-file set through `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` rather than ad hoc git diff logic ([review])
- ALWAYS: report a spec that contradicts an ancestor ADR compliance rule with the conflicting ADR reference ([audit])
- ALWAYS: flag implementation details that belong in an ADR as content misplacement ([audit])
- ALWAYS: identify temporal markers in specs with atemporal rewrites ([audit])
- NEVER: weaken a spec to match code or tests — the declaration governs ([review])
