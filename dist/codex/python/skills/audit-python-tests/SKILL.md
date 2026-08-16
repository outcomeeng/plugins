---
name: audit-python-tests
description: >-
  Python test-evidence audit methodology — judges the Python tests in scope
  against the spec-tree and Python-specific evidence properties.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Skill
---

<objective>
A verdict on Python test evidence — APPROVED, or REJECTED with each finding naming the assertion or evidence artifact, the failed evidence property, and the evidence.
</objective>

<constraints>

This audit is read-only. Produce a verdict over test evidence; never edit tests, production code, specs, fixtures, harnesses, generators, or project configuration.

</constraints>

<audit_workflow>

<prerequisites>

Invoke the `python:python-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `python:python-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `spec-tree:audit-tests` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `spec-tree:test` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Read `spx/local/python.md` and `spx/local/python-tests.md` when they exist; otherwise apply the loaded skills only. Each overlay routes behavior to the product's governing specs and decisions, supplements the loaded skills, and does not declare product truth.

Invoke `/contextualize` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1.

</prerequisites>

<audit_scope>
Begin with the current governing spec and its current evidence links. A deleted test or test-infrastructure path belongs to this audit only when a current `[test]` assertion still links it or a current linked test still imports it. When the current spec carries no `[test]` link to the deleted path and no current evidence chain references it, classify the retired path as outside current Python test-evidence scope and return `NOT_APPLICABLE` for that path. Never demand restoration of deterministic evidence solely because the base revision or changeset deletion names the retired path. When a current `[test]` assertion still links a missing path, report missing evidence against that current assertion.

Use read-only `git diff` only when the supplied changeset scope requires confirming whether an evidence path was deleted. Run no other shell command from this concern skill.

For every in-scope test assertion, inspect the full evidence chain:

- The spec assertion and selected assertion type
- The executed test file
- Imported production modules
- Imported `<package>_testing.harnesses.*` modules
- Imported `<package>_testing.generators.*` modules
- Inert fixture path providers and fixture data files referenced by the test
- `conftest.py` files that apply to the test

Do not approve a test by looking only at the test file. Laundering and severed coupling can live in generators, harnesses, fixture path providers, and pytest discovery shims.
</audit_scope>

<no_deterministic_verification>
This audit runs no deterministic verification — no test collection, lint, type-check, coverage, or naming-convention command. Spend the whole audit on reading the evidence chain.
</no_deterministic_verification>

<structural_reading>
Before Gate 1, read each in-scope test filename. Canonical Python evidence files match `test_<subject>.<evidence>.<level>[.<runner>].py`, where `<evidence>` is `scenario`, `mapping`, `conformance`, `property`, or `compliance` and `<level>` is `l1`, `l2`, or `l3`. Reject the legacy suffixes `/python-test-standards` names — `.unit.py`, `.integration.py`, `.e2e.py`, `.spec.py` — as a Gate 1 `filename_policy` finding carrying property `alignment` from the base `/audit-tests` enum, since a filename that misdeclares its evidence type or level misaligns the file with the assertion it claims to evidence. The project's validation owns the convention; fold this reading observation into Gate 1 rather than running a naming-convention command.
</structural_reading>

<test_file_declarations>
Apply the base `/audit-tests` semantic binding screen before coupling. Python assignments, annotated assignments, named expressions, loop bindings, context-manager bindings, exception bindings, pattern bindings, pytest fixture parameters, and property-generated parameters are valid when they only receive actual results, source-owned contracts, generated values, harness observations, callback inputs, resource handles, or fixture paths and introduce no data or policy. In particular, accept `tmp_path`, `observations = harness_call(...)`, and assertion-local comprehensions over those observations; none chooses a case, expectation, or policy. Emit a finding carrying property `declarations` and the base `/audit-tests` rule label the choice matches — `test-owned configuration` when a binding chooses runner settings, seed policy, retries, setup policy, or lifecycle policy, and `test-owned data` when it chooses hand-picked data, boundary bags, expected outputs, fixture contents, or generator domains. Keep the two labels distinct; collapsing them loses the difference between a configuration defect and a data defect. Local functions are findings when they own those choices — property `declarations` — or when they move a predicate or assertion call out of the linked test function or callback — property `predicate-ownership`, rule `assertion-seam`, remediation target `test-file`.
</test_file_declarations>

<gate_1_assertion>
Entry point is the spec, not the test file.

Judge every in-scope assertion against each audit below. A `REJECT` finding from any audit rejects the assertion it names and moves to the next assertion. An audit whose subject is an imported artifact rather than an assertion — a generator, a harness, an inert fixture, or a `conftest.py` shim — attributes its finding to every in-scope assertion whose evidence chain reaches that artifact, so each finding carries the `assertion` field the base schema requires. The `<structural_reading>` and `<test_file_declarations>` observations above are folded into this gate rather than reported as a separate deterministic gate.

<coupling_audit>
A `<package>_testing.generators` import is an input-domain provider, audited in `<generator_audit>` rather than classified as coupling here.

Imports inside `if TYPE_CHECKING:` do not create runtime coupling. A test with only framework, stdlib, and type-only imports is a tautology unless it reaches production through a harness that itself reaches production.

When a test imports a harness, inspect the harness and verify it calls the production behavior the assertion is about. A harness that builds expected values without exercising production is severed coupling.

Specialize each category of the coupling taxonomy `/audit-tests` owns to Python imports. Classify from the table below rather than a subset of it; every category the canonical taxonomy names appears here, so a category missing from this table would silently narrow the verdict.

| Category           | Python-specific definition                                                                                                                      | Verdict                                         |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Direct             | Test imports and calls the governed Python module, function, or class                                                                           | Proceed                                         |
| Indirect           | Test imports a `<package>_testing.harnesses` module that calls the governed path                                                                | Proceed after harness tracing                   |
| Transitive         | Test imports a public consumer of the governed module                                                                                           | Proceed if the level matches                    |
| Laundered indirect | Imports a `<package>_testing` module that exists only to expose hardcoded values back to the test                                               | REJECT — laundering                             |
| False              | Test imports the module but never calls the assertion-relevant symbols                                                                          | REJECT                                          |
| Partial            | Test calls the module with the wrong inputs or path, missing the assertion-relevant behavior                                                    | REJECT                                          |
| None               | Test imports only pytest, Hypothesis, stdlib, or type-only symbols, with zero production coupling                                               | REJECT — tautology                              |
| Severed            | Test or harness replaces the governed behavior with `unittest.mock`, `MagicMock`, `mocker.patch`, monkeypatch, or an alternate import           | REJECT — coupling severed                       |
| Prose-coupling     | Reads an authored prose/doc body (skill, spec, prompt) and asserts its content, directly or through a harness constant or infrastructure reader | REJECT — couples to authored text, not behavior |

Framework and stdlib imports such as `pytest`, `hypothesis`, `json`, and `pathlib` do not count as coupling by themselves. The Prose-coupling row is the table-side form of a test reading a `src/` or authored-doc body; both reach the same REJECT.

A severed, false, partial, or absent coupling carries property `coupling` from the base enum.
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

Replacing the behavior under test carries property `falsifiability` from the base enum — a severed seam means no production mutation can break the test.

</falsifiability_audit>

<source_ownership_audit>
The audit asks one question per test case: *where does this case come from?* The legitimate sources:

| Assertion type | Case source                                                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Scenario       | The spec assertion text — the case is declared by the spec, not invented by the test author                                                                              |
| Mapping        | A finite source-owned enumeration (enum, registry, schema, structured metadata)                                                                                          |
| Property       | A generator over a domain — the author writes the invariant, the generator owns the cases                                                                                |
| Conformance    | An external oracle (schema validator, reference implementation, parser the test doesn't author)                                                                          |
| Compliance     | The decision record being enforced — the case is the rule itself                                                                                                         |
| Any (fixture)  | An inert fixture file under `<package>_testing/fixtures/`, passed to the code under test as a file path or byte stream — the file's whole real-world payload is the case |

The first five rows pair an assertion type with the case source it normally takes. The Fixture row is cross-cutting: any assertion type may use an inert fixture file as the case. An auditor classifying a test case checks both the assertion type and whether the case is a whole-payload fixture file.

A case that does not have a documentable source outside the author's head is a tautology dressed as a measurement — the test confirms the author's understanding forever, never the spec. The defect is in the case's *origin*. Lexical location (`Final` at module scope, plain assignment, inline literal), syntactic form, and reuse pattern (shared bag, single-value, parametrize row) are irrelevant — the audit names them only as forms the same defect takes.

**Vocabulary check (where the values live).** Independently of case provenance, the *values* used in cases must come from the right home:

| Value kind                                                   | Lives in                                                                        |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| Production vocabulary (labels, paths, schema fields, tokens) | Owning production module, imported                                              |
| Variable input domain                                        | Generator under `<package>_testing/generators/`                                 |
| Resource-bound or runner-tuning value (timeouts, retries)    | The harness module that owns the resource, under `<package>_testing/harnesses/` |
| Whole-payload real-world sample                              | Inert fixture file under `<package>_testing/fixtures/`, read by path            |
| One-off descriptive text (test titles, diagnostic messages)  | Inline in the test function body                                                |

For each test case, name the source. REJECT against the missing source when:

- The case's value is production vocabulary the test re-declares instead of imports.
- The case's value is a container key or f-string template key hand-written by the author — keys are vocabulary; the key belongs to the owning production module.
- The case's value is a hand-copied YAML/HCL/bash/JSON schema field name — artifacts are downstream; the Python module that renders or consumes the artifact owns the vocabulary, and that module must be created if it does not yet exist.
- The case's value is a runner-tuning literal at test scope — the harness that owns the resource owns the timeout, retry count, or polling interval.
- The case's input or expected output is hand-picked by the author with no source the audit can name — REJECT, the case is a tautology regardless of where it sits lexically.

When the missing source is an architectural defect (the Python module that should own the vocabulary does not yet exist), name the module that should be created and the spec-tree node that should govern it.

A case or value copied from the module under test carries property `source-ownership`, rule `source-ownership`, remediation target `source-contract`; an expected output computed by the same production path that produces the actual output carries property `oracle-independence`, remediation target `independent-oracle`. These are the two base-enum properties this audit judges.

Pass only when every case is traceable to a source independent of the author and every value lives in its proper home.
</source_ownership_audit>

<generator_audit>
Audit every imported generator:

- It represents a variable input domain with meaningful variation, composition, or shrinkage
- It does not duplicate source-owned vocabulary
- It does not hide arbitrary example values behind a strategy name
- It derives expected outputs from generated inputs, an independent oracle, or a source outside the module under test

Property evidence requires a meaningful property. `@given` that only checks for lack of exceptions is insufficient.

A strategy that collapses to a single example or checks only for the absence of exceptions carries property `falsifiability`; a generator that duplicates source-owned vocabulary carries property `source-ownership`, rule `source-ownership`, remediation target `source-contract`; an expected output derived from the module under test carries property `oracle-independence`, remediation target `independent-oracle`.
</generator_audit>

<harness_audit>
Audit every imported harness:

- It manages setup, teardown, cleanup, dependency checks, or access to external behavior
- It reaches the production behavior the assertion is about
- It does not replace the behavior under test with framework mocks, monkeypatches, environment stubs, network fakes, or alternate imports
- It cleans up temp dirs, subprocesses, services, Docker resources, browsers, databases, and environment changes
- It does not own arbitrary test data that belongs in source modules or generators

A harness that severs the asserted behavior — replacing it or failing to reach production — carries property `coupling`; a harness that owns setup policy, resource-tuning values, or arbitrary test data carries property `declarations`.

Pytest fixture callables that perform setup, teardown, cleanup, or dependency access are harness entrypoints. They belong under `<package>_testing.harnesses.*`.
</harness_audit>

<fixture_audit>
Audit inert fixture files and fixture path providers:

- Fixture files are real-world payloads whose complete shape matters to the assertion
- Tests consume fixture files by path, reading, or copying
- Tests do not import fixture files as Python modules
- Fixture files do not store isolated strings or numbers as test data

Reject Python modules under `<package>_testing/fixtures/` that export pytest fixture body functions. That category is for inert data files under the PDR vocabulary.
</fixture_audit>

<conftest_audit>
Inspect every `conftest.py` that applies to the test path.

Allowed content:

- Explicit imports of pytest fixture callables from `<package>_testing.harnesses.*`
- Pytest marker registration
- Pytest hooks that configure collection or reporting

Rejected content:

- Fixture body code
- Harness classes or setup policy
- Generated data
- Source-owned protocol values
- Star imports from test infrastructure packages
- Mocking, monkeypatching, or import-path mutation

A rejected `conftest.py` discovery defect carries property `evidence-chain-completeness` from the base enum — the shim breaks the chain from the assertion to the imported infrastructure.

</conftest_audit>

Gate 1 status:

- PASS if no Gate 1 finding carries severity `REJECT`.
- FAIL if any Gate 1 finding carries severity `REJECT`.

</gate_1_assertion>

<gate_2_architectural>
Runs only if Gate 1 is PASS.

<architectural_dry_audit>
When two or more in-scope tests repeat setup or infrastructure logic, reject the duplication and identify the canonical destination:

| Repeated pattern                                      | Destination                           |
| ----------------------------------------------------- | ------------------------------------- |
| Temp product scaffolding                              | `<package>_testing.harnesses.*`       |
| Subprocess or CLI execution setup                     | `<package>_testing.harnesses.*`       |
| Database, Docker, browser, service, or API setup      | `<package>_testing.harnesses.*`       |
| Domain-shaped input construction with variable values | `<package>_testing.generators.*`      |
| Real-world payload samples                            | `<package>_testing/fixtures/` as data |

Do not recommend `tests/helpers`, `tests/support`, node-local test-infrastructure modules, or fixture body code in `conftest.py`.
</architectural_dry_audit>

Gate 2 status:

- PASS if no repeated setup or infrastructure pattern appears in two or more in-scope tests.
- FAIL if any repeated setup or infrastructure pattern appears in two or more in-scope tests.

</gate_2_architectural>

</audit_workflow>

<verdict_format>
This skill composes the base `/audit-tests` verdict: the row names (`gate-1-assertion`, `gate-2-architectural`), the JSON schema, and the closed `property` enum are defined in its `<verdict_format>` and are not redefined here. This skill contributes Python-specific finding detail into those rows. Put evidence-property findings in `gate-1-assertion` and repeated setup or test-infrastructure extraction findings from `<architectural_dry_audit>` in `gate-2-architectural`. Append findings to the matching base rows; never replace a row or emit `gate-0-deterministic`.

Every finding carries a `property` drawn from the base `/audit-tests` enum, attributed inline at the audit above that raised it — this skill never re-enumerates the enum or remaps its members here. A Python concern with no home in the base enum is a signal to extend that enum in `/audit-tests`, never to invent a value here.

Each finding carries the base nine-field record. These Python-specific details accompany that record rather than replacing any of its fields:

- Exact file and line
- The imported chain when the defect is outside the test file
- Required fix

Emit `APPROVED` only when all evidence-property checks pass. Emit `REJECTED` when any property fails.

When `<audit_scope>` finds that a retired path has no current `[test]` assertion or current evidence-chain owner, emit this alternate concern result instead of the inherited rows:

```json
{
  "status": "NOT_APPLICABLE",
  "subjects": ["<retired-repository-relative-path>"],
  "explanation": "No current [test] assertion or evidence chain references the retired path."
}
```

Emit this shape only when every supplied subject is outside current Python test-evidence scope. A current broken `[test]` link remains applicable and produces the inherited `REJECTED` verdict.
</verdict_format>

<failure_modes>
Failure 1: Accepted `TYPE_CHECKING` import as coupling.

What happened: Claude saw `from product.theme import ThemeColor` inside an `if TYPE_CHECKING:` block and counted it as runtime coupling. The test declared its own color values and never executed production code.

Why it failed: Type-only imports disappear at runtime and cannot couple executed evidence to production behavior.

How to avoid: Ignore type-only imports for coupling.

Failure 2: Missed coupling severed by `@patch`.

What happened: Claude saw a production import and approved the test, while `@patch("product.database.query")` replaced the imported behavior.

Why it failed: The patch severed the runtime path the import appeared to exercise.

How to avoid: Check decorators, fixtures, monkeypatch usage, and harness setup code.

Failure 3: Accepted a generator that only hid a constant.

What happened: Claude saw a Hypothesis strategy and treated it as property evidence. The strategy returned one copied source value through `st.just(...)`.

Why it failed: Framework syntax wrapped one example without creating a variable property domain.

How to avoid: Inspect generator bodies and require meaningful variation.

Failure 4: Accepted pytest fixture body code in `conftest.py`.

What happened: Claude treated pytest discovery as a reason to put setup logic in `conftest.py`.

Why it failed: Discovery wiring became the owner of harness behavior, hiding setup and lifecycle policy outside the canonical test-infrastructure home.

How to avoid: Check every applicable `conftest.py`; require harness logic to live in the product's test-infrastructure implementation home.

Failure 5: Accepted a hand-picked test case as evidence.

What happened: Claude saw `parse("name=alice")` followed by `assert result.name == "alice"` and approved the test. The author invented the string to show their understanding of the parser.

Why it failed: The same mental model produced the case and the implementation, so every run confirmed self-consistency rather than the spec assertion.

How to avoid: Ask where every case comes from: a generator, an oracle, a fixture, source-owned vocabulary, or the spec assertion text itself. If the author chose it because it seemed reasonable, REJECT.

Failure 6: Container-literal keys treated as opaque scaffolding.

What happened: Claude saw `INVENTORY_JSON = f'{{"flatcar-version":"{VERSION}",...}}'` and classified it as test-fixture scaffolding because the *values* were synthetic. The author hand-wrote production-owned label vocabulary into the keys.

Why it failed: Container keys are protocol vocabulary; synthetic values do not make copied keys source-owned.

How to avoid: Audit keys and values separately; require `json.dumps({LABEL: synthetic_value, ...})` with `LABEL` imported from its owner.

Failure 7: "Artifact is the source-of-truth" rationalization.

What happened: Claude accepted a hand-copied YAML field name, HCL attribute, or systemd unit path because the value appeared in a parsed artifact and no Python module owned it.

Why it failed: Artifacts are downstream of Python; a missing renderer or consumer module is an architecture defect rather than permission to copy vocabulary into evidence.

How to avoid: Name the missing source-of-truth module and the spec-tree node that should govern it; REJECT against the missing module.

Failure 8: Required restoration of retired deterministic evidence.

What happened: Claude followed a base revision's former link to a deleted Python test and harness and rejected the implementation because the deleted files no longer supplied deterministic evidence. The current spec had reclassified the assertions to pathless `[audit]` evidence.

Why it failed: Historical evidence ownership overrode the current governing declaration.

How to avoid: Derive applicability from current spec links first; return `NOT_APPLICABLE` for a retired deleted path, and report missing evidence only when a current `[test]` assertion still links it.
</failure_modes>

<success_criteria>
The Python test verdict is sound when:

- Every in-scope test was judged on all evidence properties this skill owns with none skipped — coupling, falsifiability, alignment, source ownership, and the Python-specific checks (generators, harnesses, fixtures, `conftest.py`); coverage is judged by the base `/audit-tests` step that owns it and is never claimed here. Gate 2 was judged when Gate 1 passed and omitted only when Gate 1 rejected the evidence.
- Every deleted test or test-infrastructure path was classified from current spec links and current evidence chains, with retired evidence returned as `NOT_APPLICABLE` and current broken `[test]` links reported as missing evidence.
- Applicable scope states an overall `APPROVED` / `REJECTED` with no assertion left unevaluated; a composition-only retired-path scope emits the defined `NOT_APPLICABLE` result.
- Each finding with inherited severity `REJECT` is falsifiable: it names the assertion or evidence artifact, the failed property, the gate that raised it, and the evidence — including, where the defect is a missing source contract, the production module that should own the vocabulary. The overall verdict remains `REJECTED`.
- The same test node yields the same verdict regardless of run order (reproducible).

</success_criteria>

<reference_guides>

- `${SKILL_DIR}/references/python-test-audit-examples.md` — worked Python test-audit analysis cases (an approved audit, a rejection for `@patch` severing runtime coupling, and a rejection for a `TYPE_CHECKING` import disguised as coupling). Use them to inspect evidence; `<verdict_format>` and the inherited `/audit-tests` JSON schema remain the output contract.

</reference_guides>
