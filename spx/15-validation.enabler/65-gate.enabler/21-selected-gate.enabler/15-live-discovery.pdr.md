# Live Discovery Selection

Live discovery is the two real-agent Codex tests: the fresh-session subagent discovery test and the real-agent bootstrap test. Local changed-path verification, explicit full verification, and CI select live discovery exactly when a changeset changes an agent definition, and a selected test runs to a verdict on the Codex CLI the host installs. An agent definition is an authored agent source, a rendering of one, or the code that converts, profiles, emits, or places agent definitions, the shipped placement script and its renderings included. A changeset that changes no agent definition excludes live discovery while it keeps its complete selected deterministic scope, including when that scope widens automatically to the full deterministic suite, and the exclusion removes no other step or test. Direct execution that names a live-discovery test runs it, whatever the changeset changes.

## Rationale

The real-agent Codex tests prove that the definitions an installation places reach a fresh agent session, and they consume model quota on a host CLI whose version moves outside the repository. Agent definitions are the subject those tests can falsify, so selecting them by agent-definition change keeps their proof on every changeset that can alter what they observe and spares every other changeset the authentication, model use, and host-CLI coupling. The selection lives in this decision because a maintainer running local verification notices it: a selected live check spends that maintainer's model quota and needs that maintainer's credentials.

## Product properties

1. Local changed-path verification, explicit full verification, and CI include live discovery exactly for a changeset that changes an agent definition, with the selection reason visible before execution.
2. A changeset that changes no agent definition retains its complete selected deterministic scope while excluding live discovery, including when that scope widens automatically to the full deterministic suite; direct execution that names a live-discovery test runs it.
3. A selected live check requires a successful execution; missing or invalid credentials fail visibly without skipping or switching authentication mode.

## Verification

### Testing

- ALWAYS: local changed-path, explicit full, and CI verification select live discovery exactly for a changeset that changes an agent definition, and a selected test runs to a verdict ([compliance])
- ALWAYS: direct execution that names a live-discovery test runs it, whatever the changeset changes ([compliance])
- NEVER: a changeset that changes no agent definition selects live discovery, including through automatic full-suite escalation, or loses any other step or test to the exclusion ([compliance])
- ALWAYS: the execution plan displays the reason for including or excluding live discovery before running selected steps. ([compliance])
- NEVER: credential availability determines change relevance or turns selected required evidence into a passing skip. ([compliance])
