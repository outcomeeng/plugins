# Real-Agent Codex Test Selection

The real-agent Codex tests — the fresh-session subagent discovery test and the real-agent bootstrap test — are selected in local changed-path verification, explicit full verification, and CI exactly when a changeset changes agent definitions, and a selected test runs to a verdict on the Codex CLI the host installs. Agent definitions are the authored agent sources under `src/plugins/*/agents/`, their generated renderings under `dist/`, and the code that converts, emits, and places them: the agent conversion and emission code under `outcomeeng/distribution/` and the shipped placement scripts. Direct execution that names a real-agent Codex test runs it whatever the changeset changes.

## Rationale

The real-agent Codex tests prove that the definitions an installation places reach a fresh agent session, and they consume model quota on a host CLI whose version moves outside the repository. Agent definitions are the subject those tests can falsify, so selecting them by agent-definition change keeps their proof on every changeset that can alter what they observe and spares every other changeset the authentication, model use, and host-CLI coupling.

## Product properties

1. A changeset that changes agent definitions selects the real-agent Codex tests in local changed-path verification, explicit full verification, and CI, with the selection reason visible before execution.
2. A changeset that changes no agent definition excludes the real-agent Codex tests from local, explicit full, and CI verification while retaining its complete selected deterministic scope, including when that scope widens automatically to the full deterministic suite.
3. A selected real-agent Codex test requires a successful execution to a verdict; missing or invalid credentials fail visibly without skipping or switching authentication mode.

## Verification

- ALWAYS: local changed-path selection, explicit full verification, and CI full verification select the real-agent Codex tests when the changeset changes an authored agent source, a generated rendering of one, or the code that converts, emits, or places agent definitions.
- NEVER: a changeset that changes no agent definition selects a real-agent Codex test in local changed-path, explicit full, or CI verification — including when its selected deterministic scope widens automatically to the full deterministic suite.
- NEVER: excluding the real-agent Codex tests removes any other step or test from the selected deterministic verification scope.
- ALWAYS: direct execution that names a real-agent Codex test runs that test, whatever the changeset changes.
- ALWAYS: the execution plan displays the reason for including or excluding the real-agent Codex tests before running selected steps.

### Testing

- NEVER: credential availability determines change relevance or turns selected required evidence into a passing skip. ([compliance])
