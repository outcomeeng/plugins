---
name: handing-off
description: ALWAYS invoke when closing an in-scope spec-tree session, deciding whether to create a handoff, writing a handoff, or preparing continuation context. NEVER create a spec-tree handoff without this skill.
---

<context>
**Working Directory:**
!`pwd`

**Git Status:**
!`git status --short || echo "Not in a git repo"`

**Current Branch:**
!`git branch --show-current || echo "Not in a git repo"`

**Spec Tree:**
!`ls spx/*.product.md 2>/dev/null || echo "No spec tree found"`

</context>

<objective>
Close or transfer a spec-tree work session: persist what was learned to the right durable target, commit session-owned work, and decide whether a continuation artifact has a reader. The session file is a thin coordination envelope — the last resort for information that cannot live anywhere else.

The four-workflow sequence enforces persist-then-commit-then-continuation discipline. Lean on the imperfection ledger defined in `/understanding` (`references/imperfection-protocol.md`) for what was learned and what is broken — `/understanding` is loaded before any spec-tree work, so the ledger is always available here. Session scope, persistence tier, the Path A/B/C decision, and multi-context queue safety are spec-tree-specific concerns the ledger does not cover — they drive the workflows below.

</objective>

<artifact_purpose>
A handoff artifact exists for a future reader who must continue work. Create one only when unresolved in-scope work remains, a claimed session needs canonical continuation context, or the user explicitly asks for a continuation record.

When the work has reached the user-approved stopping state and all remaining issues already live in higher persistence tiers, omit the session file and close with `--no-session`. A session with no continuation reader creates queue noise and splits truth away from the durable map.

Example of the omit case: a session lands a spec amendment, writes a `PLAN.md` entry for deferred CLI work, and commits both. Every continuation thread is persisted — the spec carries the new rule, `PLAN.md` carries the deferred work — so `/handoff --no-session` (or `/release`) closes correctly and no `.spx/sessions/todo/` file is created.

The artifact is not a retrospective, changelog, lessons-learned notebook, or duplicate of PLAN.md/ISSUES.md. Reusable lessons belong in methodology. Open issues belong in the owning spec tree node. Review and validation facts belong in commit/PR history unless a future reader needs them to resume.

</artifact_purpose>

<session_scope_invariants>
Three rules govern a conversation's session scope:

1. Scope grows only by user confirmation (via `/picking-up`).
2. Closure has exactly one acceptable end state per in-scope session: archived after this workflow runs against it.
3. Quick-release escape hatch via `/release` if the user confirms within a few turns of pickup.

Permission to archive comes from completing this workflow against the in-scope set named in `<SESSION_SCOPE ids="…">` — never from queue inspection. A handoff replaces incorporated context, never supplements it. Mid-session handoff artifacts created by this conversation are workflow artifacts, not scope members.

Full algorithm in `references/scope-resolution.md`.

</session_scope_invariants>

<persistence_hierarchy>
Persist to the HIGHEST applicable tier.

| Tier | Where                                   | Durability   | When to use                                                                       |
| ---- | --------------------------------------- | ------------ | --------------------------------------------------------------------------------- |
| 1    | Spec tree (`spx/`)                      | Durable      | Spec amendments, test files, assertion updates                                    |
| 2    | Methodology (skills, CLAUDE.md, memory) | Durable      | Reusable patterns, user preferences, coding gotchas                               |
| 3    | Node-local (PLAN.md, ISSUES.md)         | Escape hatch | Remaining steps, known gaps — non-durable but discoverable via `/contextualizing` |
| 4    | Session file (`.spx/sessions/todo/`)    | Ephemeral    | Coordination only: node list, skill checklist, cross-cutting context              |

Tier 3 is an escape hatch, not a home. MUST use `AskUserQuestion` before writing PLAN.md or ISSUES.md.

Git commit is the final persistence operation, not a fifth tier. Session-owned spec edits, test edits, code edits, and escape hatches MUST be committed before session closure.

</persistence_hierarchy>

<multi_agent_awareness>
The `.spx/sessions/todo/` queue contains work for all active contexts across all worktrees. NEVER archive others' work. `doing` = claimed by active contexts; archive only the sessions in the resolved scope. `archive` = completed work (safe to prune old entries).

</multi_agent_awareness>

<arguments>
- `--no-session` (= `/release`): persist all approved items, archive in-scope sessions, and skip handoff creation because no continuation reader exists. Putting a claimed session back in TODO is a separate manual operation (not currently supported by `spx session`).
- `--prune`: after writing the new handoff, delete archive sessions. Ignored under `--no-session`.

Check `$ARGUMENTS` for these flags before starting workflow 01.

</arguments>

<workflows>
Execute all four workflows in sequence. Each workflow has its own success criteria — do not proceed to the next until the current one is complete. Workflow 04 writes a session file only when the approved proposal identifies continuation work that needs a reader.

1. `workflows/01-anchor-to-nodes.md` — identify every node worked on this session
2. `workflows/02-reflect.md` — review imperfections, scope, and starting point
3. `workflows/03-propose.md` — present persistence proposal to user for approval
4. `workflows/04-execute.md` — write approved items, commit, then write or omit the canonical continuation

</workflows>

<success_criteria>

A successful closure or handoff:

- [ ] All anchored nodes identified with status and TDD position (workflow 01)
- [ ] All four perspectives worked through (workflow 02)
- [ ] Existing PLAN.md and ISSUES.md checked for staleness — updated or removed if stale (workflow 02)
- [ ] `<RESOLVED_SCOPE>` marker emitted into the conversation by workflow 02
- [ ] Combined persistence proposal presented to user and approved items written (workflows 03–04)
- [ ] Session-owned spec, test, code, and escape-hatch changes committed before closure (workflow 04)
- [ ] Committed vs uncommitted state recorded for each node (workflow 04)
- [ ] Continuation need explicitly decided: session file created via `spx session handoff`, rewritten in place from a mid-session artifact, or omitted under `--no-session` (workflow 04)
- [ ] Every session in the resolved scope archived after the canonical continuation is written, rewritten, or intentionally omitted (workflow 04)
- [ ] Any session file created is a thin coordination envelope — bulk of value persisted durably
- [ ] End state has zero or one handoff incorporating everything — never a sidecar/supplemental/addendum
- [ ] Closure order followed: reflect → propose → persist → commit → canonical continuation decided → archive scope

</success_criteria>
