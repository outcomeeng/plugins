---
name: handoff
description: ALWAYS invoke when closing an in-scope spec-tree session, deciding whether to create a session file, writing a session file, or preparing continuation context. NEVER create a spec-tree session file without this skill.
argument-hint: "[--no-session] [--prune]"
allowed-tools: Read, Edit, Write, Bash(spx:*), Bash(git:*), Bash(pwd), Bash(ls:*), AskUserQuestion, Glob, Grep, Skill
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
Close the ongoing spec-tree session: commit session-owned work on its branch, persist issues and plans you have already made in coordination notes (these live in the affected spec tree nodes), commit them on the session branch or create a pure coordination branch, and push all branches to origin. Unless absolutely all work in the threads of this session is done, create a session file as an initialization prompt for the next session of Claude. If created, the session file comprises pointers to the persisted files (via origin branch) and external state such as the state of production infrastructure.

The imperfection ledger you started when invoking the `/understanding` skill (`references/imperfection-protocol.md`) has captured insights and issues. With this skill, it is drained by triaging and persisting all remaining entries.

</objective>

<session_file_purpose>

A session file initializes Claude in the next session. Claude starts from a blank slate — none of what was achieved, learnt, or tried in this session will be known to Claude in the next session. The session file is an initialization prompt: it lists the skills to invoke, points at the relevant spec tree nodes, and suggests the first action. This way, the user does not have to point Claude at information the repository holds. Claude will derive all details from the spec tree, not from the session file.

- **Initialization session file** — every fact the next session needs lives in the repository. The file carries pointers (skills, nodes, action) plus the coordination that cannot be reconstructed from the spec tree and git history.
- **Initialization session file with external state** — the same pointers and suggested actions plus the optional `<state_at_handoff>` section recording observable external state Claude cannot re-derive from the repository (live PR/run/image identifiers, deployed inventories, failed workflows to be re-started). Through this skill, Claude guides the next Claude's pickup from that external state in clear and unambiguous prose.

<what_not_to_add>

- NEVER duplicate or summarize coordination notes — they load via `/contextualizing`
- NEVER summarize spec content — it is literally in the spec tree and is bound to become stale eventually
- NEVER narrate or otherwise log session activity — git commit messages and PRs carry that

</what_not_to_add>

Create a session file unless absolutely no unresolved work in-scope remains.

**Unfinished work needs a session file, even when the remaining steps are written to a node's `PLAN.md`.** The `PLAN.md` is the *what* (the steps, on the branch); the session is the point-in-time *pointer* by which Claude in another worktree discovers the work exists and which branch carries it. They are not substitutes.

Closing without a session file is appropriate only in two cases:

1. When **absolutely no continuation exists** as the work reached the user-approved stopping state and only deferred coordination notes remain, or
2. When the **user explicitly asks by passing `--no-session`** or passes along words to that effect (e.g., `determine if a session file is needed`).

In any other situation, a session file is required.

<no_excuses>

When the invocation of **`spx session handoff` refuses to create a session file,** e.g. on a linked worktree that is not cleanly detached at `origin/<default>` because the persist-then-detach precondition is unmet (see `workflows/04-execute.md` `<release_work_branch>`), address the problem by properly executing `workflows/04-execute.md` rather than rationalizing that no session file is needed.

</no_excuses>

</session_file_purpose>

<session_scope_invariants>
Three rules govern a conversation's session scope:

1. Scope grows only by user confirmation (via `/pickup`).
2. Closure has exactly one acceptable end state per in-scope session: archived after this workflow runs against it.
3. Quick-release shortcut via `/handoff --no-session` if the user confirms within a few turns of pickup.

Permission to archive comes from completing this workflow against the in-scope set named in `<SESSION_SCOPE ids="…">` — never from queue inspection. A handoff replaces incorporated context, never supplements it. Mid-session session files created by this conversation are workflow artifacts, not scope members.

Full algorithm in `references/scope-resolution.md`.

</session_scope_invariants>

<persistence_hierarchy>
Persist to the HIGHEST applicable tier.

| Tier | Where                                   | Durability                 | When to use                                                                                                                                                                                             |
| ---- | --------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Methodology (skills, CLAUDE.md)         | Durable                    | Reusable patterns, gotchas, clarifications etc.                                                                                                                                                         |
| 2    | Spec tree (`spx/`)                      | Durable                    | New or updated durable spec tree files such as decisions, specs and tests                                                                                                                               |
| 3    | Coordination notes (PLAN.md, ISSUES.md) | Until resolved or disposed | Remaining steps, known gaps and defects — committed for cross-session coordination. CAUTION: coordination notes are prone to go stale; always reconcile before use, discoverable via `/contextualizing` |
| 4    | Session file                            | Ephemeral                  | Coordination only: node list, skill checklist, external-infrastructure state, cross-cutting context                                                                                                     |

A Tier-3 coordination note holds remaining steps, known gaps and defects that Claude thought to be relevant and correct at one point in time. When in conflict with spec tree's durable product truth, they must be reconciled before use.

Session-owned spec edits, test edits, code edits, and coordination notes MUST be committed before session closure.
Committing changes discovered during the handoff is expected, this is why the reflection is valuable. Coordination notes that are related to the main thread belong on the same branch. Differently scoped coordination notes belong on a fresh branch.
Pushing all branches to origin is the most important and final persistence operation for the committed tiers (1–3); the Tier-4 session file is written separately by `spx session handoff` to the gitignored `.spx/` session store, which is not pushed. The push is followed by switching to and then detaching from the origin's default branch.

</persistence_hierarchy>

<multi_agent_awareness>
The session file store queues work for all active contexts across all worktrees.

NEVER archive others' work. `doing` = claimed by active contexts; archive only the sessions in the resolved scope. `archive` = completed work (safe to prune old entries once the user approves).

</multi_agent_awareness>

<arguments>
- `--no-session`: complete all workflows as mandated by this skill, including persisting coordination notes on a remote branch, archiving potentially in-scope sessions, etc. The only difference is that Claude skips creating a session file.
- `--prune`: after writing the new handoff, delete archived sessions. Ignored under `--no-session`.

Check `$ARGUMENTS` for these flags before starting the workflows below.

</arguments>

<workflows>
Execute all four workflows in sequence. Each workflow has its own success criteria — do not proceed to the next until the current one is complete. Workflow 04 persists all work and coordination notes and, unless `--no-session`, writes the session file.

1. `workflows/01-anchor-to-nodes.md` — identify every node worked on this session
2. `workflows/02-reflect.md` — review imperfections, scope, and starting point
3. `workflows/03-propose.md` — present persistence proposal to user for approval
4. `workflows/04-execute.md` — create or update coordination notes, commit, then write or omit the canonical continuation session file

</workflows>

<success_criteria>

A successful closure or handoff:

- [ ] All anchored nodes identified with status and TDD position (workflow 01)
- [ ] All five perspectives worked through (workflow 02)
- [ ] Existing coordination notes such as PLAN.md and ISSUES.md checked for staleness — updated or removed if stale (workflow 02)
- [ ] `<RESOLVED_SCOPE>` marker emitted into the conversation by workflow 02
- [ ] Combined persistence proposal presented to user and approved items written (workflows 03–04)
- [ ] Session-owned spec, test, code, and coordination-note changes committed before closure (workflow 04)
- [ ] Continuation need explicitly decided: session file created via `spx session handoff`, rewritten in place from a mid-session artifact, or omitted under `--no-session` (workflow 04)
- [ ] Every session in the resolved scope archived after the canonical continuation is written, rewritten, or intentionally omitted (workflow 04)
- [ ] Any session file created is a thin coordination envelope — bulk of value persisted durably
- [ ] End state has zero, one, or several completely independent session files incorporating everything within the resolved scope
- [ ] Closure order followed: reflect → propose → persist → commit → canonical continuation decided → archive scope

</success_criteria>
