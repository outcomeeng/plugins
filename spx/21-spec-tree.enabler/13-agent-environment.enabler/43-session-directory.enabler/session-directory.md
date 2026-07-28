# Session Directory

PROVIDES the per-runtime session directory convention keyed on the agent session identity
SO THAT session management nodes (sessions, pickup, handoff)
CAN accumulate per-session state without colliding across concurrent agents

## Assertions

### Scenarios

- Given a Claude Code session starts in a directory containing `.spx/`, when the `SessionStart` hook completes, then no per-runtime session directory is created — `.spx/sessions/<session_id>/` exists only after `spx session pickup` lazily creates it on first successful claim ([test](tests/test_session_directory.scenario.l1.py))

### Compliance

- ALWAYS: create the per-runtime session directory lazily on first `spx session pickup` claim, not in the `SessionStart` hook, at the path `.spx/sessions/<session_id>/` where `<session_id>` is the agent session identity — no other naming convention is used ([audit])
- NEVER: read or write another agent's session directory — each agent's scope is limited to `.spx/sessions/<own_session_id>/` ([audit])
