# On-Demand Test Suite

Every test whose file name carries the execution level `l3` forms the on-demand suite. Default verification never runs the suite, and one explicit command does.

## Rationale

Evidence at level `l3` depends on remote, shared, or credentialed systems, so each run spends credentials and capacity that the default verification of every changeset must not spend. The file name already carries the level, so one selector serves every gate, CI, and direct execution. Selecting by changed paths instead needs a second mechanism for each such test and repeats the cost on every changeset that touches those paths.

## Product properties

1. A maintainer who runs local, full, or CI verification meets no test of the on-demand suite, and each plan names that exclusion and its reason.
2. One explicit command runs the whole on-demand suite and no other test.
3. An on-demand run reaches a verdict for every test, with missing credentials failing visibly.

## Verification

### Testing

- on-demand-suite: Every test whose file name carries the execution level `l3` belongs to the on-demand suite. ([mapping])
- default-exclusion: `just check`, `just check-full`, CI, and `just verify-marketplace-installation` never run a test of the on-demand suite, whatever the changeset changes, and each plan names that exclusion and its reason before any step runs. ([compliance])
- on-demand-command: One explicit command runs every test of the on-demand suite and no other test, and direct execution that names an on-demand test runs it. ([mapping])
- exclusion-scope: The exclusion removes no test or step outside the on-demand suite from any selected or full scope, including when local selection widens to the full deterministic suite. ([compliance])

### Audit

- on-demand-verdict: An on-demand run requires each test to reach a verdict; missing or invalid credentials fail visibly, without a skip and without switching authentication mode. ([audit:on-demand-credential-failure])
