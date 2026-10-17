# Python

PROVIDES the complete Python development workflow — architecture, testing, implementation, and review
SO THAT Python projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The python plugin contains 9 skills: `/python-code-standards` (reference), `/python-architecture-standards` (reference), `/python-test-standards` (reference), `/author-python-test`, `/author-python-code`, `/audit-python-code`, `/audit-python-test`, `/author-python-architecture`, `/audit-python-architecture`. The `audit-python-{code|test|architecture}` skills carry no Python-specific auditor agent; `implementation-auditor` composes all three, `adr-auditor` composes `audit-python-architecture`, and `test-evidence-auditor` composes `audit-python-test`, per [`spx/21-spec-tree.enabler/17-audit.adr.md`](spx/21-spec-tree.enabler/17-audit.adr.md).

## Assertions

### Compliance

- ALWAYS: the `audit-python-{code|test|architecture}` skills carry no Python-specific auditor agent, name no caller, and stay invocable on their own; `implementation-auditor`, `adr-auditor` and `test-evidence-auditor` compose them, and the author-context isolation an audit verdict requires binds the author context per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) ([audit])
- ALWAYS: `/test` carries the core testing principles and `/author-python-test` the Python-specific patterns ([audit])
- ALWAYS: the Python plugin's standards are grouped under `spx/43-python.enabler/25-python-standards.enabler/`, with architecture standards, test standards, and implementation workflows separated by dependency order ([audit])
- ALWAYS: the Python plugin's test standards cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and [`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md) for the language-neutral seam rules, and the `25-python-standards.enabler` subtree declares only the Python delta ([audit])
- NEVER: the Python plugin's skills teach or recommend `tests/fixtures/`, `tests/support/`, `tests/conftest.py` for fixture bodies, or any inside-`tests/` location for harnesses, generators, or fixture implementations — `conftest.py` may exist as a thin discovery shim for pytest that imports from `product_testing/`, never as a home for fixture body code ([audit])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([audit])
