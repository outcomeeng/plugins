# Identity

PROVIDES a stable per-agent session identity written into the agent's environment at session start
SO THAT session management nodes and the per-runtime session directory
CAN scope work to the current agent without file-system heuristics or race conditions

`spx hooks session-start`, invoked directly by the runtime, writes the session identity into the harness-provided `$CLAUDE_ENV_FILE` per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`.

## Assertions

### Scenarios

- Given a Claude Code session starts, when `spx hooks session-start` fires, then `$CLAUDE_SESSION_ID` is written to the harness env file as the session UUID so every subsequent Bash tool call in that session reads it ([test](tests/test_identity.scenario.l1.py))

### Mappings

- A `SessionStart` payload maps to the identity write: distinct session UUIDs map to distinct `$CLAUDE_SESSION_ID` writes, and a missing or empty `session_id` maps to no export ([test](tests/test_identity.mapping.l1.py))

### Properties

- For any session UUID, the env file receives that identity as `$CLAUDE_SESSION_ID` with surrounding whitespace trimmed — the value round-trips through the env-file quoting otherwise unchanged ([test](tests/test_identity.property.l1.py))
- The identity write is deterministic: repeated `SessionStart` events with the same payload produce the same `$CLAUDE_SESSION_ID` export line, so every Bash tool call in the session reads one stable value ([test](tests/test_identity.property.l1.py))

### Compliance

- ALWAYS: resolve session identity from `$CLAUDE_SESSION_ID` (Claude Code) or `$CODEX_THREAD_ID` (Codex) — never infer identity from file modification timestamps, directory enumeration, or index files ([review])
- ALWAYS: two concurrent sessions resolve distinct identities — the runtime assigns each session a unique id, and `spx hooks session-start` writes what the payload supplies rather than generating uniqueness ([review])
- ALWAYS: under Codex, session identity is the runtime-injected `$CODEX_THREAD_ID` — the Claude Code `SessionStart` hook does not run, and no marketplace code sets it ([review])
