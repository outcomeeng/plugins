---
name: audit-python-tests
description: >-
  ALWAYS invoke this skill when auditing Python test evidence, reviewing Python tests for spec-tree evidence quality, or evaluating Python test infrastructure.
  NEVER audit Python test evidence without this skill.
allowed-tools: Read, Grep, Glob, Bash
---

Invoke the `python:python-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `python:python-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:audit-tests` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

!`test -f spx/local/python.md && cat spx/local/python.md || true`

!`test -f spx/local/python-tests.md && cat spx/local/python-tests.md || true`

Any overlay loaded above routes skill behavior to the product's governing specs and decisions; a local overlay supplements skill behavior and does not declare product truth.

<objective>
Audit Python test evidence against the spec-tree test-audit properties plus Python-specific source ownership, testability, harness, generator, inert-fixture, and pytest discovery rules.

This skill audits tests and test infrastructure. It does not audit production implementation style except where source architecture affects test evidence quality.
</objective>

<audit_scope>
For every in-scope test assertion, inspect the full evidence chain:

- The spec assertion and selected assertion type
- The executed test file
- Imported production modules
- Imported `product_testing.harnesses.*` modules
- Imported `product_testing.generators.*` modules
- Inert fixture path providers and fixture data files referenced by the test
- `conftest.py` files that apply to the test

Do not approve a test by looking only at the test file. Laundering and severed coupling can live in generators, harnesses, fixture path providers, and pytest discovery shims.
</audit_scope>

<gate_0_deterministic>
Run deterministic checks before judgment when the repository provides the tools. Prefer the repository's canonical commands — those its `CLAUDE.md` / `AGENTS.md`, Justfile, Makefile, or package scripts document; the `python3 -m …` forms below are the portable fallback when the product ships no wrapper:

```bash
bad_test_names="$(rg --files <spec-node-path>/tests/ --glob '*.py' | rg -v '/test_[^.]+\.(scenario|mapping|conformance|property|compliance)\.l[123](\.[^.]+)?\.py$' || true)"
test -z "$bad_test_names"
python3 -m pytest --collect-only -q <spec-node-path>/tests/
python3 -m ruff check <spec-node-path>/tests/
python3 -m mypy <spec-node-path>/tests/
```

Report unavailable tools separately instead of silently skipping them.

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

Accept explicit test doubles only when they are passed through dependency injection and map to a `/test` Stage 5 exception:

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
The audit asks one question per test case: *where does this case come from?* The legitimate sources:

| Assertion type | Case source                                                                                                                                                            |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Scenario       | The spec assertion text — the case is declared by the spec, not invented by the test author                                                                            |
| Mapping        | A finite source-owned enumeration (enum, registry, schema, structured metadata)                                                                                        |
| Property       | A generator over a domain — the author writes the invariant, the generator owns the cases                                                                              |
| Conformance    | An external oracle (schema validator, reference implementation, parser the test doesn't author)                                                                        |
| Compliance     | The decision record being enforced — the case is the rule itself                                                                                                       |
| Any (fixture)  | An inert fixture file under `product_testing/fixtures/`, passed to the code under test as a file path or byte stream — the file's whole real-world payload is the case |

The first five rows pair an assertion type with the case source it normally takes. The Fixture row is cross-cutting: any assertion type may use an inert fixture file as the case. An auditor classifying a test case checks both the assertion type and whether the case is a whole-payload fixture file.

A case that does not have a documentable source outside the author's head is a tautology dressed as a measurement — the test confirms the author's understanding forever, never the spec. The defect is in the case's *origin*. Lexical location (`Final` at module scope, plain assignment, inline literal), syntactic form, and reuse pattern (shared bag, single-value, parametrize row) are irrelevant — the audit names them only as forms the same defect takes.

**Vocabulary check (where the values live).** Independently of case provenance, the *values* used in cases must come from the right home:

| Value kind                                                   | Lives in                                                                      |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| Production vocabulary (labels, paths, schema fields, tokens) | Owning production module, imported                                            |
| Variable input domain                                        | Generator under `product_testing/generators/`                                 |
| Resource-bound or runner-tuning value (timeouts, retries)    | The harness module that owns the resource, under `product_testing/harnesses/` |
| Whole-payload real-world sample                              | Inert fixture file under `product_testing/fixtures/`, read by path            |
| One-off descriptive text (test titles, diagnostic messages)  | Inline in the test function body                                              |

For each test case, name the source. REJECT against the missing source when:

- The case's value is production vocabulary the test re-declares instead of imports.
- The case's value is a container key or f-string template key hand-written by the author — keys are vocabulary; the key belongs to the owning production module.
- The case's value is a hand-copied YAML/HCL/bash/JSON schema field name — artifacts are downstream; the Python module that renders or consumes the artifact owns the vocabulary, and that module must be created if it does not yet exist.
- The case's value is a runner-tuning literal at test scope — the harness that owns the resource owns the timeout, retry count, or polling interval.
- The case's input or expected output is hand-picked by the author with no source the audit can name — REJECT, the case is a tautology regardless of where it sits lexically.

When the missing source is an architectural defect (the Python module that should own the vocabulary does not yet exist), name the module that should be created and the spec-tree node that should govern it.

Pass only when every case is traceable to a source independent of the author and every value lives in its proper home.
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
Follow `<verdict_format>` in `/audit-tests`.

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

Claude treated pytest discovery as a reason to put setup logic in `conftest.py`. The PDR requires harness logic to live in the product's test-infrastructure implementation home. Avoid this by checking every applicable `conftest.py`.

Failure 5: Accepted a hand-picked test case as evidence.

Claude saw `parse("name=alice")` followed by `assert result.name == "alice"` and approved the test. The string `"name=alice"` was invented by the author to demonstrate their understanding of the parser. The same author wrote (or read) the parser. Every future run confirms the author's understanding — that `"name=alice"` parses to a record with `name` field equal to `"alice"` — never the spec assertion about parser correctness. Avoid this by asking, for every case, where the case comes from: a generator, an oracle, a fixture, source-owned vocabulary, or the spec assertion text itself. If the answer is "the author chose it because it seemed reasonable", REJECT.

Failure 6: Container-literal keys treated as opaque scaffolding.

Claude saw `INVENTORY_JSON = f'{{"flatcar-version":"{VERSION}",...}}'` and classified it as test-fixture scaffolding because the *values* were synthetic. The *keys* were production-owned label vocabulary the author hand-wrote into the template — hand-picked cases for the parser or consumer that reads the JSON. Avoid this by auditing keys and values separately; the construction `json.dumps({LABEL: synthetic_value, ...})` with `LABEL` imported is the only legitimate form.

Failure 7: "Artifact is the source-of-truth" rationalization.

Claude saw a test that hand-copied a YAML field name (`"flatcar-version"`), an HCL attribute, or a systemd unit path. The value appeared in a parsed artifact file but no Python module owned it. Claude classified the artifact as the source-of-truth and accepted the case. The artifact is downstream — a Python module either renders or consumes it, and the absence of that Python module is the architectural defect, not the test's fault for finding nothing to import. Avoid this by naming the missing source-of-truth module and the spec-tree node that should govern it; REJECT against the missing module.
</failure_modes>

<success_criteria>
A Python test audit succeeds when:

- Gate 0 deterministic checks are run or unavailable tools are reported
- Every test is traced to the spec assertion and selected assertion type
- Runtime coupling reaches production behavior directly or through audited harnesses
- No framework mock, monkeypatch, or import trick replaces the behavior under test
- Source-owned values come from source modules or owning packages
- Every test case is traceable to a source independent of the author — spec assertion text, source-owned enumeration, generator over a domain, external oracle, decision record, or inert fixture file
- Container keys are imported from the owning production module, not hand-written
- Runner-tuning values live on the harness that owns the resource, not at test scope
- Missing source-of-truth modules are named in the verdict and routed to source-shape improvement, not absorbed into the test
- Generators represent meaningful variable domains
- Harnesses manage resource lifecycle and cleanup without owning arbitrary data
- Inert fixtures are consumed only as files
- `conftest.py` is limited to discovery, registration, and explicit harness imports
- The verdict lists exact evidence-property findings or emits `APPROVED`

</success_criteria>
