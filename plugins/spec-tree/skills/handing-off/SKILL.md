---
name: handing-off
description: ALWAYS invoke this skill when closing a spec-tree work session, writing a handoff, or preparing continuation context for another agent. NEVER create a spec-tree handoff without this skill.
---

<context>
**Working Directory:**
!`pwd`

**Git Status:**
!`git status --short || echo "Not in a git repo"`

**Current Branch:**
!`git branch --show-current || echo "Not in a git repo"`

**Current Sessions:**
!`spx session list || echo 'Ask user to install spx CLI: "npm install --global @outcomeeng/spx"'`

**Spec Tree:**
!`ls spx/*.product.md 2>/dev/null || echo "No spec tree found"`

</context>

<objective>
Handoff is proper session closure, not note-taking. Reflect deeply on what was learned before persisting anything — four sequential workflows enforce the discipline that produces the right persistence decisions. The session file is a thin coordination envelope — the last resort for information that can't live anywhere else.

**Reflect, then persist, then commit, then hand off.** Workflow 02 (reflect) is the most important step. Without it, Claude dumps a narrative instead of making durable persistence decisions. Stale PLAN.md and ISSUES.md files are worse than none. A handoff with uncommitted session-owned work is incomplete.

</objective>

<session_scope_invariants>
Three rules govern a conversation's session scope:

1. **Scope grows only by user confirmation.** A session enters scope via `/picking-up` at user instruction, or by the user confirming an agent-suggested pickup. Nothing else extends scope.

2. **Closure has exactly one acceptable end state.** Every in-scope session becomes the agent's sole responsibility. The agent reflects, persists remaining validated relevant context, and ends with either zero or one handoff that incorporates everything from the in-scope sessions.

3. **Quick-release escape hatch.** If, within a few turns of pickup, the agent realizes the pickup was wrong and the user confirms release, the session leaves scope via `/release` without counting toward the closure workload.

**A handoff replaces incorporated context. It never supplements it.** A receiving agent must never need to read a prior handoff to understand the continuation.

**Permission to archive comes from completing this workflow against the in-scope set named in `<SESSION_SCOPE ids="…">` — never from queue inspection.** The mere existence of another session (whether created by this agent mid-work, queued by another agent, or otherwise) never grants permission to close an in-scope session.

**Mid-session created handoffs are workflow artifacts, not scope members.** If the agent ran `spx session handoff` earlier in this conversation and that file still sits in TODO, it must be reconciled at final closure so the end state has at most one handoff — either rewritten in place as the canonical continuation, or archived alongside the scope.

</session_scope_invariants>

<persistence_hierarchy>
All information discovered during a session falls into one of four tiers. Persist to the HIGHEST applicable tier.

| Tier | Where                                   | Durability   | When to use                                                                       |
| ---- | --------------------------------------- | ------------ | --------------------------------------------------------------------------------- |
| 1    | Spec tree (`spx/`)                      | Durable      | Spec amendments, test files, assertion updates                                    |
| 2    | Methodology (skills, CLAUDE.md, memory) | Durable      | Reusable patterns, user preferences, coding gotchas                               |
| 3    | Node-local (PLAN.md, ISSUES.md)         | Escape hatch | Remaining steps, known gaps — non-durable but discoverable via `/contextualizing` |
| 4    | Session file (`.spx/sessions/todo/`)    | Ephemeral    | Coordination only: node list, skill checklist, cross-cutting context              |

**Tier 3 is an escape hatch, not a home.** MUST use `AskUserQuestion` before writing PLAN.md or ISSUES.md.

Git commit is not a fifth tier. It is the final persistence operation after approved durable writes are complete. Session-owned spec edits, test edits, code edits, and escape hatches MUST be committed before session closure.

</persistence_hierarchy>

<multi_agent_awareness>
**Multiple agents may be working in parallel.** The todo queue contains work for ALL agents across ALL worktrees, not just this session.

- `todo` = Shared work queue (NEVER archive others' work)
- `doing` = Claimed by active agents (only archive YOUR claimed session)
- `archive` = Completed work (safe to prune old entries)

</multi_agent_awareness>

<arguments>
**`--no-session`**: Run the full reflection and persistence protocol, including the final commit, but skip session file creation in workflow 04. All approved items are persisted to their durable targets and committed. Unapproved items are dropped. Every in-scope session is still archived — `--no-session` skips only the creation of a new handoff file, not the archival of incorporated work.

Use `--no-session` when closing a session without handing off to another agent.

**Note on terminology**: the `/release` command is an alias for `--no-session` — it means "close without a new handoff, archive in-scope sessions." It does NOT mean "put the session back in the todo queue for another agent to pick up." Putting a claimed session back in todo is a distinct operation (not currently supported by `spx session`) and would require a manual file move from `.spx/sessions/doing/` to `.spx/sessions/todo/`.

**`--prune`**: After successfully writing the new handoff, delete old archive sessions. Does NOT touch the todo queue. Ignored when `--no-session` is set.

Check `$ARGUMENTS` for these flags before starting workflow 01.

</arguments>

<compact_analog>
When the conversation compacts before explicit closure, `compactPrompt` directs Claude to produce a compaction summary that includes spec-tree-specific sections. The PostCompact hook persists it to `.spx/sessions/tmp/compact-<session_id>.md`; the `session-resume` SessionStart hook atomically claims the file and injects it into the next session.

The receiving session executes workflows 03–04: presents the Persistence Proposal to the user, writes approved items, creates a session file via `spx session handoff`, and runs `compact-done` to remove the claimed compact file. Subsequent sessions resume from that session file via `/picking-up`. See `references/compact-format.md` for file naming, the `compactPrompt` value, and complete receiving-agent behavior.
</compact_analog>

<workflows>
Execute all four workflows in sequence. Each workflow has its own success criteria — do not proceed to the next until the current one is complete.

1. `workflows/01-anchor-to-nodes.md` — identify every node worked on this session
2. `workflows/02-reflect.md` — work through six perspectives internally
3. `workflows/03-propose.md` — present persistence proposal to user for approval
4. `workflows/04-execute.md` — write approved items, commit, create session file

</workflows>

<success_criteria>

A successful handoff:

- [ ] All anchored nodes identified with status and TDD position (workflow 01)
- [ ] All six reflection perspectives worked through (workflow 02)
- [ ] Existing PLAN.md and ISSUES.md checked for staleness — updated or removed if stale (workflow 02)
- [ ] Combined persistence proposal presented to user and approved items written (workflows 03–04)
- [ ] Session-owned spec, test, code, and escape-hatch changes committed before closure (workflow 04)
- [ ] Committed vs uncommitted state recorded for each node (workflow 04)
- [ ] Session file created via `spx session handoff`, rewritten in place from a mid-session artifact, or omitted under `--no-session` (workflow 04)
- [ ] Every session in the resolved scope archived after the canonical continuation is verified (workflow 04) — resolved from `<SESSION_SCOPE>` when present, or from the additive fallback when it is not
- [ ] Session file is a thin coordination envelope — bulk of value persisted durably
- [ ] End state has zero or one handoff incorporating everything — never a sidecar/supplemental/addendum
- [ ] Closure order followed: reflect → propose → persist → commit → canonical continuation written → archive scope

</success_criteria>
