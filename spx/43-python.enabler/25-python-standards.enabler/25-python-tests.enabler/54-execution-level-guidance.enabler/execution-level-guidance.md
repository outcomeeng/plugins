# Execution Level Guidance

PROVIDES Python execution-level guidance for local deterministic, local infrastructure, and remote credentialed evidence
SO THAT Python test authors
CAN choose `l1`, `l2`, or `l3` from evidence cost and dependency availability rather than runner names or implementation layers

## Assertions

### Compliance

- ALWAYS: `l1` Python guidance applies to deterministic local evidence, including pure functions, cheap temporary filesystem work, standard repository-required tools, and dependency-injected Stage 5 doubles — local determinism is the deciding property ([audit])
- ALWAYS: `l2` Python guidance applies to real local infrastructure, including Docker containers, local databases or queues, local dev servers, browsers against local services, and product binaries installed during bootstrap — heavier local setup remains local evidence ([audit])
- ALWAYS: `l3` Python guidance applies only to remote, shared, credentialed, or network-dependent systems that cannot be reproduced through local real infrastructure — remote evidence is selected by necessity ([audit])
- ALWAYS: level documentation names files by operational meaning, such as `l1-local-deterministic.md`, `l2-local-infrastructure.md`, and `l3-remote-credentialed.md` — filenames describe the level rather than repeating the level token ([audit])
- ALWAYS: pytest, Playwright, or another runner receives a runner token when it is not the default runner, while its level still comes from infrastructure cost and dependency availability — runner choice does not determine level ([audit])
- ALWAYS: level examples obey source-testability and test-data ownership rules — execution level does not permit copied literals, constant-only generators, replacement mocks, or `conftest.py` fixture-body laundering ([audit])
- NEVER: escalate a test to `l3` because a flow feels end-to-end when equivalent evidence is available with local real infrastructure — evidence uses the lowest level that proves the assertion ([audit])
- NEVER: let missing mandatory credentials, base URLs, binaries, or local services produce a passing test — unavailable required evidence fails loudly or is skipped only when the suite marks the evidence optional ([audit])
