# Selected Gate

PROVIDES changed-path selection for the local `check` wrapper
SO THAT coding agents and contributor workstations
CAN run the deterministic gate steps that prove the current slice without spending local time on unrelated full-gate work

## Assertions

### Mappings

- Changed repository paths map to a deterministic ordered subset of source-owned validation steps, with each selected step carrying a human-readable reason for inclusion ([test](tests/test_selected_gate.mapping.l1.py))
- Changed Python test assertion files map to a pytest step targeted at those files, while the full-gate wrapper preserves the complete validation-plus-test recipe set for CI and explicit full-gate runs ([test](tests/test_selected_gate.mapping.l1.py))
- Changed paths under the test-infrastructure package map by the reach the static import index reports, per `spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/21-test-infrastructure-reach.adr.md`: a module reached by executed tests under exactly one node selects a pytest step targeted at exactly those tests; a module reached by tests under more than one node or by `conftest.py`, and any non-Python artifact, selects the full surface; a module no test reaches selects no test step ([test](tests/test_selected_gate.mapping.l1.py))
- Every import statement form an executed test or test-infrastructure module can carry — `import a.b`, `from a.b import c` naming a submodule, `from a.b import c` naming an attribute, `from . import c`, and `from .c import d` — maps to the test-infrastructure module names the static import index records for it: the imported module and every package on its dotted path, plus the submodule when the imported name resolves to one ([test](tests/test_infrastructure_index.mapping.l1.py))

### Scenarios

- Given a harness module that imports a generator module and an executed test that imports only the harness, when the index is built, then the generator's reach includes that test ([test](tests/test_infrastructure_index.scenario.l1.py))

### Properties

- Gate selection is deterministic for any ordering or duplication of the same changed-path set ([test](tests/test_selected_gate.property.l1.py))
- For any chain of test-infrastructure modules in which each imports the next and an executed test imports the first, every module in the chain reaches that test ([test](tests/test_infrastructure_index.property.l1.py))

### Compliance

- ALWAYS: the selected gate prints the selected steps and reasons before running them through the existing signal-safe recipe orchestrator, preserving bounded output and structured summaries ([test](tests/test_selected_gate.compliance.l1.py))
- ALWAYS: when the canonical changeset-scope helper cannot resolve the remote default branch, the selected gate returns its structured git-discovery failure instead of propagating the helper exception ([test](tests/test_selected_gate.compliance.l1.py))
- NEVER: building the static import index imports, executes, or reloads a test-infrastructure or test module — a module whose import has an observable side effect leaves no trace after the index is built ([test](tests/test_infrastructure_index.compliance.l1.py))
- NEVER: the planner classifies a changed test-infrastructure path without the reach index — a plan built with none supplied raises the source-owned error naming the paths it cannot classify ([test](tests/test_selected_gate.compliance.l1.py))
