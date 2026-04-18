---
name: standardizing-python-testing
disable-model-invocation: true
description: >-
  Python testing standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Define Python testing standards and patterns that other skills reference. Not invoked directly—invoke `/testing-python` (to write tests) or `/auditing-python-tests` (to audit tests) instead. These standards apply to ALL Python test code.
</objective>

<quick_start>
Reference this skill for:

- **Level routing** - How `/testing` decisions map to Python implementations
- **Level tooling** - Infrastructure requirements per level
- **Level patterns** - Concrete patterns for Level 1, 2, 3 tests
- **Exception implementations** - The 7 exception cases from `/testing` in Python
- **Property-based testing** - MANDATORY for parsers, serializers, math, algorithms
- **Data factories** - NO magic values, use factories with constants
- **File naming** - `.unit.py`, `.integration.py`, `.e2e.py` (level indicated by filename, no markers needed)
- **DI patterns** - Protocols and dataclass dependencies
- **Harness patterns** - Docker, subprocess, binary harnesses
- **Test signatures** - `-> None`, type annotations
- **Credential management** - Fail loudly, not skip silently
- **Anti-patterns** - What to avoid

</quick_start>

<router_to_python_mapping>
After running through `/testing` router, use this mapping:

| Router Decision                                 | Python Implementation                          |
| ----------------------------------------------- | ---------------------------------------------- |
| **Stage 2 → Level 1**                           | pytest + temp dirs + dataclasses for DI        |
| **Stage 2 → Level 2**                           | pytest fixtures + Docker/subprocess harnesses  |
| **Stage 2 → Level 3**                           | pytest + skip decorators + credential loading  |
| **Stage 3A** (Pure computation)                 | Pure functions, test directly                  |
| **Stage 3B** (Extract pure part)                | Factor into pure functions + thin wrappers     |
| **Stage 5 Exception 1** (Failure modes)         | Protocol + stub returning errors               |
| **Stage 5 Exception 2** (Interaction protocols) | Spy class recording calls                      |
| **Stage 5 Exception 3** (Time/concurrency)      | `patch("time.time")`, `patch("random.random")` |
| **Stage 5 Exception 4** (Safety)                | Stub that records but doesn't execute          |
| **Stage 5 Exception 6** (Observability)         | Spy class capturing request details            |

</router_to_python_mapping>

<level_tooling>

| Level          | Infrastructure                                   | Speed  |
| -------------- | ------------------------------------------------ | ------ |
| 1: Unit        | Python stdlib + temp dirs + standard dev tools   | <100ms |
| 2: Integration | Docker containers + project-specific binaries    | <1s    |
| 3: E2E         | Network services + external APIs + test accounts | <10s   |

**Standard dev tools** (Level 1): git, cat, grep, curl—available in CI without setup.
**Project-specific tools** (Level 2): Docker, PostgreSQL, Hugo, ffmpeg—require installation.

</level_tooling>

<level_1_patterns>

## Pure Computation (Stage 3A)

When the router determines your code is pure computation, test it directly.

```python
# ✅ Test pure functions directly, no doubles needed
def test_command_includes_checksum_flag() -> None:
    cmd = build_rclone_command("/source", "remote:dest", checksum=True)
    assert "--checksum" in cmd


def test_unicode_paths_preserved() -> None:
    cmd = build_rclone_command("/tank/фото", "remote:резервная")
    assert "/tank/фото" in cmd


def test_validates_empty_order() -> None:
    result = validate_order(Order(items=[]))
    assert result.ok is False
    assert "empty" in result.error.lower()
```

## Temporary Directories

Temp dirs are NOT external dependencies—use freely at Level 1.

```python
import tempfile
from pathlib import Path


def test_loads_yaml_config() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text("""
site_dir: ./site
base_url: http://localhost:1313
""")
        config = load_config(config_path)
        assert config.site_dir == "./site"
```

## Extracted Logic (Stage 3B)

When the router says "extract the pure part," factor your code.

**Before** (tangled):

```python
class OrderProcessor:
    def __init__(self, repository) -> None:
        self.repository = repository

    def process(self, order: Order) -> None:
        # Validation (pure) mixed with persistence (integration)
        if not order.items:
            raise ValidationError("Empty order")
        self.repository.save(order)
```

**After** (factored):

```python
# Pure computation - test at Level 1, no doubles
def validate_order(order: Order) -> ValidationResult:
    if not order.items:
        return ValidationResult(ok=False, error="Empty order")
    return ValidationResult(ok=True)


# Thin wrapper - test at Level 2 with real database
class OrderProcessor:
    def __init__(self, repository) -> None:
        self.repository = repository

    def process(self, order: Order) -> None:
        result = validate_order(order)
        if not result.ok:
            raise ValidationError(result.error)
        self.repository.save(order)
```

Now test separately:

```python
# Level 1: Test validation logic exhaustively
def test_validates_empty_order() -> None:
    result = validate_order(Order(items=[]))
    assert result.ok is False


# Level 2: Test persistence with real database (see Level 2 section)
```

</level_1_patterns>

<exception_implementations>

## Exception Case Implementations

When the `/testing` router reaches Stage 5 and an exception applies, here's how to implement each in Python.

### Exception 1: Failure Modes

Testing retry logic, error handling, circuit breakers.

```python
from typing import Protocol


class HttpClient(Protocol):
    def fetch(self, url: str) -> dict: ...


def test_retries_on_timeout() -> None:
    attempts = 0

    class TimeoutingClient:
        def fetch(self, url: str) -> dict:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise TimeoutError("Request timed out")
            return {"status": 200, "body": "ok"}

    result = fetch_with_retry("https://api.example.com", TimeoutingClient())
    assert attempts == 3
    assert result["status"] == 200
```

### Exception 2: Interaction Protocols

Testing call sequences, saga compensation, "no extra calls."

```python
def test_saga_compensates_in_reverse_order() -> None:
    calls: list[str] = []

    class Step1:
        def execute(self) -> None:
            calls.append("step1-execute")

        def compensate(self) -> None:
            calls.append("step1-compensate")

    class Step2:
        def execute(self) -> None:
            calls.append("step2-execute")
            raise RuntimeError("Step 2 failed")

        def compensate(self) -> None:
            calls.append("step2-compensate")

    saga = Saga([Step1(), Step2()])

    with pytest.raises(RuntimeError):
        saga.run()

    assert calls == [
        "step1-execute",
        "step2-execute",
        "step2-compensate",
        "step1-compensate",
    ]
```

### Exception 3: Time and Concurrency

Testing time-dependent behavior with controlled time.

```python
from unittest.mock import patch


def test_lease_renews_before_expiry() -> None:
    with patch("time.time") as mock_time:
        mock_time.return_value = 1000.0

        renewed = False

        def on_renew() -> None:
            nonlocal renewed
            renewed = True

        lease = Lease(ttl=30, renew_at=25, on_renew=on_renew)

        # Before renewal threshold
        mock_time.return_value = 1024.0
        lease.tick()
        assert renewed is False

        # After renewal threshold
        mock_time.return_value = 1026.0
        lease.tick()
        assert renewed is True
```

### Exception 4: Safety

Testing destructive operations without executing them.

```python
def test_processes_refund_for_cancelled_order() -> None:
    refunds: list[dict] = []

    class FakePaymentProvider:
        def refund(self, charge_id: str, amount: float, reason: str) -> dict:
            refunds.append({"charge_id": charge_id, "amount": amount, "reason": reason})
            return {"refund_id": "refund_123", "status": "succeeded"}

    processor = OrderProcessor(payment=FakePaymentProvider())
    processor.cancel_order(order_with_charge)

    assert refunds == [
        {"charge_id": "ch_123", "amount": 99.99, "reason": "order_cancelled"}
    ]
```

### Exception 6: Observability

Testing request details the real system can't expose.

```python
def test_includes_idempotency_key() -> None:
    requests: list[dict] = []

    class SpyHttpClient:
        def post(self, url: str, headers: dict, body: dict) -> dict:
            requests.append({"url": url, "headers": headers, "body": body})
            return {"status": 200}

    client = PaymentClient(http=SpyHttpClient())
    client.charge(amount=100, card_token="tok_123")

    assert len(requests) == 1
    assert "Idempotency-Key" in requests[0]["headers"]
```

</exception_implementations>

<level_2_patterns>

## Integration Patterns

When the router determines Level 2 is appropriate, use real dependencies via harnesses.

### pytest Fixtures for Harnesses

```python
import pytest


@pytest.fixture(scope="module")
def database() -> PostgresHarness:
    harness = PostgresHarness()
    harness.start()
    yield harness
    harness.stop()


@pytest.fixture(autouse=True)
def reset_database(database: PostgresHarness) -> None:
    yield
    database.reset()


def test_user_repository_saves_and_retrieves(database: PostgresHarness) -> None:
    repo = UserRepository(database.connection_string)
    user = User(email="test@example.com", name="Test User")

    repo.save(user)
    retrieved = repo.find_by_email("test@example.com")

    assert retrieved is not None
    assert retrieved.name == "Test User"
```

### Binary Harness

```python
@dataclass
class HugoHarness:
    site_dir: Path
    output_dir: Path

    def build(self, args: list[str] | None = None) -> subprocess.CompletedProcess:
        args = args or []
        return subprocess.run(
            [
                "hugo",
                "--source",
                str(self.site_dir),
                "--destination",
                str(self.output_dir),
            ]
            + args,
            capture_output=True,
            text=True,
        )


def test_builds_site_successfully(hugo: HugoHarness) -> None:
    result = hugo.build()
    assert result.returncode == 0
    assert (hugo.output_dir / "index.html").exists()
```

### Docker Harness

```python
from dataclasses import dataclass
import subprocess


@dataclass
class DockerHarness:
    """Base class for Docker-based test harnesses."""

    container_name: str
    image: str
    port: int

    def start(self) -> None:
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                self.container_name,
                "-p",
                f"{self.port}:{self.port}",
                self.image,
            ],
            check=True,
        )
        self._wait_for_ready()

    def stop(self) -> None:
        subprocess.run(["docker", "rm", "-f", self.container_name])

    def _wait_for_ready(self, timeout: int = 30) -> None:
        raise NotImplementedError


@dataclass
class PostgresHarness(DockerHarness):
    """PostgreSQL test harness."""

    container_name: str = "test-postgres"
    image: str = "postgres:15"
    port: int = 5432
    password: str = "test"

    def start(self) -> None:
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                self.container_name,
                "-p",
                f"{self.port}:5432",
                "-e",
                f"POSTGRES_PASSWORD={self.password}",
                self.image,
            ],
            check=True,
        )
        self._wait_for_ready()

    @property
    def connection_string(self) -> str:
        return f"postgresql://postgres:{self.password}@localhost:{self.port}/postgres"
```

</level_2_patterns>

<level_3_patterns>

## E2E Patterns

When the router determines Level 3 is required (real credentials, external services).

### Skip If No Credentials (Optional Tests Only)

```python
credentials = load_credentials()
skip_no_creds = pytest.mark.skipif(
    credentials is None, reason="E2E credentials not configured"
)


@skip_no_creds
def test_full_sync_workflow(dropbox_test_folder: str) -> None:
    result = sync_to_dropbox(local_path, dropbox_test_folder)
    assert result.success
    assert result.files_transferred > 0
```

**Note**: Use `skipif` only for **optional** E2E tests. Required tests must fail loudly—see credential management section.

</level_3_patterns>

<property_based_testing>
Property-based testing is **MANDATORY** for these code types:

| Code Type               | Property to Test         | Example                      |
| ----------------------- | ------------------------ | ---------------------------- |
| Parsers                 | `parse(format(x)) == x`  | JSON, YAML, CLI args         |
| Mathematical operations | Algebraic properties     | Commutativity, associativity |
| Serialization           | `decode(encode(x)) == x` | Protocol buffers, msgpack    |
| Complex algorithms      | Invariant preservation   | Sorting, tree operations     |

### Hypothesis Configuration

```python
from hypothesis import given, settings, strategies as st


# ✅ REQUIRED: All property tests use @given decorator
@given(st.text())
def test_round_trips_through_encoding(text: str) -> None:
    encoded = encode(text)
    decoded = decode(encoded)
    assert decoded == text


# ✅ REQUIRED: Settings for slow generators
@settings(max_examples=500, deadline=None)
@given(st.binary(min_size=1, max_size=10_000))
def test_handles_arbitrary_binary(data: bytes) -> None:
    result = process(data)
    assert result.valid or result.error is not None


# ✅ REQUIRED: Composite strategies for complex data
@st.composite
def valid_orders(draw: st.DrawFn) -> Order:
    items = draw(st.lists(st.builds(OrderItem), min_size=1, max_size=10))
    return Order(items=items, total=sum(item.price for item in items))


@given(valid_orders())
def test_order_validation_accepts_valid(order: Order) -> None:
    result = validate_order(order)
    assert result.ok is True
```

### Common Properties

```python
# ✅ Idempotency: f(f(x)) == f(x)
@given(st.text())
def test_normalization_is_idempotent(text: str) -> None:
    once = normalize(text)
    twice = normalize(once)
    assert once == twice


# ✅ Commutativity: f(a, b) == f(b, a)
@given(st.integers(), st.integers())
def test_merge_is_commutative(a: int, b: int) -> None:
    assert merge(a, b) == merge(b, a)


# ✅ Invariant preservation: property holds before and after
@given(st.lists(st.integers()))
def test_sort_preserves_elements(items: list[int]) -> None:
    sorted_items = sort(items)
    assert sorted(items) == sorted(sorted_items)
    assert len(items) == len(sorted_items)
```

**If testing a parser or serializer without property-based tests, the tests are INCOMPLETE.**

</property_based_testing>

<data_factories>
Test data MUST use factories with named constants. Never use arbitrary literals.

### Dataclass Factory Pattern

```python
from dataclasses import dataclass, field
from typing import Iterator
import itertools

# Module-level counter for unique IDs
_id_counter: Iterator[int] = itertools.count(1)

# Named constants at module level
DEFAULT_PERFORMANCE_SCORE = 90
DEFAULT_ACCESSIBILITY_SCORE = 100
FAILING_PERFORMANCE_THRESHOLD = 45


@dataclass
class AuditResultFactory:
    """Factory for creating test audit results."""

    url: str = field(default_factory=lambda: f"https://example.com/{next(_id_counter)}")
    performance: int = DEFAULT_PERFORMANCE_SCORE
    accessibility: int = DEFAULT_ACCESSIBILITY_SCORE

    def build(self) -> dict:
        return {
            "url": self.url,
            "scores": {
                "performance": self.performance,
                "accessibility": self.accessibility,
            },
        }


# ✅ CORRECT: Factory with named constant
def test_fails_on_low_performance() -> None:
    result = AuditResultFactory(performance=FAILING_PERFORMANCE_THRESHOLD).build()
    analysis = analyze_results([result])
    assert analysis.passed is False


# ❌ REJECTED: Magic value (PLR2004)
def test_fails_on_low_performance_bad() -> None:
    result = {"scores": {"performance": 45}}  # What is 45?
    analysis = analyze_results([result])
    assert analysis.passed is False
```

### Builder Pattern

```python
@dataclass
class UserBuilder:
    """Builder for test users with sensible defaults."""

    email: str = field(default_factory=lambda: f"user{next(_id_counter)}@test.com")
    name: str = "Test User"
    role: str = "member"
    active: bool = True

    def with_admin_role(self) -> "UserBuilder":
        self.role = "admin"
        return self

    def inactive(self) -> "UserBuilder":
        self.active = False
        return self

    def build(self) -> User:
        return User(
            email=self.email, name=self.name, role=self.role, active=self.active
        )


# ✅ CORRECT: Builder with fluent interface
def test_admin_can_delete_users() -> None:
    admin = UserBuilder().with_admin_role().build()
    target = UserBuilder().build()
    result = delete_user(admin, target)
    assert result.success is True
```

</data_factories>

<file_naming>
Test level is indicated by filename suffix:

| Level | Suffix            | Example                             |
| ----- | ----------------- | ----------------------------------- |
| 1     | `.unit.py`        | `test_validation.unit.py`           |
| 2     | `.integration.py` | `test_database.integration.py`      |
| 3     | `.e2e.py`         | `test_checkout.e2e.py`              |
| 3     | `.e2e.spec.py`    | `checkout.e2e.spec.py` (Playwright) |

### Directory Structure

```text
spx/
└── {NN}-{slug}.enabler/
    └── {NN}-{slug}.outcome/
        ├── {slug}.outcome.md
        └── tests/
            ├── test_{name}.unit.py
            ├── test_{name}.integration.py
            └── test_{name}.e2e.py
```

</file_naming>

<dependency_injection>
When Stage 3 of `/testing` determines DI is appropriate, use Protocols.

### Protocol Definition

```python
from typing import Protocol


class CommandRunner(Protocol):
    """Protocol for running shell commands."""

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        """Run command, return (exit_code, stdout, stderr)."""
        ...


class HttpClient(Protocol):
    """Protocol for HTTP operations."""

    def fetch(self, url: str) -> dict:
        """Fetch URL, return response as dict."""
        ...
```

### Dataclass Dependencies

```python
from dataclasses import dataclass
from typing import Callable
import os


@dataclass
class SyncDependencies:
    """Dependencies for sync operation, injectable for testing."""

    run_command: CommandRunner
    get_env: Callable[[str], str | None] = os.environ.get


def sync_to_remote(source: str, dest: str, deps: SyncDependencies) -> SyncResult:
    """Sync files to remote, using injected dependencies."""
    cmd = build_command(source, dest)
    returncode, stdout, stderr = deps.run_command.run(cmd)
    return SyncResult(success=returncode == 0, output=stdout)
```

### Test Double Implementation

```python
# ✅ CORRECT: Test double via DI (Exception 1: Failure modes)
def test_handles_command_failure() -> None:
    class FailingRunner:
        def run(self, cmd: list[str]) -> tuple[int, str, str]:
            return (1, "", "Connection refused")

    deps = SyncDependencies(run_command=FailingRunner())
    result = sync_to_remote("/src", "remote:dest", deps)
    assert result.success is False


# ❌ REJECTED: Mocking via patch
@patch("subprocess.run")
def test_handles_command_failure_bad(mock_run: Mock) -> None:
    mock_run.return_value = Mock(returncode=1)
    result = sync_to_remote("/src", "remote:dest")  # No DI!
    assert result.success is False
```

</dependency_injection>

<test_signatures>
All test functions MUST have complete type annotations.

```python
import pytest
from pathlib import Path


# ✅ REQUIRED: -> None on all test functions
def test_validates_input() -> None:
    result = validate("test")
    assert result.valid


# ✅ REQUIRED: Type annotations on fixture parameters
def test_creates_file(tmp_path: Path) -> None:
    file = tmp_path / "test.txt"
    file.write_text("content")
    assert file.exists()


# ✅ REQUIRED: Return type on fixtures
@pytest.fixture
def config(tmp_path: Path) -> Config:
    return Config(path=tmp_path)


# ❌ REJECTED: Missing -> None (ANN201)
def test_something(self):
    pass


# ❌ REJECTED: Missing parameter type (ANN001)
def test_with_fixture(self, tmp_path) -> None:
    pass
```

</test_signatures>

<credential_management>
E2E tests requiring credentials MUST fail loudly, not skip silently.

```python
CREDENTIALS_DOC = """
Level 3 tests require these environment variables:

Required:
  STRIPE_TEST_KEY    - From 1Password: "Engineering/Test Credentials"

Setup:
  cp .env.test.example .env.test
  # Fill in values from 1Password
"""


def load_credentials() -> dict | None:
    key = os.environ.get("STRIPE_TEST_KEY")
    if not key:
        return None
    return {"key": key}


def require_credentials() -> dict:
    creds = load_credentials()
    if not creds:
        raise RuntimeError(f"Missing required credentials.\n\n{CREDENTIALS_DOC}")
    return creds


# ✅ CORRECT: Fail loudly if credentials required but missing
# File: test_payment.e2e.py
def test_charges_card() -> None:
    creds = require_credentials()
    client = StripeClient(creds["key"])
    result = client.charge(amount=100)
    assert result.success


# ❌ REJECTED: Silent skip on required credentials
# File: test_payment.e2e.py
@pytest.mark.skipif(not load_credentials(), reason="No credentials")
def test_charges_card_bad() -> (
    None
): ...  # CI goes green with zero payment verification!
```

</credential_management>

<anti_patterns>

## Python-Specific Anti-Patterns

### Using unittest.mock.patch on External Services

```python
# ❌ WRONG: Mocking external service
@patch("httpx.Client.get")
def test_fetches_user(mock_get: Mock) -> None:
    mock_get.return_value = Mock(json=lambda: {"id": 1})
    user = api_client.get_user(1)
    assert user.id == 1  # Proves nothing about real API


# ✅ RIGHT: Use DI for Level 1, real service for Level 2/3
def test_parses_user_response() -> None:
    # Level 1: Test parsing logic with known data
    response = {"id": 1, "name": "Test", "email": "test@example.com"}
    user = parse_user_response(response)
    assert user.id == 1


# File: test_api.e2e.py
def test_fetches_real_user(test_credentials: dict) -> None:
    # Level 3: Test against real API
    client = ApiClient(credentials=test_credentials)
    user = client.get_user(known_test_user_id)
    assert user is not None
```

### Overusing pytest-mock

```python
# ❌ WRONG: mocker fixture everywhere
def test_sync(mocker: MockerFixture) -> None:
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("subprocess.run", return_value=Mock(returncode=0))
    result = sync_files(src, dest)
    assert result.success  # What did we prove? Nothing.


# ✅ RIGHT: DI for controllable behavior
def test_sync_returns_success_on_zero_exit() -> None:
    class FakeRunner:
        def run(self, cmd: list[str]) -> tuple[int, str, str]:
            return (0, "Done", "")

    deps = SyncDeps(runner=FakeRunner())
    result = sync_files(src, dest, deps)
    assert result.success
```

### Testing Library Behavior

```python
# ❌ WRONG: Testing that argparse works
def test_parses_verbose_flag() -> None:
    parser = create_parser()
    args = parser.parse_args(["--verbose"])
    assert args.verbose is True  # Testing argparse, not your code


# ✅ RIGHT: Test YOUR behavior that uses parsed args
def test_verbose_mode_produces_detailed_output() -> None:
    output = run_command(Config(verbose=True))
    assert "DEBUG:" in output
```

</anti_patterns>

<rejection_criteria>

| Issue                              | Example                                   | Rule/Reason           |
| ---------------------------------- | ----------------------------------------- | --------------------- |
| Missing property tests for parser  | `test_parse_json` without `@given`        | Mandatory for parsers |
| Magic values in assertions         | `assert score == 45`                      | PLR2004               |
| Missing `-> None` on test          | `def test_foo(self):`                     | ANN201                |
| Mocking                            | `@patch("module.func")`                   | Use DI instead        |
| Silent skip on required dependency | `@pytest.mark.skipif(not has_postgres())` | Must fail, not skip   |
| Wrong filename suffix              | `test_db.py` for integration test         | Use `.integration.py` |
| Untyped fixture parameter          | `def test_foo(tmp_path) -> None:`         | ANN001                |

</rejection_criteria>

<specified_node_exclusion>

## Specified Node Exclusion

When tests are written before the implementation exists (specified nodes), they import non-existent modules and break type checkers and the test runner. The spec-tree convention uses `spx/EXCLUDE` as the source of truth. The `spx` CLI reads this file and skips excluded nodes at invocation time.

### How It Works

`spx test passing` reads `spx/EXCLUDE` and passes exclusion flags to each tool:

| Tool        | Exclusion mechanism                 |
| ----------- | ----------------------------------- |
| **pytest**  | `--ignore=spx/{node}/`              |
| **mypy**    | Excluded from check scope           |
| **pyright** | Excluded from check scope           |
| **ruff**    | NOT excluded — style always checked |

`spx` never writes to `pyproject.toml` or any project configuration file. The project's own tools always run against all files.

### Ruff Always Checks

Do NOT exclude specified nodes from ruff. Test files are valid Python with correct style. Only type checkers (which resolve imports) and the test runner (which executes imports) need exclusion.

</specified_node_exclusion>

<success_criteria>
Code follows these standards when:

- [ ] Parsers, serializers, math operations have property-based tests with `@given`
- [ ] Test data uses factories with named constants (no magic values)
- [ ] File names indicate level (`.unit.py`, `.integration.py`, `.e2e.py`)
- [ ] DI uses Protocols, not mocking
- [ ] Integration tests use harnesses with real dependencies
- [ ] All test functions have `-> None` return type
- [ ] All fixture parameters have type annotations
- [ ] Required credentials fail loudly, not skip silently

</success_criteria>
