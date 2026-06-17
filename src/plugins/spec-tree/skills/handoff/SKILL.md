---
name: handoff
description: ALWAYS invoke to close a claimed spec-tree session — archive it, decide session-file creation, prepare continuation context — only once its goal is met with no continuation remaining or continuation by Claude is impossible (context exhausted, user halted, external blocker). NEVER invoke while do-able in-scope work remains, and NEVER create a spec-tree session file without this skill.
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

<precondition>
**Handoff is not a voluntary close. Run this skill only when the session is genuinely over** — either the user's stated goal is met with no continuation remaining, or continuation by Claude now is impossible (the user halted the work, the context is exhausted, or an external blocker — operator input, a remote-state change Claude cannot effect — prevents the next action). Genuine completion is a valid reason to run this skill; it then archives the claimed session and decides session-file creation per the rules below. While in-scope work Claude could do now remains — an unresolved `PLAN.md` item authored or touched this session, a `spx/EXCLUDE` entry covering the scope, a declared-but-unimplemented assertion, a branch with committed changes ahead of its resolved base for default-branch work, or any named-but-unbuilt part of the user's stated goal — STOP: do not run this skill; return to the work and continue. A clean working tree, a merge, a passing gate, or a freshly written coordination note is not a reason to hand off while committed changes remain outside the default branch on origin. Writing a `PLAN.md` or a session file to defer do-able work and then handing off is the banned closing reflex this precondition exists to prevent. Persisting coordination is correct; persisting it and handing off while able to continue is not. The workflows below run only after this precondition holds — see the `<closing_protocol>` loaded by `/understand`.
</precondition>

<objective>
Close the ongoing spec-tree session: commit session-owned work on its branch, persist issues and plans already made in coordination notes (these live in the affected spec tree nodes), commit them on the session branch or create a pure coordination branch, and push all branches to origin. Unless every node anchored this session carries no unresolved continuation, create a session file as an initialization prompt for the next session of Claude. If created, the session file comprises pointers to the persisted files (via origin branch) and external state such as the state of production infrastructure.

The imperfection ledger started when invoking the `/understand` skill (which loads the imperfection protocol) has captured insights and issues. With this skill, it is drained by triaging and persisting all remaining entries.

</objective>

<session_file_purpose>

A session file initializes Claude in the next session. Claude starts from a blank slate — none of what was achieved, learnt, or tried in this session will be known to Claude in the next session. The session file is an initialization prompt: it lists the skills to invoke, points at the relevant spec tree nodes, and suggests the first action. This way, the user does not have to point Claude at information the repository holds. Claude will derive all details from the spec tree, not from the session file.

- **Initialization session file** — every fact the next session needs lives in the repository. The file carries pointers (skills, nodes, action) plus the coordination that cannot be reconstructed from the spec tree and git history.
- **Initialization session file with external state** — the same pointers and suggested actions plus the optional `<state_at_handoff>` section recording observable external state Claude cannot re-derive from the repository (live PR/run/image identifiers, deployed inventories, failed workflows to be re-started). Through this skill, Claude guides the next Claude's pickup from that external state in clear and unambiguous prose.

<what_not_to_add>

- NEVER duplicate or summarize coordination notes — they load via `/contextualize`
- NEVER summarize spec content — it is literally in the spec tree and is bound to become stale eventually
- NEVER narrate or otherwise log session activity — git commit messages and PRs carry that

</what_not_to_add>

Create a session file unless absolutely no unresolved continuation remains.

**Nothing to archive is not nothing to hand off.** The claimed-session set (`CLAIMED_SESSIONS`, the `/pickup`'d sessions) decides only what gets archived. Whether to write a session file is a separate question decided by the continuation signal over the nodes anchored this session. Never infer one from the other: a fresh handoff with no `/pickup` (empty claimed-session set, nothing to archive) still requires a session file whenever an anchored node carries unfinished work.

**Unfinished work needs a session file, even when the remaining steps are written to a node's `PLAN.md`.** The `PLAN.md` is the *what* (the steps, on the branch); the session is the point-in-time *pointer* by which Claude in another worktree discovers the work exists and which branch carries it. They are not substitutes. A persisted `PLAN.md` or unresolved `ISSUES.md` entry on an anchored node IS continuation — both are next-session work, differing only by driver (a plan vs a defect), so both make the signal `present`.

Closing without a session file is appropriate only when **no continuation remains** — workflow 02's `<CONTINUATION_SIGNAL>` is `absent`: the anchored nodes carry no `PLAN.md`, no unresolved `ISSUES.md` entry, no `spx/EXCLUDE` entry, and no declared-but-unsatisfied assertion. A persisted coordination note that represents no future work is not a reason to skip the file — it is removed during closure, because a note no one will act on is deleted, not kept. (`--no-session`, or words to that effect, asserts this `absent` state; it never authorizes skipping the file when the signal is `present`.)

`--no-session` never authorizes skipping the session file when the `<CONTINUATION_SIGNAL>` is `present`. When `--no-session` meets a `present` signal, surface the contradiction (workflow 04 Path A) — automation never skips the session file on the user's behalf while continuation work exists. In any other situation, a session file is required.

<no_excuses>

When the invocation of **`spx session handoff` refuses to create a session file,** e.g. on a linked worktree that is not cleanly detached at `origin/<default>` because the persist-then-detach precondition is unmet (see `workflows/04-execute.md` `<release_work_branch>`), address the problem by properly executing `workflows/04-execute.md` rather than rationalizing that no session file is needed.

The refusal is not satisfied by **relocating** — running the handoff from a different worktree that is already clean while the work worktree keeps its branch. That records `git_ref` at unrelated state and leaves the work branch occupied, so `/pickup` cannot claim it: the handoff then points at the wrong place AND strands the work. The "keep the work worktree on its branch so it's ready to continue" instinct is the trap — that worktree is exactly the one the next agent cannot use. Release the worktree that holds the work — commit, push the work branch, detach it to `origin/<default>` — and run the handoff there, so the recorded anchor and the freed branch both point at the work.

**Foreign-pool guardrail.** The worktree that holds the work is always one in Claude's own pool. Never relocate the work into, or run the handoff against, a `.spx/` pool Claude does not participate in — another product's checkout. A foreign pool's worktree is off-limits regardless of how free its git state looks; treat it as occupied, because the claim protocol coordinates only agents that share one pool. Relocating a continuation into a separate live product's pool is the exact boundary this guardrail exists to stop.

</no_excuses>

</session_file_purpose>

<claimed_session_invariants>
Three rules govern a conversation's claimed-session set:

1. The claimed-session set grows only by user confirmation (via `/pickup`).
2. Closure has exactly one acceptable end state per claimed session: archived after this workflow runs against it.
3. Quick-release shortcut via `/handoff --no-session` for a wrongly-claimed session the user releases within a few turns of pickup — valid because such a session carries no continuation, so the `<CONTINUATION_SIGNAL>` is `absent`.

Permission to archive comes from completing this workflow against the claimed-session set named in `<CLAIMED_SESSIONS ids="…">` — never from queue inspection. A handoff replaces incorporated context, never supplements it. Mid-session session files created by this conversation are workflow artifacts, not members of the claimed-session set.

Full algorithm in `references/claimed-session-resolution.md`.

</claimed_session_invariants>

<persistence_hierarchy>
Persist to the HIGHEST applicable tier.

| Tier | Where                                   | Durability                 | When to use                                                                                                                                                                                           |
| ---- | --------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Methodology (skills, CLAUDE.md)         | Durable                    | Reusable patterns, gotchas, clarifications etc.                                                                                                                                                       |
| 2    | Spec tree (`spx/`)                      | Durable                    | New or updated durable spec tree files such as decisions, specs and tests                                                                                                                             |
| 3    | Coordination notes (PLAN.md, ISSUES.md) | Until resolved or disposed | Remaining steps, known gaps and defects — committed for cross-session coordination. CAUTION: coordination notes are prone to go stale; always reconcile before use, discoverable via `/contextualize` |
| 4    | Session file                            | Ephemeral                  | Coordination only: node list, skill checklist, external-infrastructure state, cross-cutting context                                                                                                   |

A Tier-3 coordination note holds remaining steps, known gaps and defects that Claude thought to be relevant and correct at one point in time. When in conflict with spec tree's durable product truth, they must be reconciled before use.

Session-owned spec edits, test edits, code edits, and coordination notes MUST be committed before session closure.
Committing changes discovered during the handoff is expected, this is why the reflection is valuable. Coordination notes that are related to the main thread belong on the same branch. Coordination notes for a different concern belong on a fresh branch.
Pushing all branches to origin is the most important and final persistence operation for the committed tiers (1–3); the Tier-4 session file is written separately by `spx session handoff` to the gitignored `.spx/` session store, which is not pushed. The push is followed by switching to and then detaching from the origin's default branch.

</persistence_hierarchy>

<multi_agent_awareness>
The session file store queues work for all active contexts across all worktrees.

NEVER archive others' work. `doing` = claimed by active contexts; archive only the sessions in the resolved claimed-session set. `archive` = completed work (safe to prune old entries once the user approves).

</multi_agent_awareness>

<arguments>
- `--no-session`: complete all workflows as mandated by this skill, including persisting coordination notes on a remote branch, archiving potentially claimed sessions, etc. The difference is that, when no continuation remains, Claude skips creating a session file. `--no-session` asserts that absence; it does not override a `present` `<CONTINUATION_SIGNAL>` — workflow 04 Path A surfaces the contradiction instead of silently skipping.
- `--prune`: after writing the new handoff, delete archived sessions. Ignored under `--no-session`.

Check `$ARGUMENTS` for these flags before starting the workflows below.

</arguments>

<workflows>
Execute all four workflows in sequence. Each workflow has its own success criteria — do not proceed to the next until the current one is complete. Workflow 04 persists all work and coordination notes and, unless `--no-session`, writes the session file.

1. `workflows/01-anchor-to-nodes.md` — identify every node worked on this session
2. `workflows/02-reflect.md` — review imperfections, claimed sessions, and starting point
3. `workflows/03-propose.md` — present persistence proposal to user for approval
4. `workflows/04-execute.md` — create or update coordination notes, commit, then write or omit the canonical continuation session file

</workflows>

<success_criteria>

A successful closure or handoff:

- [ ] All anchored nodes identified with status and TDD position (workflow 01)
- [ ] All five perspectives worked through (workflow 02)
- [ ] Existing coordination notes such as PLAN.md and ISSUES.md checked for staleness — updated or removed if stale (workflow 02)
- [ ] `<RESOLVED_CLAIMED_SESSIONS>` marker emitted into the conversation by workflow 02
- [ ] `<CONTINUATION_SIGNAL>` marker emitted by workflow 02, and `--no-session` honored only when it is `absent`
- [ ] Combined persistence proposal presented to user and approved items written (workflows 03–04)
- [ ] Session-owned spec, test, code, and coordination-note changes committed before closure (workflow 04)
- [ ] Continuation need explicitly decided: session file created via `spx session handoff`, rewritten in place from a mid-session artifact, or omitted under `--no-session` (workflow 04)
- [ ] Every session in the resolved claimed-session set archived after the canonical continuation is written, rewritten, or intentionally omitted (workflow 04)
- [ ] Any session file created is a thin coordination envelope — bulk of value persisted durably
- [ ] End state has zero, one, or several completely independent session files incorporating everything within the resolved claimed-session set
- [ ] Closure order followed: reflect → propose → persist → commit → canonical continuation decided → archive the claimed sessions

</success_criteria>
