# Agent Environment

PROVIDES a stable per-agent session identity, a per-runtime session directory keyed on it, and a session-start signal when the working directory trails its default branch
SO THAT session management nodes (sessions, applying, committing)
CAN scope work to the current agent and begin on a current base, without file-system heuristics, race conditions, or stale-base rework

This node holds only the hook-wide write-discipline constraint that spans its children.

## Assertions

### Compliance

- ALWAYS: the `SessionStart` hook's only direct filesystem write is the harness-provided `$CLAUDE_ENV_FILE`; base-staleness is surfaced through stdout context injection, and all `.spx/` state stays owned by the `spx` CLI ([review])
