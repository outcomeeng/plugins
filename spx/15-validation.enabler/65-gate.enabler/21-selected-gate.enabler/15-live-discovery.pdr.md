# Live Discovery Selection

Live discovery is the two real-agent Codex tests: the fresh-session subagent discovery test and the real-agent bootstrap test. Both are L3 tests under [`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md), so CI runs them on every pull request, `just check` and `just check-full` never select them, and direct execution that names a live-discovery test runs it.

## Rationale

The real-agent Codex tests prove that the definitions an installation places reach a fresh agent session, and they consume model quota on a host CLI whose version moves outside the repository. Their file carries the execution level `l3`, so the one rule that serves every L3 test serves them: CI runs them with the repository's credentials on every pull request, and a maintainer runs them locally through `just test-l3` with their own.

## Product properties

1. CI runs every live-discovery test on every pull request, and `just check` and `just check-full` select none, whatever the changeset changes.
2. A maintainer who runs `just test-l3`, or names a live-discovery test directly, runs it to a verdict on the Codex CLI the host installs.

## Verification

### Testing

- live-discovery-selection: The real-agent Codex tests, the fresh-session subagent discovery test and the real-agent bootstrap test, are L3 tests under [`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-l3-tests.pdr.md), so CI runs them on every pull request, and local verification runs them only through `just test-l3` or a direct target. ([compliance])
