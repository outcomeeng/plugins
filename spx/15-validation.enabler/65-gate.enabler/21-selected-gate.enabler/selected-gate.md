# Selected Gate

PROVIDES changed-path selection for the local `check` wrapper
SO THAT coding agents and contributor workstations
CAN run the deterministic gate steps that prove the current slice without spending local time on unrelated full-gate work

## Assertions

### Mappings

- Changed repository paths map to a deterministic ordered subset of source-owned validation steps, with each selected step carrying a human-readable reason for inclusion ([test](tests/test_selected_gate.mapping.l1.py))
- Changed Python test assertion files map to a pytest step targeted at those files, while the full-gate wrapper preserves the complete validation-plus-test recipe set for CI and explicit full-gate runs ([test](tests/test_selected_gate.mapping.l1.py))

### Properties

- Gate selection is deterministic for any ordering or duplication of the same changed-path set ([test](tests/test_selected_gate.property.l1.py))

### Compliance

- ALWAYS: the selected gate prints the selected steps and reasons before running them through the existing signal-safe recipe orchestrator, preserving bounded output and structured summaries ([test](tests/test_selected_gate.compliance.l1.py))
- ALWAYS: when the canonical changeset-scope helper cannot resolve the remote default branch, the selected gate returns its structured git-discovery failure instead of propagating the helper exception ([test](tests/test_selected_gate.compliance.l1.py))
