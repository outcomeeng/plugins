# Test Language Selection

## Purpose

This decision governs which programming language is used for test evidence in spec-tree nodes. Consistent language selection ensures the quality gate runs a single test framework and prevents orphaned tests that no runner collects.

## Context

**Business impact:** Orphaned tests — test files that exist but no runner collects — create phantom evidence. The quality gate passes, but the assertions are unverified.

**Technical constraints:** All implementation code in this repository (build scripts, validation tools, sync utilities) is Python. The quality gate runs pytest.

## Decision

Python (pytest) is the test language for all spec-tree nodes.

## Rationale

Two categories of testable artifacts exist:

1. **Infrastructure scripts** (validation, sync-exclude, distribute, xml-spacing) — Python implementations tested with pytest.
2. **Skill behavior** (PDR auditing, test auditing, context loading) — skills are prompt engineering artifacts. Their behavior is tested by exercising observable effects (file outputs, structured verdicts) via Python test harnesses.

## Trade-offs accepted

| Trade-off                                                             | Mitigation / reasoning                                                                                    |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Skill behavior tests use Python, not the language the skill "targets" | Skills are language-agnostic prompts; Python tests verify observable outputs, not language-specific logic |

## Compliance

### Recognized by

All test files in `spx/**/tests/` use the Python naming convention: `test_{slug}.{level}.py`.

### MUST

- Use Python (pytest) for all spec-tree test evidence — the quality gate runs a single test framework ([review])
- Reference Python test files in spec assertions — `([test](tests/test_{slug}.{level}.py))` ([review])
