# Python

PROVIDES the complete Python development workflow — architecture, testing, implementation, and review
SO THAT Python projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The python plugin contains 9 skills following the foundational + language-specific pattern: `/standardizing-python` (reference), `/standardizing-python-architecture` (reference), `/standardizing-python-tests` (reference), `/testing-python`, `/coding-python`, `/auditing-python`, `/auditing-python-tests`, `/architecting-python`, `/auditing-python-architecture`. Three auditor agents (`python-code-auditor`, `python-architecture-auditor`, `python-test-auditor`) preload the corresponding skills.

## Assertions

### Compliance

- ALWAYS: follow the foundational + language-specific pattern — core principles in `/testing`, Python-specific patterns in `/testing-python` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- ALWAYS: the Python plugin's testing skills (`/standardizing-python-tests`, `/testing-python`, `/auditing-python-tests`) teach that test infrastructure (harnesses, generators, fixtures) lives at `product_testing/` (`product_testing/harnesses/`, `product_testing/generators/`, `product_testing/fixtures/`) per `spx/15-test-infrastructure.pdr.md` ([review])
- NEVER: the Python plugin's skills teach or recommend `tests/fixtures/`, `tests/support/`, `tests/conftest.py` for fixture bodies, or any inside-`tests/` location for harnesses, generators, or fixture implementations — `conftest.py` may exist as a thin discovery shim for pytest that imports from `product_testing/`, never as a home for fixture body code ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
