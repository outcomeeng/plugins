# Issues

## Scenario predicates are hidden in boolean-returning harnesses

Implementation audit `2026-09-14_11-26-09-644-eb39d2a3b433` rejected
`tests/test_build_orchestration.scenario.l1.py:36`: the formatter-version-probe
test asserts a boolean returned by `failing_formatter_version_probe_matches_contract`.
The other scenario tests in that file use the same assertion-delegation pattern.
The test-infrastructure PDR requires predicates in linked tests and observations
from harnesses. Hidden predicates prevent the test file from exposing its oracle.

The audited test file is unchanged by the formatter-version update at
`349e3c3be3f88f496f228666036d6790b5be2a3c`. This records the rejected subject
under the merge policy for audit findings outside the changed files; it supplies
no evidence-audit approval. Settlement requires observation-returning harnesses
and test-owned predicates across this file, followed by a passing evidence audit.
Revisit before relying on this node's evidence-audit approval or changing these tests.
