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

- ALWAYS: resolve session identity from `$CLAUDE_SESSION_ID` (Claude Code) or `$CODEX_THREAD_ID` (Codex) — never infer identity from file modification timestamps, directory enumeration, or index files ([audit])
- ALWAYS: two concurrent sessions resolve distinct identities — the runtime assigns each session a unique id, and the hook writes what the payload supplies rather than generating uniqueness ([audit])
- ALWAYS: under Codex, session identity is the runtime-injected `$CODEX_THREAD_ID` — the Claude Code `SessionStart` hook does not run, and no marketplace code sets it ([audit])
