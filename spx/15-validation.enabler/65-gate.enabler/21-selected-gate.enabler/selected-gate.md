# Selected Gate

PROVIDES changed-path selection of deterministic gate steps for the local `check` wrapper, and the skip of the L3 tests from `just check` and `just check-full`
SO THAT coding agents, contributor workstations, and CI
CAN run the deterministic gate steps that prove the current slice without spending local time on unrelated full-gate work or on tests that need credentials and consume quota

## Assertions

### Mappings

- Changed repository paths map to a deterministic ordered subset of source-owned validation steps, with each selected step carrying a human-readable reason for inclusion: a Markdown or spec path selects the formatting check and the spx Markdown validation with the Markdown reason; a workflow or shell path selects actionlint and ShellCheck with the workflow reason; a Python path selects ruff format and ruff check, and a path of an importable product package also selects mypy and pyright, each with the Python reason; a plugin skill, shared fragment, or generated runtime path selects the steps the gate names as its skill surface with the skill reason; an instruction-block source path selects the instruction-block diff with the instruction-block reason; an eval trigger path selects the eval-trigger check and an eval prompt path the eval-prompt check, each with the eval reason; and a Product Tree path selects the evidence-link check with the evidence-link reason ([test](tests/test_selected_gate.mapping.l1.py))
- Changed Python test assertion files map to a pytest step targeted at those files other than L3 tests, while the full-gate wrapper preserves the complete validation-plus-test recipe set for CI and explicit full-gate runs except the L3 tests [`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md) declares ([test](tests/test_selected_gate.mapping.l1.py))
- Changed paths under the test-infrastructure package map by the reach the static import index reports, per [`spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/21-test-infrastructure-reach.adr.md`](spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/21-test-infrastructure-reach.adr.md): a module reached by executed tests under exactly one node selects a pytest step targeted at exactly those tests other than L3 tests; a module reached by tests under more than one node or by `conftest.py`, and any non-Python artifact, selects the full surface without the L3 tests; a module no test reaches selects no test step ([test](tests/test_selected_gate.mapping.l1.py))
- A changed path under `spx/` maps to the evidence-link integrity step alongside the markdown lane, and a changed path outside `spx/` does not select it — a spec edit that leaves a `[test]` or `[eval]` link dangling fails the selected gate ([test](tests/test_selected_gate.mapping.l1.py))
- Every import statement form an executed test or test-infrastructure module can carry — `import a.b`, `from a.b import c` naming a submodule, `from a.b import c` naming an attribute, `from . import c`, and `from .c import d` — maps to the test-infrastructure module names the static import index records for it: the imported module and every package on its dotted path, plus the submodule when the imported name resolves to one ([test](tests/test_infrastructure_index.mapping.l1.py))

### Scenarios

- Given a harness module that imports a generator module and an executed test that imports only the harness, when the index is built, then the generator's reach includes that test ([test](tests/test_infrastructure_index.scenario.l1.py))

### Properties

- Gate selection is deterministic for any ordering or duplication of the same changed-path set ([test](tests/test_selected_gate.property.l1.py))
- For any set of changed test files drawn across every execution level, the planned pytest step targets exactly the files other than L3 tests, and no pytest step is planned when every file is an L3 test ([test](tests/test_selected_gate.property.l1.py))
- For any chain of test-infrastructure modules in which each imports the next and an executed test imports the first, every module in the chain reaches that test ([test](tests/test_infrastructure_index.property.l1.py))

### Compliance

- ALWAYS: `just check` and `just check-full` select no L3 test, the real-agent Codex tests among them, whatever the changeset changes ([test](tests/test_selected_gate.compliance.l1.py))
- NEVER: the skip of the L3 tests removes any other step or test from the selected deterministic scope, including when local selection widens to the full deterministic suite ([test](tests/test_selected_gate.compliance.l1.py))
- ALWAYS: the plan displays the skip of the L3 tests and its reason before running selected steps ([test](tests/test_selected_gate.compliance.l1.py))
- ALWAYS: the selected gate prints the selected steps and reasons before running them through the existing signal-safe recipe orchestrator, preserving bounded output and structured summaries ([test](tests/test_selected_gate.compliance.l1.py))
- ALWAYS: when the canonical changeset-scope helper cannot resolve the remote default branch, the selected gate returns its structured git-discovery failure instead of propagating the helper exception ([test](tests/test_selected_gate.compliance.l1.py))
- NEVER: building the static import index imports, executes, or reloads a test-infrastructure or test module — a module whose import has an observable side effect leaves no trace after the index is built ([test](tests/test_infrastructure_index.compliance.l1.py))
- NEVER: the planner classifies a changed test-infrastructure path without the reach index — a plan built with none supplied raises the source-owned error naming the paths it cannot classify ([test](tests/test_selected_gate.compliance.l1.py))
