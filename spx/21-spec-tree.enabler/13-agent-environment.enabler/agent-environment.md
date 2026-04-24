# Agent Environment

PROVIDES a stable per-agent session identity and working directory
SO THAT session management nodes (sessions, applying, committing)
CAN scope work to the current agent without file-system heuristics or race conditions

## Assertions

### Scenarios

- Given a Claude Code session starts, when the `SessionStart` hook fires, then `$CLAUDE_SESSION_ID` is set to the session UUID and persists for all subsequent Bash tool calls in that session ([test](tests/agent-environment.unit.test.sh))
- Given a Codex session starts, when any tool runs, then `$CODEX_THREAD_ID` holds the thread UUID injected by the Codex runtime ([test](tests/agent-environment.unit.test.sh))
- Given the hook fires in a directory containing `.spx/`, when it completes, then `.spx/sessions/<session_id>/` exists ([test](tests/agent-environment.unit.test.sh))
- Given two concurrent agent sessions in the same worktree, when each reads its session identity, then the values are distinct ([test](tests/agent-environment.unit.test.sh))

### Properties

- The session identity is stable: every Bash tool call within the same session observes the same value ([test](tests/agent-environment.unit.test.sh))
- The session directory path is `.spx/sessions/<session_id>/` where `<session_id>` equals the agent session identity — no other naming convention is used ([test](tests/agent-environment.unit.test.sh))

### Compliance

- ALWAYS: resolve session identity from `$CLAUDE_SESSION_ID` (Claude Code) or `$CODEX_THREAD_ID` (Codex) — never infer identity from file modification timestamps, directory enumeration, or index files ([review])
- ALWAYS: create the session directory via the `SessionStart` hook, not lazily on first skill use — the hook is the authoritative setup point and fires on startup, resume, `/clear`, and `/compact` ([review])
- NEVER: read or write another agent's session directory — each agent's scope is limited to `.spx/sessions/<own_session_id>/` ([review])
