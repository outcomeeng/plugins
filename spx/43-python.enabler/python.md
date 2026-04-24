# Python

PROVIDES the complete Python development workflow — architecture, testing, implementation, and review
SO THAT Python projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The python plugin contains 9 skills following the foundational + language-specific pattern: `/standardizing-python` (reference), `/standardizing-python-architecture` (reference), `/standardizing-python-tests` (reference), `/testing-python`, `/coding-python`, `/auditing-python`, `/auditing-python-tests`, `/architecting-python`, `/auditing-python-architecture`. Three auditor agents (`python-code-auditor`, `python-architecture-auditor`, `python-test-auditor`) preload the corresponding skills.

## Assertions

### Compliance

- ALWAYS: follow the foundational + language-specific pattern — core principles in `/testing`, Python-specific patterns in `/testing-python` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
