---
name: standardizing-python-tests
disable-model-invocation: true
description: >-
  Python testing standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Define Python-specific test standards loaded by `/testing-python`, `/coding-python`, `/architecting-python`, and `/auditing-python-tests`.

Read `/testing` first when deciding what evidence to create. Read `/standardizing-python` before this reference when writing or reviewing Python test code. These standards implement `spx/15-test-infrastructure.pdr.md` and `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/python-tests.md`.
</objective>

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
Every value in a test has exactly one valid origin:

| Origin             | What it means                                                 | Where it lives                            |
| ------------------ | ------------------------------------------------------------- | ----------------------------------------- |
| Source-owned       | Production source defines and exports the value               | Owning source module                      |
| Generator-produced | Pure code emits a variable input domain                       | `product_testing/generators/`             |
| Harness-managed    | Infrastructure mediates interaction with an external resource | `product_testing/harnesses/`              |
| Inert fixture file | Real-world payload read or passed as a whole                  | `product_testing/fixtures/` as data files |
| Descriptive inline | Human-readable test title or diagnostic text                  | Inline in the test file                   |

There are no valid test-owned constants for source vocabulary or hand-picked domain data. A named constant in a test file that duplicates a value the production module owns means the production module needs a better exported contract.

Allowed source-owned singleton example:

```python
from product.audit import VERDICT_STATUSES
```

Rejected local stand-in:

```python
VERDICT_STATUSES = ("fail", "skipped", "pass")
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

Python harnesses live under `product_testing/harnesses/`:

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

Pytest fixture callables that perform setup, teardown, cleanup, or dependency access are harness entrypoints. Place their body code under `product_testing/harnesses/`; import them explicitly from `conftest.py` only for pytest discovery.

```python
# conftest.py
from product_testing.harnesses.database import database_session
from product_testing.harnesses.filesystem import temp_product
```

`conftest.py` may register pytest markers, hooks, and explicit fixture imports. It MUST NOT contain fixture body code, harness classes, generated data, source vocabulary, or hidden setup policy.
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

Allowed doubles are explicit objects or classes passed through dependency injection and mapped to a `/testing` Stage 5 exception.
</dependency_injection>

<property_based_testing>
Property assertions about parsers, serializers, mathematical operations, or invariant-preserving algorithms require Hypothesis and a meaningful property.

| Code type               | Required property        | Pattern       |
| ----------------------- | ------------------------ | ------------- |
| Parsers                 | `parse(format(x)) == x`  | `@given(...)` |
| Serialization           | `decode(encode(x)) == x` | `@given(...)` |
| Mathematical operations | algebraic laws           | `@given(...)` |
| Complex algorithms      | invariant preservation   | `@given(...)` |

`@given` that only checks "does not throw" is insufficient. The property must fail when the requirement is broken.
</property_based_testing>

<anti_patterns>
Reject or rewrite these patterns:

- Legacy file suffixes: `.unit.py`, `.integration.py`, `.e2e.py`, `.spec.py`
- Runner-level collapse: assuming Playwright means `l3`
- Level-evidence collapse: assuming `scenario` means high-cost execution
- Framework mocks replacing the dependency under test
- Property claims implemented only with examples
- Source-owned values copied into local constants
- Test-file-local constants for values the production module owns
- Production modules created only to aggregate values for tests
- Co-located helpers under `tests/`, `tests/helpers/`, `tests/support/`, or node-local support modules
- Fixture body code in `conftest.py`
- Pytest fixture body code under `product_testing/fixtures/`
- Importing inert fixture files as Python modules
- Silent skips for required credentialed evidence

Do not require `spx validation literal` for Python tests. The literal validator is TypeScript-only. Enforce source-owned values through review and Python test standards.
</anti_patterns>

<success_criteria>
Python test guidance follows this standard when:

- `/testing` determines the evidence mode, execution level, and exception path before implementation
- Test filenames use `test_<subject>.<evidence>.<level>[.<runner>].py`
- Source architecture is improved before tests accept copied values, replacement mocks, or fixture laundering
- Source-owned values come from the owning production module
- Generators vary, compose, shrink, or explore meaningful alternatives
- Harnesses live under `product_testing/harnesses/` and manage resource lifecycles
- Inert fixture files live under `product_testing/fixtures/` and are consumed only as files
- `conftest.py` is limited to pytest discovery, registration, and explicit imports from canonical harness modules
- Property assertions use meaningful Hypothesis properties
- Required credentialed evidence fails loudly when selected credentials are absent

</success_criteria>
