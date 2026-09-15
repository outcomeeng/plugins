# Sessions

PROVIDES conversation handoff and pickup via timestamped session documents and compact-summary persistence
SO THAT all Claude Code sessions
CAN maintain work continuity without context loss across explicit handoffs and context compaction events

`spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler` owns the `.spx/sessions/` store and the `spx session` command contract every other concern consumes. `spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler` owns closing a session; `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler` owns resuming one. The assertions below are the compaction contract and the coordination-overlay contract, both cross-cutting: each governs every session concern rather than any one of them.

A repository that follows methodology 4.0 coordination (the declaration in `versions/4.0/methodology/coordination/changes.md` of `outcomeeng/methodology`, the version `spx.config.yaml` selects) may declare a Change store in `spx/local/coordination.md`. Under that overlay a Change is one issue in the declared store: Product, Maturity (`Proposed`, `Framed`, `Sliced`, `Executable`), and Status (`Available`, `Claimed`, `Applied`, `Refined`, `Abandoned`) are canonical Changes project fields; the issue body carries the Output and refinement content; comments carry Claim and Handoff records; and the assignee represents the current holder. Every field transition follows the ordered write and complete-readback protocol in `spx/21-spec-tree.enabler/76-sessions.enabler/21-change-coordination.pdr.md`. Session documents remain the contract when the overlay is absent.

## Assertions

### Compliance

- NEVER: under `spx/local/coordination.md`, a new or refined Change body carries Product, Maturity, Lifecycle, or Status metadata; legacy body metadata is removed only after the canonical project fields are verified, and a conflicting or partial project state is reconstructed from issue history before removal ([audit])
- ALWAYS: under `spx/local/coordination.md`, `/pickup` and `/handoff` coordinate through the declared Change store — one Change per Output with Product, Maturity, and Status in canonical project fields, refinement content in the body, Claim and Handoff records in comments, and holder state in the assignee — explicitly write and verify every field transition under `spx/21-spec-tree.enabler/76-sessions.enabler/21-change-coordination.pdr.md`, and write no session document; without the overlay the session-document contract applies unchanged ([audit])
- NEVER: a Change body, refinement, or Handoff comment carries a secret value or credential payload ([audit])
- ALWAYS: after compaction, the managed root instruction block requires `/understand` before the next product-content access and `/contextualize` on the governing spec node before any product content it governs is read or modified and before that node is discussed, with a compaction emptying the set of contextualized nodes and an operational continuation — PR inspection, check wait, merge, deploy, release, `spx session` operations, occupancy proof — triggering neither, while the `SessionStart` hook remains limited to delegated session-environment and worktree-occupancy behavior ([audit])
- NEVER: `.claude/settings.json` defines a `compactPrompt` override; Claude Code's standard compact summary remains the state record the resuming agent interprets ([audit])
- NEVER: a compaction event creates a `/handoff` session file — compaction continuity is carried by the standard compact summary and the managed root instruction directive, distinct from the `todo`/`doing`/`archive` handoff queue; a session file is written only by a deliberate `/handoff` ([audit])
