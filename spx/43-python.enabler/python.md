# Python

PROVIDES the complete Python development workflow — architecture, testing, implementation, and review
SO THAT Python projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The python plugin contains 9 skills following the foundational + language-specific pattern: `/python-standards` (reference), `/python-architecture-standards` (reference), `/python-test-standards` (reference), `/test-python`, `/code-python`, `/audit-python-code`, `/audit-python-tests`, `/architect-python`, `/audit-python-architecture`. The `audit-python-{code|tests|architecture}` skills carry no Python-specific auditor agent; the generic artifact-type auditors compose them for the Python concerns in scope, per `spx/21-spec-tree.enabler/17-audit.adr.md`.

## Assertions

### Compliance

- ALWAYS: the `audit-python-{code|tests|architecture}` skills carry no Python-specific auditor agent, name no caller, and stay invocable on their own; an artifact-type auditor composes them for the Python concerns in scope, and the author-context isolation an audit verdict requires binds the author context per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, Python-specific patterns in `/test-python` ([audit])
- ALWAYS: the Python plugin's standards are grouped under `spx/43-python.enabler/25-python-standards.enabler/`, with architecture standards, test standards, and implementation workflows separated by dependency order ([audit])
- ALWAYS: the Python plugin's test standards cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the language-neutral seam rules, and the `25-python-standards.enabler` subtree declares only the Python delta ([audit])
- NEVER: the Python plugin's skills teach or recommend `tests/fixtures/`, `tests/support/`, `tests/conftest.py` for fixture bodies, or any inside-`tests/` location for harnesses, generators, or fixture implementations — `conftest.py` may exist as a thin discovery shim for pytest that imports from `product_testing/`, never as a home for fixture body code ([audit])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([audit])
