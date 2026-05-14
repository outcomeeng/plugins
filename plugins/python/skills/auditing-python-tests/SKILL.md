---
name: auditing-python-tests
disable-model-invocation: true
description: Use when asked by the user to invoke the Python test audit skill
allowed-tools: Read, Grep, Glob, Bash
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-python/SKILL.md" || echo "standardizing-python not found — invoke python:standardizing-python manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-python-tests/SKILL.md" || echo "standardizing-python-tests not found — invoke python:standardizing-python-tests manually"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/testing/SKILL.md" || echo "testing not found — invoke spec-tree:testing manually"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/auditing-tests/SKILL.md" || echo "auditing-tests not found — invoke spec-tree:auditing-tests manually"`

!`test -f spx/local/python.md && cat spx/local/python.md || true`

!`test -f spx/local/python-tests.md && cat spx/local/python-tests.md || true`

<codex_fallback>
If the `cat` commands above appear as literal text, invoke these skills before proceeding:

1. `python:standardizing-python`
2. `python:standardizing-python-tests`
3. `spec-tree:testing`
4. `spec-tree:auditing-tests`
5. Read `spx/local/python.md` if it exists
6. Read `spx/local/python-tests.md` if it exists

</codex_fallback>

<objective>
Audit Python test evidence against the spec-tree test-audit properties plus Python-specific source ownership, testability, harness, generator, inert-fixture, and pytest discovery rules.

This skill audits tests and test infrastructure. It does not audit production implementation style except where source architecture affects test evidence quality.
</objective>

<audit_scope>
For every in-scope test assertion, inspect the full evidence chain:

- The spec assertion and selected evidence type
- The executed test file
- Imported production modules
- Imported `product_testing.harnesses.*` modules
- Imported `product_testing.generators.*` modules
- Inert fixture path providers and fixture data files referenced by the test
- `conftest.py` files that apply to the test

Do not approve a test by looking only at the test file. Laundering and severed coupling can live in generators, harnesses, fixture path providers, and pytest discovery shims.
</audit_scope>

<gate_0_deterministic>
Run deterministic checks before judgment when the repository provides the tools:

```bash
bad_test_names="$(rg --files <spec-node-path>/tests/ --glob '*.py' | rg -v '/test_[^.]+\.(scenario|mapping|conformance|property|compliance)\.l[123](\.[^.]+)?\.py$' || true)"
test -z "$bad_test_names"
uv run pytest --collect-only -q <spec-node-path>/tests/
uv run ruff check <spec-node-path>/tests/
uv run mypy <spec-node-path>/tests/
```

Use repository-canonical commands when they exist. Report unavailable tools separately instead of silently skipping them.

If collection, linting, type checking, or repository-canonical deterministic checks fail, halt the audit and emit `REJECT` with the failing command and diagnostic. Do not proceed to semantic evidence judgment on uncollectable, untyped, or lint-failing tests.
</gate_0_deterministic>

<coupling_audit>
Classify imports by runtime coupling:

| Import pattern                                         | Classification                          |
| ------------------------------------------------------ | --------------------------------------- |
| `import pytest`                                        | Framework, does not count               |
| `from hypothesis import given`                         | Framework, does not count               |
| `import json`                                          | Stdlib, does not count                  |
| `from typing import TYPE_CHECKING`                     | Type-only, does not count               |
| `from product.config import parse_config`              | Production coupling                     |
| `from product_testing.harnesses import config_harness` | Indirect coupling through harness       |
| `from product_testing.generators import valid_config`  | Input-domain provider, audit separately |

Imports inside `if TYPE_CHECKING:` do not create runtime coupling. A test with only framework, stdlib, and type-only imports is a tautology unless it reaches production through a harness that itself reaches production.

When a test imports a harness, inspect the harness and verify it calls the production behavior the assertion is about. A harness that builds expected values without exercising production is severed coupling.
</coupling_audit>

<falsifiability_audit>
Reject replacement of the behavior under test:

- `unittest.mock.patch` replacing the production function, class, module, client, or repository the assertion claims to verify
- `Mock()` or `MagicMock()` standing in for behavior the assertion claims to verify
- `mocker.patch(...)` replacing the dependency under test
- `monkeypatch` replacing the behavior under test
- `sys.path` or `importlib` tricks that cause tests to import alternate modules

Accept explicit test doubles only when they are passed through dependency injection and map to a `/testing` Stage 5 exception:

| Exception             | Python pattern                             |
| --------------------- | ------------------------------------------ |
| Failure modes         | Class implementing a protocol and raising  |
| Interaction protocols | Class with typed call recording            |
| Time/concurrency      | Injected clock or controllable scheduler   |
| Safety                | Class that records intent                  |
| Combinatorial cost    | Configurable class mirroring real behavior |
| Observability         | Class capturing hidden boundary details    |
| Contract probes       | Stub validated against a real schema       |

</falsifiability_audit>

<source_ownership_audit>
Reject test-owned source vocabulary:

- Local constants in tests for source-owned values
- Shared constant bags in tests, helpers, harnesses, or generators
- Production modules created only to aggregate test values
- Fixture files containing isolated strings or numbers
- Generators that return source-owned singleton shapes through `st.just(...)`, singleton `st.sampled_from(...)`, or constant-returning functions

Pass only when source vocabulary comes from the owning production module, runtime package, framework package, schema, enum, registry, constructor, or typed factory.
</source_ownership_audit>

<generator_audit>
Audit every imported generator:

- It represents a variable input domain with meaningful variation, composition, or shrinkage
- It does not duplicate source-owned vocabulary
- It does not hide arbitrary example values behind a strategy name
- It derives expected outputs from generated inputs, an independent oracle, or a source outside the module under test

Property evidence requires a meaningful property. `@given` that only checks for lack of exceptions is insufficient.
</generator_audit>

<harness_audit>
Audit every imported harness:

- It manages setup, teardown, cleanup, dependency checks, or access to external behavior
- It reaches the production behavior the assertion is about
- It does not replace the behavior under test with framework mocks, monkeypatches, environment stubs, network fakes, or alternate imports
- It cleans up temp dirs, subprocesses, services, Docker resources, browsers, databases, and environment changes
- It does not own arbitrary test data that belongs in source modules or generators

Pytest fixture callables that perform setup, teardown, cleanup, or dependency access are harness entrypoints. They belong under `product_testing.harnesses.*`.
</harness_audit>

<fixture_audit>
Audit inert fixture files and fixture path providers:

- Fixture files are real-world payloads whose complete shape matters to the assertion
- Tests consume fixture files by path, reading, or copying
- Tests do not import fixture files as Python modules
- Fixture files do not store isolated strings or numbers as test data

Reject Python modules under `product_testing/fixtures/` that export pytest fixture body functions. That category is for inert data files under the PDR vocabulary.
</fixture_audit>

<conftest_audit>
Inspect every `conftest.py` that applies to the test path.

Allowed content:

- Explicit imports of pytest fixture callables from `product_testing.harnesses.*`
- Pytest marker registration
- Pytest hooks that configure collection or reporting

Rejected content:

- Fixture body code
- Harness classes or setup policy
- Generated data
- Source-owned protocol values
- Star imports from test infrastructure packages
- Mocking, monkeypatching, or import-path mutation

</conftest_audit>

<architectural_dry_audit>
When two or more in-scope tests repeat setup or infrastructure logic, reject the duplication and identify the canonical destination:

| Repeated pattern                                      | Destination                         |
| ----------------------------------------------------- | ----------------------------------- |
| Temp product scaffolding                              | `product_testing.harnesses.*`       |
| Subprocess or CLI execution setup                     | `product_testing.harnesses.*`       |
| Database, Docker, browser, service, or API setup      | `product_testing.harnesses.*`       |
| Domain-shaped input construction with variable values | `product_testing.generators.*`      |
| Real-world payload samples                            | `product_testing/fixtures/` as data |

Do not recommend `tests/helpers`, `tests/support`, node-local helper modules, or fixture body code in `conftest.py`.
</architectural_dry_audit>

<verdict_format>
Follow `<verdict_format>` in `/auditing-tests`.

For each finding, include:

- Verdict property: coupling, falsifiability, alignment, coverage, source ownership, domain variation, oracle independence, cleanup safety, or pytest discovery safety
- Exact file and line
- The imported chain when the defect is outside the test file
- Required fix

Emit `APPROVED` only when Gate 0 and all evidence-property checks pass. Emit `REJECT` when any property fails.
</verdict_format>

<failure_modes>
Failure 1: Accepted `TYPE_CHECKING` import as coupling.

Claude saw `from product.theme import ThemeColor` inside an `if TYPE_CHECKING:` block and counted it as runtime coupling. The test declared its own color values and never executed production code. Avoid this by ignoring type-only imports for coupling.

Failure 2: Missed coupling severed by `@patch`.

Claude saw a production import and approved the test, while `@patch("product.database.query")` replaced the imported behavior. Avoid this by checking decorators, fixtures, monkeypatch usage, and harness setup code.

Failure 3: Accepted a generator that only hid a constant.

Claude saw a Hypothesis strategy and treated it as property evidence. The strategy returned one copied source value through `st.just(...)`. Avoid this by inspecting generator bodies and requiring meaningful variation.

Failure 4: Accepted pytest fixture body code in `conftest.py`.

Claude treated pytest discovery as a reason to put setup logic in `conftest.py`. The PDR requires harness logic to live in the canonical test-infrastructure package. Avoid this by checking every applying `conftest.py`.
</failure_modes>

<success_criteria>
A Python test audit succeeds when:

- Gate 0 deterministic checks are run or unavailable tools are reported
- Every test is traced to the spec assertion and selected evidence type
- Runtime coupling reaches production behavior directly or through audited harnesses
- No framework mock, monkeypatch, or import trick replaces the behavior under test
- Source-owned values come from source modules or owning packages
- Generators represent meaningful variable domains
- Harnesses manage resource lifecycle and cleanup without owning arbitrary data
- Inert fixtures are consumed only as files
- `conftest.py` is limited to discovery, registration, and explicit harness imports
- The verdict lists exact evidence-property findings or emits `APPROVED`

</success_criteria>
