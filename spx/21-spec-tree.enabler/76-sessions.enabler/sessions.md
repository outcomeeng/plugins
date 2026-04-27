# Sessions

PROVIDES conversation handoff and pickup via timestamped session documents and compact-summary persistence
SO THAT all Claude Code sessions
CAN maintain work continuity without context loss across explicit handoffs and context compaction events

## Assertions

### Scenarios

- Given active work on a spec node, when `/handoff` runs, then a session document is created in `.spx/sessions/todo/` with the current tree state and active node path ([test](tests/test_sessions.unit.py))
- Given a session document in `.spx/sessions/todo/`, when `/pickup` runs, then the session is moved to `.spx/sessions/doing/` and its context is loaded ([test](tests/test_sessions.unit.py))
- Given a session with PLAN.md or ISSUES.md escape hatches, when `/handoff` runs, then the escape hatch contents are included in the session document ([test](tests/test_sessions.unit.py))
- Given `/compact` runs mid-session, when the PostCompact hook fires, then the compact summary is persisted atomically to `.spx/sessions/tmp/compact-<session_id>.md` ([test](tests/test_sessions.unit.py))
- Given a compact summary exists at `.spx/sessions/tmp/compact-<old_id>.md`, when a new session starts, then the SessionStart hook atomically claims it and injects it with a directive to invoke `/handing-off` before responding to any user message ([test](tests/test_sessions.unit.py))

### Compliance

- ALWAYS: store sessions in `.spx/sessions/` — session state is operational, not part of the durable map ([review])
- NEVER: include session state in committed files — sessions are ephemeral conversation artifacts ([review])
- ALWAYS: configure compact summaries to include spec-tree sections (Nodes, Lessons, Skills, Starting Point, Persistence Proposal, Session Scope) via the `compactPrompt` field in a Claude Code settings file — the compact summary is the continuity mechanism for same-session compaction ([review])
- NEVER: create a session file for a compaction event within an ongoing session — the compact summary carries the state; session files are only for cross-session handoffs ([review])
