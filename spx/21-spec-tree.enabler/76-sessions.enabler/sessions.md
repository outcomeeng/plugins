# Sessions

PROVIDES conversation handoff and pickup via timestamped session documents and compact-summary persistence
SO THAT all Claude Code sessions
CAN maintain work continuity without context loss across explicit handoffs and context compaction events

## Assertions

### Scenarios

- Given active work on a spec node, when `/handoff` runs, then a session document is created in `.spx/sessions/todo/` with the current tree state and active node path ([test](tests/test_sessions.scenario.l1.py))
- Given a session document in `.spx/sessions/todo/`, when `/pickup` runs, then the session is moved to `.spx/sessions/doing/` and its content is emitted to stdout for context loading ([test](tests/test_sessions.scenario.l1.py))
- Given escape hatch content is included in the session payload, when the session document is created, then that content appears verbatim in the stored session file ([test](tests/test_sessions.scenario.l1.py))
- Given `/compact` runs mid-session, when the PostCompact hook fires, then the compact summary is persisted atomically to `.spx/sessions/tmp/compact-<session_id>.md` ([test](tests/test_sessions.scenario.l1.py))

### Conformance

- The `compactPrompt` in `.claude/settings.json` contains all six state-schema section headers (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) ([test](tests/test_sessions.conformance.l1.py))
- Given a compact summary exists at `.spx/sessions/tmp/compact-<old_id>.md`, when a new session starts, then the SessionStart hook claims it, injects it as context, emits a re-anchoring directive that invokes `/spec-tree:understanding` (when the foundation marker was active pre-compact) and `/spec-tree:contextualizing` on the recorded active node, and appends a `<COMPACT_RESUMED at="..."/>` marker ([test](tests/test_sessions.scenario.l1.py))

### Compliance

- ALWAYS: the `/handoff` skill reads PLAN.md and ISSUES.md from the active node directory and includes their content in the session payload — escape hatch content must not be silently omitted ([review])
- ALWAYS: store sessions in `.spx/sessions/` — session state is operational, not part of the durable map ([review])
- NEVER: include session state in committed files — sessions are ephemeral conversation artifacts ([review])
- ALWAYS: configure the `compactPrompt` field to append state-schema sections (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) to Claude Code's base summarization prompt — base-prompt-forced sections (Pending Tasks, Current Work, Optional Next Step) are accepted as residual; the schema sections are spec-tree's contribution ([review])
- NEVER: add imperative sections via the `compactPrompt` configuration ("next step", "persistence proposal", "starting point") — those compound residual imperatives in base-prompt-forced sections that the marketplace cannot remove ([review])
- NEVER: name specific skill invocations inside the `compactPrompt` configuration — skill choice belongs to the SessionStart hook directive, not to summary text the agent reads as self-direction ([review])
- NEVER: create a session file for a compaction event within an ongoing session — the compact summary carries the state; session files are only for cross-session handoffs ([review])
