# Architecture Patterns

Architecture constraints that an ADR for a Python product states so that implementation stays testable without mocking.

## Contents

- [Dependency Injection](#dependency-injection)
- [Ports And Adapters](#ports-and-adapters)
- [Composition Root](#composition-root)
- [Pure Core, Impure Shell](#pure-core-impure-shell)
- [Directory Structure](#directory-structure)

## Dependency Injection

Dependencies arrive as parameters typed by a `Protocol`. Hidden dependencies (module-level loggers, config loaded inside the function, direct `subprocess` calls) are the defect an ADR forbids.

```python
# GOOD - dependencies are visible in the signature
def sync_files(
    source: Path,
    dest: Path,
    logger: Logger,
    runner: CommandRunner,
) -> SyncResult: ...


# BAD - hidden dependencies
def sync_files(source: Path, dest: Path) -> SyncResult:
    logger = logging.getLogger(__name__)
    config = load_config()
    ...
```

Injected implementations are real or controlled implementations that preserve the behavior boundary, never mocks.

## Ports And Adapters

A port is a `Protocol` stating what the domain needs. An adapter implements it for one external system. The domain imports ports only; adapters import the domain's types.

```python
class UserRepository(Protocol):
    """Port: what the domain needs from persistence."""

    def get(self, user_id: UUID) -> User | None: ...
    def save(self, user: User) -> None: ...


class PostgresUserRepository:
    """Adapter: implements UserRepository for Postgres."""

    def __init__(self, connection: Connection) -> None:
        self._conn = connection
```

## Composition Root

Adapters are constructed and wired in one entry point; no other module chooses a concrete adapter.

```python
def main() -> None:
    db = PostgresConnection(os.environ["DATABASE_URL"])
    user_service = UserService(PostgresUserRepository(db), SmtpNotificationGateway())
    UserCLI(user_service, logging.getLogger("app")).run()
```

## Pure Core, Impure Shell

Business rules live in pure typed functions. I/O sits in a thin shell that parses input, calls the pure core, and performs the effects.

## Directory Structure

```text
product/
├── pyproject.toml
├── product/
│   ├── domain/             # business logic and ports
│   ├── adapters/           # external integrations
│   └── main.py             # composition root
├── product_testing/        # test infrastructure, installable
│   ├── generators/         # variable input domains
│   ├── harnesses/          # resource and boundary mediators
│   └── fixtures/           # inert data files consumed by path
└── spx/
    └── NN-{slug}.enabler/
        └── NN-{slug}.outcome/
            └── tests/      # co-located tests with evidence/level naming
```

Co-located tests import generators and harnesses from `product_testing` and consume fixtures by path.
