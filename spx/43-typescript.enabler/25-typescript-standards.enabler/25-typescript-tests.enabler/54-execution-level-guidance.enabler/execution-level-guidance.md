# Execution Level Guidance

PROVIDES the TypeScript expression of the neutral execution-level semantics
SO THAT TypeScript test authors
CAN choose `l1`, `l2`, or `l3` through TypeScript's tools and dependency surfaces without re-deriving the neutral level rules

## Assertions

### Compliance

- ALWAYS: TypeScript execution-level specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` for the neutral execution-level semantics — the level definitions, runner independence, lowest-level selection, the level floor, and fail-loud evidence availability — and declare only the TypeScript delta ([audit])
- ALWAYS: TypeScript execution-level guidance realizes the neutral levels through TypeScript tooling — Vitest processes for `l1` deterministic work, dependency-injected Stage 5 collaborators behind typed interfaces at `l1`, Playwright browsers against local services at `l2`, credentialed Playwright targets at `l3` — and never restates the neutral category lists, whose semantics derive from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` ([audit])
- ALWAYS: level documentation names files by operational meaning, such as `l1-local-deterministic.md`, `l2-local-infrastructure.md`, and `l3-remote-credentialed.md` — filenames describe the level rather than repeating the level token ([audit])
- ALWAYS: Playwright or browser execution receives a runner token when it uses a non-default runner, while its level still derives from the neutral semantics ([audit])
- ALWAYS: level examples obey source-testability and test-data ownership rules — execution level does not permit copied literals, constant-only generators, or replacement mocks ([audit])
- NEVER: let missing mandatory credentials, base URLs, binaries, or local services produce a passing test — a TypeScript suite realizes the optional-evidence skip only through the runner's explicit skip API (`test.skip`/`it.skip`, or `test.fixme` under Playwright) on evidence the suite declares optional ([audit])
