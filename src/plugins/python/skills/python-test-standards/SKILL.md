---
name: python-test-standards
user-invocable: false
description: >-
  Python testing standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The Python-specific test standards every Python skill enforces.
</objective>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/python-tests.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<core_model>
Every Python test file name encodes three independent axes:

| Axis     | Tokens                                                         | Meaning                                    |
| -------- | -------------------------------------------------------------- | ------------------------------------------ |
| Evidence | `scenario`, `mapping`, `conformance`, `property`, `compliance` | What kind of evidence the test provides    |
| Level    | `l1`, `l2`, `l3`                                               | How painful the test is to run             |
| Runner   | optional token such as `playwright`                            | Which non-default runner executes the file |

Canonical filename:

```text
test_<subject>.<evidence>.<level>[.<runner>].py
```

Do not use `.unit.py`, `.integration.py`, `.e2e.py`, or `.spec.py` as the signal for evidence, level, or runner.
</core_model>

<execution_levels>
Choose the level from execution pain and dependency availability:

| Level | Infrastructure                                    | Default runner | Typical runtime |
| ----- | ------------------------------------------------- | -------------- | --------------- |
| `l1`  | Python stdlib, temp dirs, repository dev tools    | pytest         | milliseconds    |
| `l2`  | Docker, browsers, dev servers, product binaries   | pytest         | seconds         |
| `l3`  | Remote services, credentials, shared environments | pytest         | seconds/minutes |

Use a runner token when a non-default runner owns execution. Browser execution can be `l2` or `l3`; the runner does not decide the level.
</execution_levels>

<source_first_testability>
The first move when testing existing Python code is to improve the code under test until it has a source contract that can be tested cleanly.

MUST refactor source before writing or accepting a weak test when the only available test path requires copied source literals, arbitrary example bags, `Mock`/`MagicMock` replacement, `mocker.patch`, monkeypatching the behavior under test, `sys.path` tricks, or fixture-file laundering.

Source modules own domain protocol values through enums, schemas, dataclasses, registries, constructors, typed factories, or public constants that are meaningful to production consumers. Tests import those source-owned contracts.

Scripts and command entrypoints stay thin. Tests verify argument parsing and dispatch at the boundary while deeper behavior is tested through imported modules.
</source_first_testability>

<test_data_policy>
Every test case — input and expected output — derives from a source independent of the test author's invention. The legitimate sources:

| Assertion type | Case source                                                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Scenario       | The spec assertion text — the case is declared by the spec, not invented by the test author                                                                              |
| Mapping        | A finite source-owned enumeration (enum, registry, schema, structured metadata)                                                                                          |
| Property       | A generator over a domain — the author writes the invariant, the generator owns the cases                                                                                |
| Conformance    | An external oracle (schema validator, reference implementation, parser the test doesn't author)                                                                          |
| Compliance     | The decision record being enforced — the case is the rule itself                                                                                                         |
| Any (fixture)  | An inert fixture file under `<package>_testing/fixtures/`, passed to the code under test as a file path or byte stream — the file's whole real-world payload is the case |

The first five rows pair an assertion type with the case source it normally takes. The Fixture row is cross-cutting: any assertion type may use an inert fixture file as the case when the assertion is about the code's behavior on a whole real-world payload that the test author did not invent.

A case the author hand-picked because it "looked reasonable" is a tautology dressed as a measurement. The author wrote or read the implementation, so the invention encodes the same model the code embodies, and every future run confirms that shared model rather than the spec. The defect is in the case's *origin*; lexical location (`Final` at module scope, plain assignment, inline literal), syntactic form, and reuse pattern (shared bag, single-value, parametrize row) are irrelevant.

Where the *values* the cases use live:

| Value kind                                                   | Lives in                                                                        |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| Production vocabulary (labels, paths, schema fields, tokens) | The owning production module, imported                                          |
| Variable input domain                                        | A generator under `<package>_testing/generators/`                               |
| Resource-bound or runner-tuning value (timeouts, retries)    | The harness module that owns the resource, under `<package>_testing/harnesses/` |
| Whole-payload real-world sample                              | An inert fixture file under `<package>_testing/fixtures/`, read by path         |
| One-off descriptive text (test titles, diagnostic messages)  | Inline in the test function body                                                |

Executed Python test files are typed assertion files. They introduce no variable or constant declarations, domain or assertion literals, numbers, vocabulary, case data, expected results, configuration, pytest fixture parameters, or property-generated parameters. One-off descriptive test titles and diagnostic messages remain inline. Import source contracts, generators, harness entrypoints, fixture-path providers, and justified eval case data directly into the assertion expression.

<executed_test_binding_pattern>
Executed tests use zero-parameter wrappers. Resource and generated-case binding occurs inside imported harness entrypoints:

```python
# <package>_testing/harnesses/properties.py
from hypothesis import given, settings

from <package>_testing.generators.identifiers import valid_identifiers


@settings(print_blob=True)
@given(valid_identifiers())
def assert_identifier_roundtrips(identifier: str) -> None:
    assert decode(encode(identifier)) == identifier
```

```python
# spx/.../tests/test_identifiers.property.l1.py
from <package>_testing.harnesses.properties import assert_identifier_roundtrips


def test_identifier_roundtrips() -> None:
    assert_identifier_roundtrips()
```

The same shape governs resource setup: a zero-parameter test calls a harness entrypoint that opens its context manager, performs the assertion-relevant operation, asserts the observable, and cleans up. Executed evidence never receives a pytest fixture parameter. Audit traces through the imported harness to the production path, generator, oracle, and cleanup boundary.

</executed_test_binding_pattern>

**Container keys are vocabulary.** In dict literals, JSON-encoded strings, set or tuple members, and f-string templates, the *keys* and *members* are vocabulary — a hand-written key is a hand-picked case for the parser or consumer. Construct containers via `{LABEL: synthetic_value, ...}` with `LABEL` imported from the owning production module, then serialize with `json.dumps` if a string is needed.

**Artifacts are downstream of Python.** A YAML, HCL, bash, JSON schema, or IaC template file is not a legitimate source-of-truth. A Python module either renders the artifact or consumes it; that module owns the artifact's vocabulary. A test that hand-copies an artifact field name has invented the case — the production-owning module is the source, even if it has to be created first.

**Missing source-of-truth modules.** When no Python module owns a needed value today, the missing module is the architectural defect, not the test. Create the source-of-truth module first; the test imports from it.

Allowed source-owned value:

```python
from product.audit import VERDICT_STATUSES
```

Rejected local stand-in:

```python
VERDICT_STATUSES = ("fail", "skipped", "pass")
```

Allowed harness-owned tuning:

```python
from <package>_testing.harnesses.subprocess import DEFAULT_TIMEOUT_MS
```

Rejected tuning at test scope (the subprocess harness owns the resource and the timeout):

```python
TIMEOUT_SECONDS = 10
```

Rejected JSON template with hand-written keys (`verdict-status` is invented vocabulary):

```python
payload = f'{{"verdict-status": "{status}"}}'
```

Allowed JSON construction with imported keys:

```python
from product.audit import VERDICT_STATUS_FIELD

assert parse_payload(json.dumps({VERDICT_STATUS_FIELD: status})).status == status
```

</test_data_policy>

<generators>
Use generators for input domains that vary per run or across generated cases. Generators MUST vary, compose, shrink, or explore more than one meaningful value.

Use Hypothesis strategies for property evidence:

```python
from hypothesis import strategies as st


def valid_gate_names() -> st.SearchStrategy[str]:
    return st.text(min_size=1).filter(str.isidentifier)
```

Use source-owned registries inside generators only when the generated domain is meaningfully variable:

```python
from hypothesis import strategies as st

from product.audit import VERDICT_STATUSES


def verdict_statuses() -> st.SearchStrategy[str]:
    return st.sampled_from(VERDICT_STATUSES)
```

NEVER wrap a source-owned singleton with `st.just(...)`, singleton `st.sampled_from(...)`, or a constant-returning function and call it a generator. Import the source-owned singleton directly.
</generators>

<harnesses>
Use harnesses for tests that interact with filesystems, subprocesses, APIs, Docker, Playwright, databases, local services, or pytest discovery entrypoints. A harness manages setup, teardown, cleanup, dependency checks, and access to behavior.

Python harnesses live under `<package>_testing/harnesses/`:

```python
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


@contextmanager
def with_test_env(config: Config) -> Iterator[SpecTreeEnv]:
    with TemporaryDirectory() as tmp:
        env = SpecTreeEnv(root=Path(tmp), config=config)
        env.initialize()
        yield env
```

Do not expose setup, teardown, cleanup, or dependency access as pytest fixture parameters in evidence files. Put that lifecycle in zero-parameter harness entrypoints and call them through `<executed_test_binding_pattern>`.

`conftest.py` may register pytest markers and hooks. It MUST NOT contain or import fixture callables, fixture body code, harness classes, generated data, source vocabulary, or hidden setup policy.
</harnesses>

<fixtures>
Fixture files are inert data payloads. Use them for real-world inputs the code under test would encounter, such as captured JSONL, saved API responses, markdown documents, malformed source files, binary samples, or parser corpora.

Executed tests access fixture files only by path, by reading files, or by copying files into temp products. Executed tests never import fixture files as modules and never consume fixture exports.

Strings and numbers are never valid fixture files by themselves. A string literal representing a domain value belongs in the production module or a variable generator.
</fixtures>

<dependency_injection>
Tests verify behavior through real code paths. Avoid framework-level replacement of the dependency under test.

Forbidden replacement patterns:

- `unittest.mock.patch` replacing the module that should provide evidence
- `Mock()` or `MagicMock()` replacing behavior that the test claims to verify
- `mocker.patch(...)` replacing the dependency under test
- `monkeypatch` replacing the behavior under test

Allowed doubles are explicit objects or classes passed through dependency injection and mapped to a `/test` Stage 5 exception.
</dependency_injection>

<property_based_testing>
Property assertions about parsers, serializers, mathematical operations, or invariant-preserving algorithms require Hypothesis and a meaningful property.

| Code type               | Required property        | Pattern                     |
| ----------------------- | ------------------------ | --------------------------- |
| Parsers                 | `parse(format(x)) == x`  | harness-owned `@given(...)` |
| Serialization           | `decode(encode(x)) == x` | harness-owned `@given(...)` |
| Mathematical operations | algebraic laws           | harness-owned `@given(...)` |
| Complex algorithms      | invariant preservation   | harness-owned `@given(...)` |

`@given` that only checks "does not throw" is insufficient. The property must fail when the requirement is broken.

Property tests MUST run through `<executed_test_binding_pattern>`. The harness owns the Hypothesis decorator, generated parameter, invariant assertion, profile, seed policy, run count, deadline, and replay diagnostics. The zero-parameter test imports and calls that harness entrypoint. On failure, the harness output must include the seed or Hypothesis replay directive needed to reproduce the generated case.
</property_based_testing>

<boundary_validation>
An assertion that a field, parser, or constructor rejects values outside a predicate routes by the shape of the invalid set, not by a hand-picked bag of bad inputs.

- Open or infinite invalid space — arbitrary strings, identifiers, timestamps, keys, generated names — is a `property` claim. The evidence is a Hypothesis strategy generating values outside the valid predicate (for example `st.text().filter(lambda s: not s.isidentifier())`), asserting rejection across the generated domain.
- Closed, source-owned invalid set — enum variants, a defined protocol set, registry members — is a `mapping` claim. The evidence parameterizes over every source-owned invalid member, imported from the owning module, never hand-copied.

A `property`-floor rejection rule is not satisfied by a finite parametrize over a hand-picked subset of an open space. Mode selection is `/test`'s authority (see the boundary-validation router in `/test`'s methodology); this standard teaches only the Python expression of that router's output.
</boundary_validation>

<specified_node_verification>
A specified node is the one narrow exception to an all-green Python type gate. Apply it only in Write mode after source-contract inspection establishes that the owning production module does not exist yet.

- The focused test MUST fail only because that declared production module or its owned symbol cannot be imported. Collection, syntax, harness, configuration, discovery, and unrelated import failures remain failures.
- Ruff or the repository's canonical lint command MUST exit zero over the changed scope.
- Mypy or the repository's canonical type command may exit nonzero only when every diagnostic is the direct consequence of that same missing production module or owned symbol. Any unrelated type diagnostic fails the gate.
- Record the exact missing owner and diagnostics, and add the node path relative to `spx/` to `spx/EXCLUDE`.
- Treat this as an authoring-only RED checkpoint. Report the test-evidence audit as deferred; never dispatch an auditor over an absent production owner and never interpret the checkpoint as evidence approval.
- Once implementation begins, remove the exclusion. After implementation exists, the exception ends, the normal passing test, lint, and type gates apply, and test evidence must pass its audit against the complete production chain.

</specified_node_verification>

<anti_patterns>
Reject or rewrite these patterns:

- Legacy file suffixes: `.unit.py`, `.integration.py`, `.e2e.py`, `.spec.py`
- Runner-level collapse: assuming Playwright means `l3`
- Level-evidence collapse: assuming `scenario` means high-cost execution
- Framework mocks replacing the dependency under test
- Property claims implemented only with examples
- Hand-picked test cases — the author chose the input because it "seemed reasonable to exercise the code"; every future run confirms the author's understanding rather than the spec assertion
- `INVALID_*_INPUTS` / `INVALID_*_CASES` tuples, or any module- or class-scope bag of invalid values — a hand-picked set standing in for the invalid domain. Remedy by domain: an open or infinite invalid space (arbitrary strings, identifiers, timestamps, keys, generated names) takes a Hypothesis strategy generating values *outside* the valid predicate; a closed, source-owned invalid set (enum variants, a defined protocol set, registry members) imports the source enum or registry rather than hand-copying members
- Source-owned values copied into local constants
- Test-file-local constants for values the production module owns
- Variable or constant declarations in executed test files, including aliases of imported values
- Pytest fixture parameters or property-generated parameters in executed test files; the harness owns fixture access and generated-case binding
- Hand-written keys in container literals (dict keys, JSON object keys, set or tuple members, f-string templates) — keys are vocabulary, and a hand-written key is an invented case for the parser or consumer
- Hand-copied artifact field names from YAML, HCL, bash, JSON schema, or IaC templates as substitutes for imports from the Python module that should render or consume the artifact
- Test-runner tuning values (timeouts, retries, polling intervals) declared at test scope when the harness that owns the resource should own the value
- Hypothesis settings, seeds, run counts, deadlines, or replay policy declared in a test file instead of the property-test harness
- Production modules created only to aggregate values for tests
- Co-located test-infrastructure modules under `tests/`, `tests/helpers/`, `tests/support/`, or node-local support modules
- Fixture body code in `conftest.py`
- Pytest fixture body code under `<package>_testing/fixtures/`
- Importing inert fixture files as Python modules
- Silent skips for required credentialed evidence

Do not require `spx validation literal` for Python tests. The literal validator is TypeScript-only. Enforce source-owned values through review and Python test standards.
</anti_patterns>

<success_criteria>
Python test guidance follows this standard when:

- `/test` determines the assertion type, execution level, and exception path before implementation
- Test filenames use `test_<subject>.<evidence>.<level>[.<runner>].py`
- Executed test files introduce no variable or constant declarations, local data, or policy; fixture parameters and property-generated parameters remain outside the assertion file
- Source architecture is improved before tests accept copied values, replacement mocks, or fixture laundering
- Every test case has a documentable source outside the author's head — spec assertion text, source-owned enumeration, generator over a domain, external oracle, decision record, or inert fixture file
- Source-owned values come from the owning production module; container keys are imported, not hand-written; runner-tuning values live on the harness that owns the resource
- Generators vary, compose, shrink, or explore meaningful alternatives
- Property tests route through a harness or wrapper that reports the seed or replay directive on failure
- Harnesses live under `<package>_testing/harnesses/` and manage resource lifecycles
- Inert fixture files live under `<package>_testing/fixtures/` and are consumed only as files
- `conftest.py` is limited to marker and hook registration; evidence files use zero-parameter harness entrypoints instead of fixture parameters
- Property assertions use meaningful Hypothesis properties
- Required credentialed evidence fails loudly when selected credentials are absent
- Specified-node verification accepts only the declared missing-owner import or type diagnostics while lint remains green, records audit deferral, and ends before the real post-implementation evidence audit

</success_criteria>
