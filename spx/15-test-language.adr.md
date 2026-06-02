# Test Language Selection

## Purpose

This decision governs which programming language and runner the marketplace uses for `[test]` evidence in spec-tree nodes. The `[test]` lane is one of the evidence-execution lanes declared in `spx/14-verification.pdr.md`; this decision selects its language and runner. `[eval]` evidence lives in a separate lane and is not governed by this ADR.

## Context

**Business impact:** Orphaned test files — files that exist but no runner collects — create phantom evidence. The quality gate passes while assertions go unverified. A single language and runner for `[test]` evidence makes collection deterministic and silences the failure mode.

**Technical constraints:**

- Implementation code in the marketplace — validation scripts, build helpers, sync utilities, eval-harness internals — is Python.
- The `[test]` lane is for deterministic evidence: pure logic, parser-backed structural checks, command-builder scenarios, file-output assertions. Non-deterministic LLM-driven behavior is the `[eval]` lane's concern, not this lane's.
- The marketplace ships a single quality gate (`just check`); per-language test frameworks fragment that gate.
- Spec-tree node directories follow the kebab-case slug convention while Python modules require snake_case import names. A single file naming rule reconciles both.

## Decision

Python (pytest) is the language and runner for all `[test]` evidence in the spec tree. Test files follow `test_{subject}.{evidence}.{level}[.{runner}].py` and live under each node's `tests/` directory.

## Rationale

Two categories of artifacts produce `[test]` evidence:

1. **Infrastructure scripts** (validation, distribute, xml-spacing, eval-harness internals) — Python implementations tested with pytest.
2. **Skill behavior verified through observable side effects** — file outputs, structured verdicts, link-integrity checks. Pytest verifies the harness contract: input goes in, structural verdict comes out. The lane stays deterministic because the grader is code, not an LLM.

LLM-driven skill behavior — where the assertion is about what the model concludes rather than what observable artifact it produces — belongs in the `[eval]` lane per `spx/14-verification.pdr.md`. Pytest as the `[test]` runner remains the right choice precisely because it does not try to absorb the LLM lane.

Alternatives rejected: a single runner spanning all evidence mechanisms (collapses cost profiles and cadence into one CI gate); shell-based test runners (lose import-mode discovery, type checking, and parametrization); per-node runner configuration (drifts whenever a node moves).

## Trade-offs accepted

| Trade-off                                                                                                                         | Mitigation / reasoning                                                                                                                                   |
| --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill-behavior assertions whose subject is LLM output cannot use the `[test]` lane                                                | The `[eval]` lane governed by `spx/14-verification.pdr.md` and `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md` carries that load |
| Snake-case `.py` files inside kebab-case node directories looks visually inconsistent                                             | The two naming systems serve different consumers (spec-tree directory enumeration vs. Python module imports); each follows its own convention            |
| `testpaths` discovery walks the whole spec tree, which means test files for non-`[test]`-lane evidence must not match `test_*.py` | The `[eval]` lane uses its own directory layout (`evals/{rule}/`) with file names that pytest's `python_files = test_*.py` glob does not pick up         |

## Compliance

### Recognized by

All `[test]` evidence files in `spx/**/tests/` use the Python naming convention `test_{subject}.{evidence}.{level}[.{runner}].py`. Every `[test](path)` link in a spec assertion resolves to a file under this convention. No `[test]` link points outside the pytest-discovered spec-tree subtree. Python test infrastructure that these `[test]` files depend on lives at the methodology-mandated path declared by `spx/15-test-infrastructure.pdr.md` (`<package>_testing/harnesses/`, `<package>_testing/generators/`, `<package>_testing/fixtures/`), never inside any `tests/` directory.

### MUST

- Use Python (pytest) for all `[test]` evidence in the spec tree — the quality gate runs a single runner for this lane ([review])
- Reference Python test files in `[test]` links using `([test](tests/test_{subject}.{evidence}.{level}.py))` ([review])
- `pytest.ini` (or `pyproject.toml` `[tool.pytest.ini_options]`) declares `testpaths` covering `spx/` so pytest discovers every `test_*.py` under any `spx/**/tests/` directory ([review])

### NEVER

- Use a non-pytest runner for `[test]` evidence in the spec tree — the lane is single-runner by decision ([review])
- Route `[eval]` evidence through pytest as its primary execution surface — `[eval]` belongs to the lane governed by `spx/14-verification.pdr.md` ([review])
- Reference a `[test]` link from a spec assertion to a path outside `spx/**/tests/` — co-location is mandatory for `[test]`-lane evidence ([review])
