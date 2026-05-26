# Security Patterns

Security is an architectural concern. These patterns must be enforced by ADRs.

## Core Principle

> **Validate at boundaries. Trust nothing from outside. Fail securely.**

---

## Context-Aware Threat Modeling

Different applications have different threat models. The ADR must specify which applies.

### Application Context Guide

| Application Type    | Trust Boundary                    | User Input                  | External Services        |
| ------------------- | --------------------------------- | --------------------------- | ------------------------ |
| **CLI tool**        | User invoking the tool is trusted | Validate format, not intent | Verify SSL               |
| **Web service**     | All input is untrusted            | Validate everything         | Verify SSL, authenticate |
| **Internal script** | Depends on deployment             | Validate format             | Depends on network       |
| **Library/package** | Consumers are untrusted           | Validate everything         | N/A                      |

### Example ADR Section

```markdown
## Security Context

This is a **CLI tool** invoked by a trusted user.

**Trust boundary**: User input from command-line arguments is trusted
for intent (user wants to sync these files) but validated for format
(paths must exist, remotes must be configured).

**Subprocess calls**: S603/S607 violations are false positives because
the user controls all inputs.
```

---

## Input Validation at Boundaries

Validate ALL input at system boundaries. Use Pydantic.

### The Boundary

```
Untrusted Input  ──►  Validation Layer  ──►  Trusted Domain Logic
      │                      │                       │
      │                      ▼                       │
      │               REJECT INVALID                 │
      │                                              │
      └── API requests, CLI args, files, env vars ──┘
```

### Pydantic Validation

```python
from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class SyncConfig(BaseModel):
    """Validated configuration for sync operation."""

    source: Path
    destination: str
    max_retries: int = Field(ge=0, le=10, default=3)

    @field_validator("source")
    @classmethod
    def source_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Source path does not exist: {v}")
        return v

    @field_validator("destination")
    @classmethod
    def destination_must_be_remote(cls, v: str) -> str:
        if ":" not in v:
            raise ValueError("Destination must be remote (format: remote:path)")
        return v
```

### CLI Argument Validation

```python
import argparse
from pydantic import ValidationError


def parse_args() -> SyncConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination")
    parser.add_argument("--max-retries", type=int, default=3)

    args = parser.parse_args()

    try:
        return SyncConfig(
            source=args.source,
            destination=args.destination,
            max_retries=args.max_retries,
        )
    except ValidationError as e:
        parser.error(str(e))
```

---

## No Hardcoded Secrets

Secrets come from environment or secure stores. Never hardcoded.

### Forbidden

```python
# FORBIDDEN - Hardcoded secrets
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgres://user:password@localhost/db"
```

### Required

```python
import os


def get_api_key() -> str:
    """Get API key from environment.

    Raises:
        EnvironmentError: If API_KEY not set.
    """
    key = os.environ.get("API_KEY")
    if not key:
        raise EnvironmentError("API_KEY environment variable required")
    return key
```

### Configuration Pattern

```python
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Application configuration from environment."""

    api_key: str
    database_url: str
    debug: bool = False

    class Config:
        env_prefix = "APP_"  # Reads APP_API_KEY, APP_DATABASE_URL


config = AppConfig()  # Raises if required vars missing
```

---

## Subprocess Safety

Subprocess calls are a common attack vector. Handle carefully.

### The Risks

1. **Command injection**: User input interpolated into shell commands
2. **Path traversal**: User input used in file paths
3. **Argument injection**: User input as command arguments

### Safe Subprocess Pattern

```python
import subprocess
from pathlib import Path


def run_rclone_sync(
    source: Path,
    dest: str,
    logger: Logger,
) -> subprocess.CompletedProcess[str]:
    """Run rclone sync safely.

    Args:
        source: Validated source path (must exist)
        dest: Validated remote destination (format: remote:path)
        logger: Logger for diagnostics

    Returns:
        CompletedProcess with stdout/stderr
    """
    # Build command as list (no shell interpolation)
    cmd = [
        "rclone",
        "sync",
        str(source),
        dest,
        "--checksum",
        "--verbose",
    ]

    logger.debug(f"Running: {' '.join(cmd)}")

    # No shell=True, capture output, set timeout
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=3600,
        check=True,
    )
```

### What Makes It Safe?

1. **List form**: `["rclone", "sync", ...]` not `f"rclone sync {source}"`
2. **No shell=True**: Command parsed directly, no shell interpretation
3. **Validated inputs**: `source` and `dest` validated by Pydantic before reaching here
4. **Timeout**: Prevents hanging indefinitely
5. **check=True**: Raises on non-zero exit

### When shell=True is Acceptable

Only with HARDCODED commands:

```python
# ACCEPTABLE - Hardcoded command, no user input
result = subprocess.run(
    "ls -la | head -10",
    shell=True,
    capture_output=True,
)

# FORBIDDEN - User input in shell command
result = subprocess.run(
    f"ls -la {user_provided_path}",  # INJECTION RISK
    shell=True,
)
```

### Noqa for False Positives

In CLI tools where the user controls all inputs:

```python
result = subprocess.run(
    cmd,  # noqa: S603 - CLI tool, user controls all inputs
    capture_output=True,
)
```

---

## No eval/exec

Dynamic code execution is almost never needed.

### Forbidden

```python
# FORBIDDEN - Arbitrary code execution
user_code = request.get("code")
exec(user_code)

# FORBIDDEN - Even "safe" eval
user_expr = request.get("expression")
result = eval(user_expr)  # Can still be exploited
```

### Alternatives

| Need               | Solution                 |
| ------------------ | ------------------------ |
| Dynamic dispatch   | Dictionary of functions  |
| User expressions   | Domain-specific parser   |
| Plugin system      | importlib with allowlist |
| Template rendering | Jinja2 with sandbox      |

### Dynamic Dispatch Example

```python
# Instead of eval(f"{operation}(a, b)")
OPERATIONS: dict[str, Callable[[int, int], int]] = {
    "add": lambda a, b: a + b,
    "subtract": lambda a, b: a - b,
    "multiply": lambda a, b: a * b,
}


def calculate(operation: str, a: int, b: int) -> int:
    if operation not in OPERATIONS:
        raise ValueError(f"Unknown operation: {operation}")
    return OPERATIONS[operation](a, b)
```

---

## SSL Verification

Always verify SSL certificates for HTTPS connections.

### Required

```python
import requests

# SSL verification is ON by default - don't disable it
response = requests.get("https://api.example.com/data")

# If you need custom CA:
response = requests.get(
    "https://internal.example.com/data",
    verify="/path/to/ca-bundle.crt",
)
```

### Forbidden

```python
# FORBIDDEN - Disables SSL verification
response = requests.get(
    "https://api.example.com/data",
    verify=False,  # MITM vulnerability
)
```

---

## Error Handling Security

Don't leak sensitive information in errors.

### Safe Error Messages

```python
class AuthenticationError(Exception):
    """Authentication failed."""

    def __init__(self) -> None:
        # Don't reveal WHY authentication failed
        super().__init__("Authentication failed")


# In handler:
try:
    authenticate(username, password)
except InvalidCredentialsError:
    # Log the real reason internally
    logger.warning(f"Failed login for user: {username}")
    # Return generic message to user
    raise AuthenticationError()
```

### Logging Secrets

```python
# FORBIDDEN - Logging secrets
logger.info(f"Connecting with API key: {api_key}")

# ACCEPTABLE - Masked logging
logger.info(f"Connecting with API key: {api_key[:4]}...")

# BETTER - Don't log secrets at all
logger.info("Connecting to API")
```

---

## File Path Safety

Prevent path traversal attacks.

### The Risk

```python
# DANGEROUS - User can access any file
user_filename = request.get("filename")  # "../../../etc/passwd"
path = Path(f"/app/uploads/{user_filename}")
content = path.read_text()  # Reads /etc/passwd!
```

### Safe Pattern

```python
from pathlib import Path


def safe_read_file(base_dir: Path, filename: str) -> str:
    """Read file safely, preventing path traversal.

    Args:
        base_dir: Base directory (must be absolute)
        filename: User-provided filename

    Returns:
        File contents

    Raises:
        ValueError: If path escapes base_dir
        FileNotFoundError: If file doesn't exist
    """
    # Resolve to absolute path
    target = (base_dir / filename).resolve()

    # Verify it's still under base_dir
    if not target.is_relative_to(base_dir):
        raise ValueError("Path traversal detected")

    return target.read_text()
```

---

## Pickle Safety

Never unpickle untrusted data.

### The Risk

Pickle can execute arbitrary code during deserialization.

```python
# FORBIDDEN - Unpickling untrusted data
import pickle

user_data = request.get("data")
obj = pickle.loads(user_data)  # Can execute arbitrary code!
```

### Safe Alternatives

| Need               | Solution                      |
| ------------------ | ----------------------------- |
| Data serialization | JSON, MessagePack             |
| Python objects     | Pydantic models               |
| Caching            | JSON with schema validation   |
| Internal IPC       | Protocol Buffers, MessagePack |

### When Pickle is Acceptable

Only for internal data YOU control:

```python
# ACCEPTABLE - Internal cache, not from users
import pickle
from pathlib import Path

CACHE_FILE = Path("/var/cache/app/internal.pkl")


def save_internal_cache(data: InternalState) -> None:
    with CACHE_FILE.open("wb") as f:
        pickle.dump(data, f)


def load_internal_cache() -> InternalState:
    with CACHE_FILE.open("rb") as f:
        return pickle.load(f)  # noqa: S301 - internal cache only
```

---

## Key Principles

1. **Context determines threat model**: CLI vs web service vs library

2. **Validate at boundaries**: Pydantic for all external input

3. **No hardcoded secrets**: Environment variables or secret stores

4. **Subprocess as list**: Never interpolate user input into shell commands

5. **No eval/exec**: Use dictionaries, parsers, or importlib instead

6. **Verify SSL**: Never set `verify=False`

7. **Secure errors**: Don't leak sensitive information

8. **No untrusted pickle**: Use JSON or Pydantic instead
