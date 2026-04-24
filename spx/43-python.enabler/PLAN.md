# PLAN — Python enablers for constant-object guidance and test literal enforcement

## Why

Python plugin ships `/standardizing-python` (code standards) but has no declaration of the constant-object pattern. The generic test-literal rule (from `/auditing-tests`) applies to Python tests, but no Python-specific enforcement mechanism exists — there is no ESLint-equivalent for the per-file checks, and `spx validation literal` has not been specced.

## Scope

### 1. `NN-standardizing-python.enabler/` — Python code standards (author or extend)

Add constant-object assertions. Pick the right mechanism for the shape of the data:

- **`Final`-annotated module-level dict** for string-to-string maps where keys and values are loosely related.
- **`StrEnum`** (Python 3.11+) for a closed set of string values with enumerable identity. Prefer over `Final` dict when call sites want `status is Status.OK` rather than `status == Status.OK`.
- **Frozen `@dataclass(frozen=True)`** for richer shapes (structured config, typed records).
- **Plain class with uppercase fields** is banned. Not immutable, no type narrowing, mutable by default at runtime.
- **No re-export of library constants.** Production imports from `http.HTTPStatus`, `fastapi.status`, `uvicorn.config`, etc. Tests import from the same origin.

Constant-object test: Conformance assertion that a sample module's constant definitions type-check under `mypy --strict` and refuse reassignment at runtime where the mechanism supports it.

### 2. `NN-standardizing-python-tests.enabler/` — Python test standards

- **Number allow list: `{-1, 0, 1, 2}`**. Declare as Python-specific assertion that mirrors the generic rule from `/auditing-tests`.
- **String allow list: `{""}` plus descriptive callsites** (`pytest.mark.*` description args, `assert X, "message"` message arg).
- **Enforcement mechanism — decide.**
  - Option A: custom `ruff` rule. Distributed via plugin; matches the ESLint-for-TypeScript approach.
  - Option B: AST check inside `spx validation literal` with Python support. Keeps enforcement in one tool across languages.
  - Option C: rely on human/agent judgment at `/auditing-python-tests` time (no mechanical enforcement). Weakest, most consistent with a pure-review flow.
  - Default: Option B. One enforcement tool serves both languages; avoids the `ruff` plugin-ecosystem complexity.
- **Remediation documentation.** Tell agents the four legal resolutions: library-origin import (stdlib, framework), production-owned constant object (per `/standardizing-python`), generator (`hypothesis` strategies / `faker` / harness function), descriptive-callsite inline. Fixtures explicitly banned.

## Out of scope

- The generic literal rule itself — lives in `spx/21-spec-tree.enabler/32-evidence.enabler/32-test-auditing.enabler/`.
- TypeScript equivalent — lives in `spx/43-typescript.enabler/PLAN.md`.
- `spx validation literal` Python implementation if Option B is chosen — that is a subsequent enabler under `spx/15-validation.enabler/`.

## Done when

- `NN-standardizing-python.enabler/` declares the constant-object patterns with tests.
- A decision is recorded for the enforcement mechanism (Option A/B/C) — either as a new ADR or as a rationale in the test-standards spec.
- If Option A or B is chosen, `NN-standardizing-python-tests.enabler/` exists with the declared rule and a test fixture exercising detection and non-detection cases.
- `plugins/python/skills/standardizing-python/` teaches the constant-object and no-re-export rules.

## Origin

Conversation on 2026-04-24. Python needs the same structural rules as TypeScript; enforcement mechanism is the open question. User emphasized that agents need to be told what they CAN do, not only what they can't — applies to Python just as strongly as to TypeScript.
