# Test-Infrastructure Reach by Static Import Index

The selected gate decides how far a changed test-infrastructure module reaches by a static import index: the set of executed test files that import the module, directly or through other test-infrastructure modules, derived from `ast` import statements over the test-infrastructure package and every `spx/**/tests/` file. A module reached by tests under exactly one spec node is that node's concern and selects those tests; a module reached by tests under more than one node, by `conftest.py`, or by nothing the index can trace — a non-Python artifact read by path — is shared and selects the full surface. The planner receives the index as a value; the command edge builds it from the repository root.

## Rationale

Test infrastructure is production code whose only consumers are executed tests, so the tests that import a module are the complete set of evidence its change can alter. A directory-level rule cannot see that boundary and escalates every harness edit to the whole bundle, while a per-node rule that trusts a path prefix cannot see a harness two nodes share. The import graph is the one observable that answers both, and `ast` reads it without executing any module — importing a harness to discover its importers would run test-infrastructure code inside the gate and couple selection to the interpreter's module cache. Text search over import lines is rejected because it cannot resolve relative imports or distinguish a package import from a submodule import. A fixture consumed by path leaves no import edge, so the index cannot bound its reach and the full surface is the only safe answer. Passing the index as a value keeps `build_selected_gate_plan` a pure function of its inputs, so planning is verifiable against a synthetic repository under `tmp_path` while the command edge alone touches the real checkout.

## Invariants

- Reach is monotone: adding an importer never narrows a module's reach.
- A package `__init__` module is reached by every importer of any name from that package.
- The node of an executed test is the path prefix before its `tests/` directory.

## Verification

### Testing

- ALWAYS: every import statement form — `import a.b`, `from a.b import c` naming a submodule, `from a.b import c` naming an attribute, `from . import c`, and `from .c import d` — resolves to the test-infrastructure module names it depends on: the imported package or module, plus the submodule when the imported name resolves to one ([mapping])
- ALWAYS: reach closes transitively over test-infrastructure modules before it is projected onto executed tests, so a test that imports a harness reaches every module that harness imports ([scenario])
- NEVER: the index imports, executes, or reloads a test-infrastructure or test module to discover its dependencies — a module whose import has an observable side effect leaves no trace after the index is built ([compliance])

### Audit

- ALWAYS: `build_selected_gate_plan` accepts the test-infrastructure index as a parameter typed by a source-owned value class, and only the command edge (`run_selected_check`) constructs it from the repository root — enables `l1` verification of reach decisions against a synthetic repository ([audit])
- ALWAYS: the index is built from `ast.parse` over test-infrastructure modules and executed test files, resolving absolute and relative import statements into test-infrastructure module names ([audit])
- NEVER: the planner reads the filesystem or the environment to decide reach — every reach decision comes from the injected index ([audit])
- NEVER: a change under the test-infrastructure package selects the full surface by path pattern alone — the full surface follows from a reach the index reports as shared or untraceable ([audit])
