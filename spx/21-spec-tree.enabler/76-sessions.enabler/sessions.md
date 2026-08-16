# Sessions

PROVIDES conversation handoff and pickup via timestamped session documents and compact-summary persistence
SO THAT all Claude Code sessions
CAN maintain work continuity without context loss across explicit handoffs and context compaction events

`spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler` owns the `.spx/sessions/` store and the `spx session` command contract every other concern consumes. `spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler` owns closing a session; `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler` owns resuming one. The assertions below are the compaction contract, which is cross-cutting: it governs every session concern rather than any one of them.

## Assertions

### Compliance

- ALWAYS: after compaction, the managed root instruction block requires `/understand` before the next implementation access and `/contextualize` on the governing spec node before any implementation it governs is read or modified and before that node is discussed, with a compaction emptying the set of contextualized nodes and an operational continuation — PR inspection, check wait, merge, deploy, release, `spx session` operations, occupancy proof — triggering neither, while the `SessionStart` hook remains limited to delegated session-environment and worktree-occupancy behavior ([audit])
- NEVER: `.claude/settings.json` defines a `compactPrompt` override; Claude Code's standard compact summary remains the state record the resuming agent interprets ([audit])
- NEVER: a compaction event creates a `/handoff` session file — compaction continuity is carried by the standard compact summary and the managed root instruction directive, distinct from the `todo`/`doing`/`archive` handoff queue; a session file is written only by a deliberate `/handoff` ([audit])
