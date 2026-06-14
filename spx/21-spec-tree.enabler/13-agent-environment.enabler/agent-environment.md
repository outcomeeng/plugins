# Agent Environment

PROVIDES a stable per-agent session identity and a working directory whose base currency against the default branch is surfaced at session start
SO THAT session management nodes (sessions, applying, committing)
CAN scope work to the current agent and begin on a current base, without file-system heuristics, race conditions, or stale-base rework

## Assertions

### Scenarios

- Given a Claude Code session starts, when the `SessionStart` hook fires, then `$CLAUDE_SESSION_ID` is written to the harness env file as the session UUID so every subsequent Bash tool call in that session reads it ([test](tests/test_agent_environment.scenario.l1.py))
- Given a Claude Code session starts in a directory containing `.spx/`, when the `SessionStart` hook completes, then no per-runtime session directory is created — `.spx/sessions/<session_id>/` exists only after `spx session pickup` lazily creates it on first successful claim ([test](tests/test_agent_environment.scenario.l1.py))
- Given a `SessionStart` payload whose project directory is a git worktree behind its resolved default branch, when the hook runs, then stdout carries a `<SPEC-TREE_SESSION_START .../>` directive naming the behind-count and the resolved default branch and instructing the agent to fetch and rebase onto it, never reset ([test](tests/test_agent_environment.scenario.l1.py))

### Mappings

- A worktree base state maps to the hook's staleness output: behind the resolved default by N (N greater than zero) maps to a `<SPEC-TREE_SESSION_START>` directive carrying N; current with the default maps to no directive; a non-git directory or an unresolvable default maps to no directive and a zero exit ([test](tests/test_agent_environment.mapping.l1.py))
- A `SessionStart` payload maps to the identity write: distinct session UUIDs map to distinct `$CLAUDE_SESSION_ID` writes, and a missing or empty `session_id` maps to no export ([test](tests/test_agent_environment.mapping.l1.py))

### Properties

- For any session UUID, the env file receives that identity as `$CLAUDE_SESSION_ID` with surrounding whitespace trimmed — the value round-trips through the hook's shell-quoting otherwise unchanged ([test](tests/test_agent_environment.property.l1.py))
- The hook writes the session identity deterministically: repeated `SessionStart` events with the same payload produce the same `$CLAUDE_SESSION_ID` export line, so every Bash tool call in the session reads one stable value ([test](tests/test_agent_environment.property.l1.py))

### Compliance

- ALWAYS: the `SessionStart` hook resolves the default branch from git's configured default (`origin/HEAD`), never a literal `origin/main` ([test](tests/test_agent_environment.compliance.l1.py))
- ALWAYS: the base-staleness check is read-only — the hook runs no `git fetch` and no state-mutating git command, and HEAD and refs are unchanged after it runs ([test](tests/test_agent_environment.compliance.l1.py))
- ALWAYS: resolve session identity from `$CLAUDE_SESSION_ID` (Claude Code) or `$CODEX_THREAD_ID` (Codex) — never infer identity from file modification timestamps, directory enumeration, or index files ([review])
- ALWAYS: two concurrent sessions resolve distinct identities — the runtime assigns each session a unique id, and the hook writes what the payload supplies rather than generating uniqueness ([review])
- ALWAYS: create the per-runtime session directory lazily on first `spx session pickup` claim, not in the `SessionStart` hook, at the path `.spx/sessions/<session_id>/` where `<session_id>` is the agent session identity — no other naming convention is used ([review])
- ALWAYS: the `SessionStart` hook's only direct filesystem write is the harness-provided `$CLAUDE_ENV_FILE`; base-staleness is surfaced through stdout context injection, and all `.spx/` state stays owned by the `spx` CLI ([review])
- ALWAYS: under Codex, session identity is the runtime-injected `$CODEX_THREAD_ID` — the Claude Code `SessionStart` hook does not run, and no marketplace code sets it ([review])
- NEVER: read or write another agent's session directory — each agent's scope is limited to `.spx/sessions/<own_session_id>/` ([review])
