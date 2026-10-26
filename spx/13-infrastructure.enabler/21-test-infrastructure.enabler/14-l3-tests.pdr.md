# L3 Tests

Every test whose file name carries the execution level `l3` is an L3 test. The gates skip them, and `just test-l3` runs them.

## Rationale

Evidence at level `l3` depends on remote, shared, or credentialed systems, and a run spends the credentials and capacity of whoever starts it. A gate that ran them would spend those on every changeset, so the gates skip the L3 tests, and one explicit command runs them when a maintainer asks for them. The file name already carries the level, so one selector serves every gate and direct execution.

## Product properties

1. A maintainer who runs `just check`, `just check-full`, or `just verify-marketplace-installation` meets no L3 test, and each plan names that skip and its reason.
2. `just test-l3` runs every L3 test and no other test, and `just test` naming an L3 file runs it.
3. Every run of an L3 test reaches a verdict, with missing credentials failing visibly.
4. The repository calls these tests L3 tests and names their command `just test-l3`, and no other name for the suite appears in any file.

## Verification

### Testing

- l3-tests: Every test whose file name carries the execution level `l3` is an L3 test. ([mapping])
- local-skip: `just check`, `just check-full`, and `just verify-marketplace-installation` run no L3 test, whatever the changeset changes, and each plan names that skip and its reason before any step runs. ([compliance])
- l3-command: `just test-l3` runs every L3 test and no other test, and `just test` naming an L3 file runs it. ([mapping])
- skip-scope: The local skip removes no test or step outside the L3 tests from any selected or full scope, including when local selection widens to the full deterministic suite. ([compliance])
- l3-term: The repository names the tests at execution level `l3` "L3 tests" and their command `just test-l3`, and no file in the repository carries the words "on" and "demand" joined by a hyphen, by an underscore, or directly, in any letter case. ([compliance])

### Audit

- l3-verdict: Every run of an L3 test requires it to reach a verdict; missing or invalid credentials fail visibly, without a skip and without switching authentication mode. ([audit:l3-credential-failure])
