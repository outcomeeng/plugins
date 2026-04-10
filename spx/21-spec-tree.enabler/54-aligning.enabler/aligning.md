# Aligning

PROVIDES systematic consistency checking across the spec tree — structural conformance, atemporal voice, and content placement
SO THAT all spec authors
CAN detect contradictions, gaps, and content misplacement before they reach implementation

## Assertions

### Scenarios

- Given a spec that contradicts an ancestor ADR compliance rule, when alignment is checked, then the contradiction is reported with the conflicting ADR reference ([test](tests/test_aligning.unit.py))
- Given a spec with implementation details that belong in an ADR, when alignment is checked, then the content misplacement is flagged ([test](tests/test_aligning.unit.py))
- Given a spec with temporal language, when alignment is checked, then the temporal markers are identified with atemporal rewrites ([test](tests/test_aligning.unit.py))

### Compliance

- ALWAYS: check specs against all ancestor ADRs/PDRs — decision records win by hierarchy ([review])
- NEVER: weaken a spec to match code or tests — the declaration governs ([review])
