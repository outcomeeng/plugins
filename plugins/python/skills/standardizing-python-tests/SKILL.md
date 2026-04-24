---
name: standardizing-python-tests
disable-model-invocation: true
description: >-
  Python testing standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Define Python-specific test standards loaded by `/testing-python`, `/coding-python`, `/architecting-python`, and `/auditing-python-tests`.

Read `/testing` first when deciding what evidence to create. Read `/standardizing-python` before this reference when writing or reviewing Python test code. These standards apply to all Python tests.
</objective>

<core_model>
Every Python test file name encodes three independent axes:

| Axis     | Tokens                                                         | Meaning                                    |
| -------- | -------------------------------------------------------------- | ------------------------------------------ |
| Evidence | `scenario`, `mapping`, `conformance`, `property`, `compliance` | What kind of proof the test provides       |
| Level    | `l1`, `l2`, `l3`                                               | How painful the test is to run             |
| Runner   | optional token such as `playwright`                            | Which non-default runner executes the file |

Evidence, level, and runner are orthogonal:

- A Playwright test can be `l2` or `l3`
- A filesystem test can be `l1` when it uses `tmp_path` or `TemporaryDirectory`
- A `scenario` test can run at any level
- A runner token appears only when the runner is not the default

</core_model>

<file_naming>
Use this canonical Python pattern:

```text
test_<subject>.<evidence>.<level>[.<runner>].py
```

Examples:

| Purpose                               | File                                      |
| ------------------------------------- | ----------------------------------------- |
| Cheap behavior scenario               | `test_config_loader.scenario.l1.py`       |
| Deterministic input-output mapping    | `test_route_parser.mapping.l1.py`         |
| Local browser flow through Playwright | `test_checkout.scenario.l2.playwright.py` |
| Live webhook contract                 | `test_stripe_webhook.conformance.l3.py`   |
| Safety boundary                       | `test_pii_redaction.compliance.l1.py`     |
| Generated invariant                   | `test_slug_roundtrip.property.l1.py`      |

Do not use legacy file suffixes such as `.unit.py`, `.integration.py`, `.e2e.py`, or `.spec.py` as the signal for evidence, level, or runner.
</file_naming>

<level_tooling>
Choose the level from execution pain and dependency availability:

| Level | Infrastructure                                    | Default runner | Typical runtime |
| ----- | ------------------------------------------------- | -------------- | --------------- |
| `l1`  | Python stdlib, temp dirs, repo-required dev tools | pytest         | milliseconds    |
| `l2`  | Docker, browsers, dev servers, project binaries   | pytest         | seconds         |
| `l3`  | Remote services, credentials, shared environments | pytest         | seconds/minutes |

Use a runner token when a non-default runner owns execution:

- `test_browser_menu.scenario.l2.playwright.py` for a local browser flow
- `test_production_login.scenario.l3.playwright.py` for a credentialed remote flow

</level_tooling>

<router_mapping>
After `/testing` chooses the evidence and level, implement it with these Python patterns:

| Router Decision                            | Python implementation                             |
| ------------------------------------------ | ------------------------------------------------- |
| Stage 2 -> `l1`                            | pytest, typed factories, `tmp_path`, pure helpers |
| Stage 2 -> `l2`                            | pytest fixtures with local real dependencies      |
| Stage 2 -> `l3`                            | pytest with explicit credential gating            |
| Stage 3A: pure computation                 | Direct tests of typed pure functions              |
| Stage 3B: extract pure part                | Pure helper at `l1`, boundary at outer level      |
| Stage 5 exception 1: failure simulation    | `Protocol` implementation that raises/errors      |
| Stage 5 exception 2: interaction protocols | Spy class with typed call recording               |
| Stage 5 exception 3: time/concurrency      | Injected clock or controllable scheduler          |
| Stage 5 exception 4: safety                | Class that records intent without side effects    |
| Stage 5 exception 5: combinatorial cost    | Configurable fake with real-shaped behavior       |
| Stage 5 exception 6: observability         | Spy that captures hidden boundary details         |
| Stage 5 exception 7: contract probes       | Stub validated against the contract schema        |

</router_mapping>

<python_style>
All Python tests must follow the same quality baseline as production Python:

- Test functions return `None`
- Fixture parameters and helper functions have type annotations
- Test data uses named constants, factories, builders, or Hypothesis strategies
- Assertions target behavior and include enough detail to diagnose failure
- Imports use the project package layout: `product.*` and `product_testing.*` in examples
- Test files stay co-located with the spec node they prove unless the project has a documented alternative

Prefer `tmp_path` for filesystem tests:

```python
CONFIG_TEXT = "site_dir: ./site\nbase_url: http://localhost:1313\n"


def test_loads_yaml_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(CONFIG_TEXT)

    config = load_config(config_path)

    assert config.site_dir == "./site"
    assert config.base_url == "http://localhost:1313"
```

</python_style>

<dependency_injection>
Tests verify behavior through real code paths. Avoid framework-level replacement of the dependency under test.

Forbidden patterns:

- `unittest.mock.patch` replacing the module that should provide evidence
- `Mock()` or `MagicMock()` replacing behavior that the test claims to verify
- `mocker.patch(...)` replacing the dependency under test

Allowed doubles are explicit objects or classes passed through dependency injection and mapped to a `/testing` Stage 5 exception.

```python
from dataclasses import dataclass, field
from typing import Protocol


class PaymentGateway(Protocol):
    def charge(self, amount_cents: int) -> ChargeResult: ...


@dataclass
class RecordingGateway:
    charges: list[int] = field(default_factory=list)

    def charge(self, amount_cents: int) -> ChargeResult:
        self.charges.append(amount_cents)
        return ChargeResult(id="test-charge", status="approved")
```

For time-dependent behavior, inject a clock:

```python
class Clock(Protocol):
    def now(self) -> datetime: ...


@dataclass(frozen=True)
class FixedClock:
    instant: datetime

    def now(self) -> datetime:
        return self.instant
```

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

```python
@given(valid_config_values())
def test_config_roundtrips(value: ConfigValue) -> None:
    assert parse_config(format_config(value)) == value
```

</property_based_testing>

<test_data_policy>
Use source-owned values when the production system owns them.

- Import routes, selectors, ids, feature flags, registry names, and public constants from the module that owns them
- Keep descriptive test names and assertion diagnostics near the assertion
- Put stable test-only strings, ids, dates, and expected-output snippets in `product_testing.fixtures`
- Put shared harnesses, generated data, and Stage 5 doubles in `product_testing.harnesses`
- Use co-located `helpers.py` only when the helper serves one test directory

</test_data_policy>

<credential_policy>
`l3` tests with credentials must be explicit and safe:

- Load credentials from documented environment variables or project secret helpers
- Skip only when the test is optional for the current command
- Fail loudly when the selected command claims to run required credentialed evidence
- Never silently pass when required credentials are missing

```python
def require_token() -> str:
    token = os.environ.get("STRIPE_TEST_TOKEN")
    if token is None:
        pytest.fail("STRIPE_TEST_TOKEN is required for this l3 contract test")
    return token
```

</credential_policy>

<script_testing>
Checked-in `scripts/` entrypoints get thin tests:

- Argument parsing through the repository's canonical parser
- Dispatch into the imported orchestrator
- Exit-code mapping and observable terminal output

The orchestrator carries the main behavioral evidence. Script files should stay small and route to tested modules.
</script_testing>

<anti_patterns>
Reject or rewrite these patterns:

- Legacy file suffixes: `.unit.py`, `.integration.py`, `.e2e.py`, `.spec.py`
- Runner-level collapse: assuming Playwright means `l3`
- Level-evidence collapse: assuming `scenario` means high-cost execution
- Framework mocks replacing the dependency under test
- Property claims implemented only with examples
- Source-owned values copied into local constants
- Production modules created only to aggregate values for tests
- Deep relative imports into stable shared test infrastructure
- Silent skips for required credentialed evidence

</anti_patterns>

<success_criteria>
Python test guidance follows this standard when:

- `/testing` determines the evidence mode, execution level, and exception path before implementation
- Test filenames use `test_<subject>.<evidence>.<level>[.<runner>].py`
- Doubles are passed through dependency injection and mapped to a Stage 5 exception
- Property assertions use meaningful Hypothesis properties
- Source-owned values come from the owning production module
- Shared test infrastructure lives in test-owned packages or co-located helpers
- Required credentialed evidence fails loudly when selected credentials are absent

</success_criteria>
