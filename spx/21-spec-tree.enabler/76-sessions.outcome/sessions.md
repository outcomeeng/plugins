# Sessions

WE BELIEVE THAT conversation handoff and pickup via timestamped session documents
WILL enable work continuity across Claude Code sessions without context loss
CONTRIBUTING TO uninterrupted development flow and reduced context re-discovery time

The `/handoff` command creates a timestamped session document capturing tree state, active work, and deferred items. The `/pickup` command loads a session and resumes work. Sessions are stored in `.spx/sessions/` (gitignored, separate from the spec tree).

## Assertions

### Scenarios

- Given active work on a spec node, when `/handoff` runs, then a session document is created in `.spx/sessions/todo/` with the current tree state and active node path ([test](tests/test_sessions.unit.py))
- Given a session document in `.spx/sessions/todo/`, when `/pickup` runs, then the session is moved to `.spx/sessions/doing/` and its context is loaded ([test](tests/test_sessions.unit.py))
- Given a session with PLAN.md or ISSUES.md escape hatches, when `/handoff` runs, then the escape hatch contents are included in the session document ([test](tests/test_sessions.unit.py))

### Compliance

- ALWAYS: store sessions in `.spx/sessions/` — session state is operational, not part of the durable map ([review])
- NEVER: include session state in committed files — sessions are ephemeral conversation artifacts ([review])
