# On-Demand Test Suite

Every test whose file name carries the execution level `l3` belongs to the on-demand suite. The suite runs only when an operator asks for it: `just check`, `just check-full`, CI, and `just verify-marketplace-installation` never run a test of the suite, and one explicit command runs all of it.

## Rationale

An `l3` test exercises real external systems, such as a real agent session under a real login, so each run costs time and quota. Repeating that cost in every local gate, every pull request, and every scheduled run is too expensive, while the tests keep their value as evidence an operator gathers deliberately. The execution level already sits in the test file name, which selects the suite without a second marker, so one rule serves every runner that collects tests.

## Product properties

1. The on-demand suite is exactly the tests whose file names carry the level segment `l3`, and every default verification path leaves it out and says so.
2. One explicit command runs the suite, and direct execution that names an on-demand test runs that test.
3. An on-demand run reaches a verdict for every test it selects, and the exclusion removes nothing outside the suite from any scope.

## Verification

- ALWAYS: every test whose file name carries the execution level `l3` belongs to the on-demand suite
- NEVER: `just check`, `just check-full`, CI, and `just verify-marketplace-installation` run a test of the on-demand suite, whatever the changeset changes
- ALWAYS: each gate plan names the exclusion of the on-demand suite and its reason before any step runs
- ALWAYS: one explicit command runs every test of the on-demand suite and no other test, and direct execution that names an on-demand test runs it
- NEVER: the exclusion of the on-demand suite removes a test or step outside the suite from any selected or full scope, including when local selection widens to the full deterministic suite
- ALWAYS: an on-demand run requires each test to reach a verdict; missing or invalid credentials fail visibly, without a skip and without switching authentication mode
