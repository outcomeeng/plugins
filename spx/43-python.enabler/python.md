# Python

PROVIDES the complete Python development workflow — architecture, testing, implementation, and review
SO THAT Python projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The python plugin contains 9 skills following the foundational + language-specific pattern: `/python-standards` (reference), `/python-architecture-standards` (reference), `/python-test-standards` (reference), `/test-python`, `/code-python`, `/audit-python-code`, `/audit-python-tests`, `/architect-python`, `/audit-python-architecture`. The `audit-python-{code|tests|architecture}` skills carry no Python-specific auditor agent; the generic artifact-type auditors compose them for the Python concerns in scope. `implementation-auditor` composes the code, test, and architecture concern skills for implementation audits; `adr-auditor` and `test-evidence-auditor` compose the matching concern skills for decision and test-evidence audits, per `spx/21-spec-tree.enabler/17-audit.adr.md`.

## Assertions

### Compliance

- ALWAYS: the `audit-python-{code|tests|architecture}` skills carry no Python-specific auditor agent and are composed by the generic artifact-type auditor for the Python concerns in scope; the main conversation does not invoke them in place — the dispatched verifier's isolated context produces the verdict, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, Python-specific patterns in `/test-python` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- ALWAYS: the Python plugin's standards are grouped under `spx/43-python.enabler/25-python-standards.enabler/`, with architecture standards, test standards, and implementation workflows separated by dependency order ([review])
- ALWAYS: the Python plugin's testing skills (`/python-test-standards`, `/test-python`, `/audit-python-tests`) teach the `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` contract: source contracts come first, test infrastructure lives in the importable `<package>_testing/` package, generators vary, fixtures stay inert, harnesses manage resources, and audits inspect the full test-infrastructure chain ([review])
- NEVER: the Python plugin's skills teach or recommend `tests/fixtures/`, `tests/support/`, `tests/conftest.py` for fixture bodies, or any inside-`tests/` location for harnesses, generators, or fixture implementations — `conftest.py` may exist as a thin discovery shim for pytest that imports from `<package>_testing/`, never as a home for fixture body code ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
