---
name: audit-python-tests
description: >-
  Python test-evidence audit methodology composed by a dispatched test-evidence-auditor or implementation-auditor for the Python tests in scope.
  Reached only through those auditor agents, never the main conversation.
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Skill
---

<dispatch_gate>

This audit runs inside either the dispatched `test-evidence-auditor` context via `audit-tests` or the dispatched `implementation-auditor` context via `audit-implementation`, isolated from the author context that produced the work under audit. When this skill loads in the author/main conversation instead, STOP — dispatch the auditor matching the requested verification surface. An already-dispatched matching auditor that loaded this skill proceeds.

</dispatch_gate>

<objective>
A verdict on Python test evidence — APPROVED, or REJECTED with each finding naming the assertion or evidence artifact, the failed spec-tree or Python-specific evidence property, and the evidence gap.
</objective>

<constraints>

This audit is read-only. Produce a verdict over test evidence; never edit tests, production code, specs, fixtures, harnesses, generators, or project configuration.

</constraints>

<audit_workflow>

<prerequisites>

{!% require_skill 'python:python-standards' %!}

{!% require_skill 'python:python-test-standards' %!}

{!% require_skill 'spec-tree:test' %!}

Read `spx/local/python.md` and `spx/local/python-tests.md` when they exist; otherwise apply the loaded skills only. Each overlay routes behavior to the product's governing specs and decisions, supplements the loaded skills, and does not declare product truth.

</prerequisites>

<audit_scope>
Begin with the current governing spec and its current evidence links. A deleted test or test-infrastructure path belongs to this audit only when a current `[test]` assertion still links it or a current linked test still imports it. When the current spec carries no `[test]` link to the deleted path and no current evidence chain references it, classify the retired path as outside current Python test-evidence scope; under implementation-auditor composition, return `NOT_APPLICABLE` for that path. Never demand restoration of deterministic evidence solely because the base revision or changeset deletion names the retired path. When a current `[test]` assertion still links a missing path, report missing evidence against that current assertion.

Use read-only `git diff` only when the caller's changeset scope requires confirming whether an evidence path was deleted. Run no other shell command from this concern skill.

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

<no_deterministic_verification>
This audit runs no deterministic verification — no test collection, lint, type-check, coverage, or naming-convention command. The caller brings the project's tests, linters, and type-checker to passing on the changeset before dispatch, and CI re-runs them over the whole repository. Spend the whole audit on reading the evidence chain; the green deterministic gate is a precondition the caller owns, not a step this audit re-pays.
</no_deterministic_verification>

<test_file_declarations>
Apply the base `/audit-tests` declaration screen before coupling. Any Python assignment, annotated assignment, named expression, loop binding, context-manager binding, exception binding, pattern binding, pytest fixture parameter, or property-generated parameter in an executed test file is a `test_owned_declaration` finding. Local functions are findings when they own setup, reusable cases, fixture handling, generator selection, harness behavior, diagnostics, or source vocabulary. Name the right owner for the value or configuration: production source contract, `product_testing.harnesses.*`, `product_testing.generators.*`, inert fixture data, or eval case data.
</test_file_declarations>

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

Do not recommend `tests/helpers`, `tests/support`, node-local test-infrastructure modules, or fixture body code in `conftest.py`.
</architectural_dry_audit>

</audit_workflow>

<verdict_format>
This skill contributes Python-specific findings to the base `/audit-tests` verdict and inherits its JSON schema. Put coupling, falsifiability, alignment, coverage, source ownership, domain variation, oracle independence, cleanup safety, and pytest discovery safety findings in `gate-1-assertion`. Put repeated setup or test-infrastructure extraction findings from `<architectural_dry_audit>` in `gate-2-architectural`. Append findings to the matching base rows; never replace a row or emit `gate-0-deterministic`.

For each finding, include:

- Verdict property: coupling, falsifiability, alignment, coverage, source ownership, domain variation, oracle independence, cleanup safety, or pytest discovery safety
- Exact file and line
- The imported chain when the defect is outside the test file
- Required fix

Emit `APPROVED` only when all evidence-property checks pass. Emit `REJECTED` when any property fails.
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

Failure 8: Required restoration of retired deterministic evidence.

Claude saw a deleted Python test and harness in the changeset, followed the base revision's former link, and rejected the implementation because the deleted files no longer supplied deterministic evidence. The current governing spec had reclassified the assertions to pathless `[audit]` evidence, so no current `[test]` assertion or evidence chain owned those files. Avoid this by deriving test-audit applicability from current spec links first: return `NOT_APPLICABLE` for a retired deleted path, and report missing evidence only when a current `[test]` assertion still links the missing path.
</failure_modes>

<success_criteria>
The Python test verdict is sound when:

- Every in-scope test was judged on all evidence properties with none skipped — coupling, falsifiability, alignment, coverage (by reading), source ownership, and the Python-specific checks (generators, harnesses, fixtures, `conftest.py`).
- Every deleted test or test-infrastructure path was classified from current spec links and current evidence chains, with retired evidence returned as `NOT_APPLICABLE` and current broken `[test]` links reported as missing evidence.
- The verdict states an overall `APPROVED` / `REJECTED` with no assertion left unevaluated.
- Each finding with inherited severity `REJECT` is falsifiable: it names the assertion or evidence artifact, the failed property, and the evidence — including, where the defect is a missing source contract, the production module that should own the vocabulary. The overall verdict remains `REJECTED`.
- The same test node yields the same verdict regardless of run order (reproducible).

</success_criteria>

<reference_guides>

- `references/python-test-audit-examples.md` — worked Python test-audit analysis cases (an approved audit, a rejection for `@patch` severing runtime coupling, and a rejection for a `TYPE_CHECKING` import disguised as coupling). Use them to inspect evidence; `<verdict_format>` and the inherited `/audit-tests` JSON schema remain the output contract.

</reference_guides>
