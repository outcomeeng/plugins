# Aligning

PROVIDES systematic consistency checking across the spec tree — structural conformance, atemporal voice, and content placement
SO THAT all spec authors
CAN detect contradictions, gaps, and content misplacement before they reach implementation

## Assertions

### Scenarios

- Given a spec that contradicts an ancestor ADR compliance rule, when alignment is checked, then the contradiction is reported with the conflicting ADR reference ([test](tests/test_aligning.scenario.l1.py))
- Given a spec with implementation details that belong in an ADR, when alignment is checked, then the content misplacement is flagged ([test](tests/test_aligning.scenario.l1.py))
- Given a spec with temporal language, when alignment is checked, then the temporal markers are identified with atemporal rewrites ([test](tests/test_aligning.scenario.l1.py))

### Compliance

- ALWAYS: check specs against all ancestor ADRs/PDRs — decision records win by hierarchy ([audit])
- ALWAYS: when checking a changeset, report a product spec, ADR, PDR, or ancestor spec change that lacks both aligned first affected lower specs and first-affected-node `PLAN.md` grounding, deriving the changed-file set through `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` rather than ad hoc git diff logic ([audit])
- NEVER: weaken a spec to match code or tests — the declaration governs ([audit])
