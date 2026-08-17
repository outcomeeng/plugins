# Sessions

PROVIDES conversation handoff and pickup via timestamped session documents and compact-summary persistence
SO THAT all Claude Code sessions
CAN maintain work continuity without context loss across explicit handoffs and context compaction events

`spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler` owns the `.spx/sessions/` store and the `spx session` command contract every other concern consumes. `spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler` owns closing a session; `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler` owns resuming one. The assertions below are the compaction contract and the coordination-overlay contract, both cross-cutting: each governs every session concern rather than any one of them.

A repository that follows methodology 4.0.0 coordination (the declaration in `versions/next/11-coordination.md` of `outcomeeng/methodology`, the version `spx.config.yaml` selects) may declare a Change store in `spx/local/coordination.md`. Under that overlay a Change — one issue in the declared store, carrying its Product, its Maturity (`Proposed`, `Framed`, `Sliced`, `Executable`), and a Lifecycle derived from GitHub facts (`Available` open with no assignee, `Claimed` open with one assignee, `Applied`, `Refined`, or `Abandoned` closed with the matching authorized comment) — is the coordination object for one Output, and a Handoff is the newest `Handoff:` comment on that Change. Session documents remain the contract when the overlay is absent.

## Assertions

### Compliance

- ALWAYS: under `spx/local/coordination.md`, `/pickup` and `/handoff` coordinate through the declared Change store — a Change per Output with Product, Maturity, and derived Lifecycle, and a `Handoff:` comment as the continuation — and write no session document; without the overlay the session-document contract applies unchanged ([audit])
- NEVER: a Change body, refinement, or Handoff comment carries a secret value or credential payload ([audit])
- ALWAYS: after compaction, the managed root instruction block requires `/understand` before the next product-content access and `/contextualize` on the governing spec node before any product content it governs is read or modified and before that node is discussed, with a compaction emptying the set of contextualized nodes and an operational continuation — PR inspection, check wait, merge, deploy, release, `spx session` operations, occupancy proof — triggering neither, while the `SessionStart` hook remains limited to delegated session-environment and worktree-occupancy behavior ([audit])
- NEVER: `.claude/settings.json` defines a `compactPrompt` override; Claude Code's standard compact summary remains the state record the resuming agent interprets ([audit])
- NEVER: a compaction event creates a `/handoff` session file — compaction continuity is carried by the standard compact summary and the managed root instruction directive, distinct from the `todo`/`doing`/`archive` handoff queue; a session file is written only by a deliberate `/handoff` ([audit])
