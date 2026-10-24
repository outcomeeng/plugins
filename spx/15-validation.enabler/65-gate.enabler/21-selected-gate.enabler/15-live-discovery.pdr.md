# Live Discovery Selection

Live discovery is the two real-agent Codex tests: the fresh-session subagent discovery test and the real-agent bootstrap test. Both belong to the on-demand suite that [`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md) declares, and no changeset selects them into local, full, or CI verification. Direct execution that names a live-discovery test runs it, whatever the changeset changes.

## Rationale

The real-agent Codex tests prove that the definitions an installation places reach a fresh agent session, and they consume model quota on a host CLI whose version moves outside the repository. Their file carries the execution level `l3`, so the one exclusion that serves every on-demand test serves them, and one explicit command runs them with the maintainer's own credentials.

## Product properties

1. Local changed-path verification, explicit full verification, and CI select no live-discovery test, whatever the changeset changes.
2. A maintainer who runs the on-demand suite, or names a live-discovery test directly, runs it to a verdict on the Codex CLI the host installs.

## Verification

### Testing

- live-discovery-selection: The real-agent Codex tests, the fresh-session subagent discovery test and the real-agent bootstrap test, belong to the on-demand suite that [`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md) declares, and no changeset selects them into local, full, or CI verification. ([compliance])
