# Security Patterns

Security constraints an ADR states for a Python product.

## Contents

- [Context-Aware Threat Modeling](#context-aware-threat-modeling)
- [Input Validation at Boundaries](#input-validation-at-boundaries)
- [Subprocess Boundary](#subprocess-boundary)
- [Secrets](#secrets)

## Context-Aware Threat Modeling

The ADR Rationale names the application context, because the context sets the trust boundary.

| Application type | Trust boundary                    | User input                  | External services        |
| ---------------- | --------------------------------- | --------------------------- | ------------------------ |
| CLI tool         | User invoking the tool is trusted | Validate format, not intent | Verify SSL               |
| Web service      | All input is untrusted            | Validate everything         | Verify SSL, authenticate |
| Internal script  | Depends on deployment             | Validate format             | Depends on network       |
| Library/package  | Consumers are untrusted           | Validate everything         | Not applicable           |

```markdown
## Rationale

This is a **CLI tool** invoked by a trusted user. Command-line arguments are trusted for intent and validated for format (paths exist, remotes are configured). Subprocess lint findings S603 and S607 are false positives because the user controls every input.
```

## Input Validation at Boundaries

All input from arguments, files, environment variables, and requests passes through a Pydantic model before reaching domain logic. The ADR names the model for each boundary and rejects invalid input at load time.

## Subprocess Boundary

Every external tool runs through an injected `CommandRunner` Protocol. The production adapter, bound at the composition root, is the only place that calls `subprocess`.

```python
class CommandRunner(Protocol):
    def run(
        self, args: Sequence[str], *, timeout_seconds: int
    ) -> subprocess.CompletedProcess[str]: ...
```

- ALWAYS pass arguments as a list with an explicit timeout.
- NEVER use `shell=True`, including for hardcoded commands. Express pipelines as explicit subprocess stages with array arguments, or replace shell composition with Python standard-library operations.
- NEVER place an analyzer suppression on a direct subprocess call in domain or orchestration code. A suppression belongs inside the production adapter and carries a concrete justification.

## Secrets

Secrets come from the environment or a secret store through a validated settings model, never from source. Logs and error messages carry no secret and no authentication failure reason.
