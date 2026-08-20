# Identity

PROVIDES a stable per-agent session identity written into the agent's environment at session start
SO THAT session management nodes and the per-runtime session directory
CAN scope work to the current agent without file-system heuristics or race conditions

## Assertions

### Scenarios

- Given a Claude Code session starts, when the `SessionStart` hook fires, then `$CLAUDE_SESSION_ID` is written to the harness env file as the session UUID so every subsequent Bash tool call in that session reads it ([test](tests/test_identity.scenario.l1.py))

### Properties

- Every UUID-form `session_id` in a `SessionStart` payload is exported exactly as `$CLAUDE_SESSION_ID` ([test](tests/test_identity.property.l1.py))

### Mappings

- A `SessionStart` payload with a missing or empty `session_id` maps to no `$CLAUDE_SESSION_ID` export ([test](tests/test_identity.mapping.l1.py))

### Compliance

- ALWAYS: resolve session identity from the variable the running agent publishes — `$CLAUDE_CODE_SESSION_ID` under Claude Code and under Pi, whose Claude-Code-compatible surface publishes it alongside its own `$PI_SESSION_ID` with the same value, and `$CODEX_THREAD_ID` under Codex — never by inferring identity from file modification timestamps, directory enumeration, or index files ([audit])
- ALWAYS: two concurrent sessions resolve distinct identities — the agent assigns each session a unique id, and every consumer reads what the agent published rather than generating uniqueness ([audit])
- ALWAYS: every agent that consumes a plugin surface publishes its own session identity and no marketplace code sets it — Claude Code publishes `$CLAUDE_CODE_SESSION_ID`, Pi publishes `$PI_SESSION_ID` and the Claude-Code-compatible `$CLAUDE_CODE_SESSION_ID`, and Codex publishes `$CODEX_THREAD_ID` — so an agent that gains a plugin surface declares its published variable here ([audit])
