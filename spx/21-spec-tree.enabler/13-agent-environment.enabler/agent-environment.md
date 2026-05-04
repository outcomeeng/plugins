# Agent Environment

PROVIDES a stable per-agent session identity and working directory
SO THAT session management nodes (sessions, applying, committing)
CAN scope work to the current agent without file-system heuristics or race conditions

## Assertions

### Scenarios

- Given a Claude Code session starts, when the `SessionStart` hook fires, then `$CLAUDE_SESSION_ID` is set to the session UUID and persists for all subsequent Bash tool calls in that session ([test](tests/test_agent_environment.scenario.l1.py))
- Given a Codex session starts, when any tool runs, then `$CODEX_THREAD_ID` holds the thread UUID injected by the Codex runtime ([test](tests/test_agent_environment.scenario.l1.py))
- Given two concurrent agent sessions in the same worktree, when each reads its session identity, then the values are distinct ([test](tests/test_agent_environment.scenario.l1.py))
- Given a Claude Code session starts in a directory containing `.spx/`, when the `SessionStart` hook completes, then no per-runtime session directory is created — `.spx/sessions/<session_id>/` exists only after `spx session pickup` lazily creates it on first successful claim ([test](tests/test_agent_environment.scenario.l1.py))

### Properties

- The session identity is stable: every Bash tool call within the same session observes the same value ([test](tests/test_agent_environment.property.l1.py))
- Per-runtime session directories use the path `.spx/sessions/<session_id>/` where `<session_id>` equals the agent session identity — no other naming convention is used ([test](tests/test_agent_environment.property.l1.py))

### Compliance

- ALWAYS: resolve session identity from `$CLAUDE_SESSION_ID` (Claude Code) or `$CODEX_THREAD_ID` (Codex) — never infer identity from file modification timestamps, directory enumeration, or index files ([review])
- ALWAYS: create the per-runtime session directory lazily on first `spx session pickup` claim, not in the `SessionStart` hook — eager creation in the hook leaves empty directories for conversations that never claim a session ([review])
- NEVER: read or write another agent's session directory — each agent's scope is limited to `.spx/sessions/<own_session_id>/` ([review])
