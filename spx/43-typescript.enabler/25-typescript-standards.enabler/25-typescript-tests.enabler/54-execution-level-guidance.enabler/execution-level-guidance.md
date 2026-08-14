# Execution Level Guidance

PROVIDES the TypeScript expression of the neutral execution-level semantics
SO THAT TypeScript test authors
CAN choose `l1`, `l2`, or `l3` through TypeScript's tools and dependency surfaces without re-deriving the neutral level rules

## Assertions

### Compliance

- ALWAYS: TypeScript execution-level specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` for the neutral execution-level semantics — the level definitions, runner independence, lowest-level selection, the level floor, and fail-loud evidence availability — and declare only the TypeScript delta ([audit])
- ALWAYS: the TypeScript expression of the levels: `l1` covers pure functions, cheap temporary filesystem work, standard repository-required tools, and dependency-injected controlled implementations under a recorded exception; `l2` covers Docker containers, local databases or queues, local dev servers, browsers against local services, and product binaries installed during bootstrap; `l3` covers remote, shared, credentialed, or network-dependent systems ([audit])
- ALWAYS: level documentation names files by operational meaning, such as `l1-local-deterministic.md`, `l2-local-infrastructure.md`, and `l3-remote-credentialed.md` — filenames describe the level rather than repeating the level token ([audit])
- ALWAYS: Playwright or browser execution receives a runner token when it uses a non-default runner, while its level still derives from the neutral semantics ([audit])
- ALWAYS: level examples obey source-testability and test-data ownership rules — execution level does not permit copied literals, constant-only generators, or replacement mocks ([audit])
- NEVER: let missing mandatory credentials, base URLs, binaries, or local services produce a passing test — TypeScript suites realize the neutral fail-loud rule through loud failure or an explicit optional-evidence skip marker ([audit])
