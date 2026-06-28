---
name: handoff
description: ALWAYS invoke to close a claimed spec-tree session — archive it, decide session-file creation, prepare continuation context — only once its goal is met with no continuation remaining, the user halted work, context is exhausted, or an external blocker prevents the next action. NEVER invoke while do-able in-scope work remains, and NEVER create a spec-tree session file without this skill.
argument-hint: "[--no-session] [--prune]"
arguments: [session_mode, prune_mode]
allowed-tools: Read, Edit, Write, Bash(spx session:*), Bash(git status:*), Bash(git branch:*), Bash(git push:*), Bash(git switch:*), Bash(git symbolic-ref:*), Bash(pwd), Bash(ls:*), AskUserQuestion, Glob, Grep, Skill
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

<precondition>
**Handoff is not a voluntary close. Run this skill only when the session is genuinely over** — either the user's stated goal is met with no continuation remaining, or continuation by Claude now is impossible (the user halted the work, the context is exhausted, or an external blocker — operator input, a remote-state change Claude cannot effect — prevents the next action). Genuine completion is a valid reason to run this skill; it then archives the claimed session and decides session-file creation per the rules below. While in-scope work Claude could do now remains — an unresolved `PLAN.md` item authored or touched this session, a `spx/EXCLUDE` entry covering the scope, a declared-but-unimplemented assertion, a branch with committed changes ahead of its resolved base for default-branch work, or any named-but-unbuilt part of the user's stated goal — STOP: do not run this skill; return to the work and continue. A clean working tree, a merge, a passing gate, or a freshly written coordination note is not a reason to hand off while committed changes remain outside the default branch on origin. Writing a `PLAN.md` or a session file to defer do-able work and then handing off is the banned closing reflex this precondition exists to prevent. Persisting coordination is correct; persisting it and handing off while able to continue is not. The workflows below run only after this precondition holds — see the `<closing_protocol>` loaded by `/understand`.
</precondition>

<objective>
A closed spec-tree session with session-owned work committed and pushed, encountered coordination notes reconciled or fixed, the imperfection ledger drained, and continuation disposition recorded.
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

Create a session file only when continuation by Claude is impossible now: the user halted the work, context is exhausted, or an external blocker prevents the next action. A session file is not a disposal path for coordination notes Claude can reconcile now.

**Nothing to archive is not nothing to hand off.** The claimed-session set (`CLAIMED_SESSIONS`, the `/pickup`'d sessions) decides only what gets archived. Whether to write a session file is a separate question decided by the stop condition, the coordinated-node state, and the existing session queue. Never infer one from the other.

**Coordination notes block closure while Claude can act.** A persisted `PLAN.md` or unresolved `ISSUES.md` entry on an anchored node means the session is not over unless continuation is impossible now. Reconcile notes in the same session: remove stale entries, fix safe local defects, update imprecise entries, or continue into the work they describe. When a clearly wrong note outside the original scope is observed, record it in the imperfection ledger and fix it if the correction is safe and local; if ownership, scope, or cost changes, ask the operator at the next checkpoint. Do not convert it into a new session file.

**Search before adding any continuation.** Before proposing or creating a continuation session, inspect existing `todo` and `doing` sessions with status-filtered reads: `spx session list --status todo --json` and `spx session list --status doing --json`. Compare their `specs`, `files`, `goal`, and `next_step` against the nodes and topic terms from this closure. If an existing session already owns the same continuation, reconcile against it: rewrite a mid-session artifact only when this conversation created it, archive only sessions this conversation owns, and leave unrelated or ambiguous sessions untouched. Creating a new `todo` entry is valid only after this search shows no existing owner and continuation by Claude is impossible now.

Closing without creating a session file is appropriate when no continuation reader is needed from this closure. That is true when workflow 02's `<CONTINUATION_SIGNAL>` is `absent`: the anchored nodes carry no actionable `PLAN.md`, no unresolved `ISSUES.md` entry, no `spx/EXCLUDE` entry, no declared-but-unsatisfied assertion, and no external blocker. It is also true when `<EXISTING_SESSION_RECONCILIATION status="existing-owner">` confirms another session already owns the only remaining continuation and this closure has no local blocker. A persisted coordination note that represents no future work is removed during closure, because a note no one will act on is deleted, not kept.

`--no-session` never authorizes skipping the session file when the `<CONTINUATION_SIGNAL>` is `present` and no existing owner exists. When `--no-session` meets that state, surface the contradiction (workflow 04 Path A) — automation never skips the session file on the user's behalf when a real stop condition requires a continuation reader. In any other situation, a session file is written only after the existing-session search completes.

<no_excuses>

When the invocation of **`spx session handoff` refuses to create a session file,** e.g. on a linked worktree that is not cleanly detached at `origin/<default>` because the persist-then-detach precondition is unmet (see `workflows/04-execute.md` `<release_work_branch>`), address the problem by properly executing `workflows/04-execute.md` rather than rationalizing that no session file is needed.

The refusal is not satisfied by **relocating** — running the handoff from a different worktree that is already clean while the work worktree keeps its branch. That records `git_ref` at unrelated state and leaves the work branch occupied, so `/pickup` cannot claim it: the handoff then points at the wrong place AND strands the work. The "keep the work worktree on its branch so it's ready to continue" instinct is the trap — that worktree is exactly the one the next agent cannot use. Step the worktree that holds the work off the branch — commit, push the work branch, detach it to `origin/<default>` — and run the handoff there, so the recorded anchor and the freed branch both point at the work.

**Foreign-pool guardrail.** The worktree that holds the work is always one in Claude's own pool. Never relocate the work into, or run the handoff against, a `.spx/` pool Claude does not participate in — another product's checkout. A foreign pool's worktree is off-limits regardless of how free its git state looks; treat it as occupied, because the claim protocol coordinates only agents that share one pool. Relocating a continuation into a separate live product's pool is the exact boundary this guardrail exists to stop.

</no_excuses>

</session_file_purpose>

<claimed_session_invariants>
Three rules govern a conversation's claimed-session set:

1. The claimed-session set grows only by user confirmation (via `/pickup`).
2. Closure has exactly one acceptable end state per claimed session: archived after this workflow runs against it.
3. Quick-release shortcut via `/handoff --no-session` for a wrongly-claimed session the user releases within a few turns of pickup — valid only when the session carries no actionable coordination note or do-able continuation, so the `<CONTINUATION_SIGNAL>` is `absent`.

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
Session files are not a lower tier for unresolved notes Claude can fix or reconcile. They are only a pointer for a real stop condition after durable and coordination tiers are already correct.
Pushing the session-owned work branch to origin is the most important and final persistence operation for the committed tiers (1–3); the Tier-4 session file is written separately by `spx session handoff` to the gitignored `.spx/` session store, which is not pushed. The push is followed by switching to and then detaching from the origin's default branch.

</persistence_hierarchy>

<multi_agent_awareness>
The session file store queues work for all active contexts across all worktrees.

NEVER archive others' work. `doing` = claimed by active contexts; archive only the sessions in the resolved claimed-session set. `archive` = completed work (safe to prune old entries once the user approves).

</multi_agent_awareness>

<arguments>
- `--no-session`: complete all workflows as mandated by this skill, including persisting coordination notes on a remote branch, archiving potentially claimed sessions, etc. The difference is that Claude skips creating a new session file when no continuation remains or when another existing session already owns the only remaining continuation. It does not override a `present` `<CONTINUATION_SIGNAL>` with no existing owner — workflow 04 Path A surfaces that contradiction instead of silently skipping.
- `--prune`: after writing the new handoff, delete archived sessions. Ignored under `--no-session`.

Check `$session_mode` and `$prune_mode` for these flags before starting the workflows below.

</arguments>

<workflows>
Execute all four workflows in sequence. Each workflow has its own success criteria — do not proceed to the next until the current one is complete. Workflow 04 persists all work and coordination notes and, unless `--no-session`, writes the session file.

1. `workflows/01-anchor-to-nodes.md` — identify every node worked on this session
2. `workflows/02-reflect.md` — review imperfections, claimed sessions, and starting point
3. `workflows/03-propose.md` — present persistence proposal to user for approval
4. `workflows/04-execute.md` — create or update coordination notes, commit, then write or omit the canonical continuation session file

</workflows>

<failure_modes>

**Continuation written before durable persistence.** Claude created or rewrote the session file before approved coordination, spec, test, code, or generated-output changes were committed and pushed. Return to workflow 04 persistence, commit session-owned files first, push the work branch when it exists, then create or rewrite the canonical continuation.

**Branch left occupied after handoff.** Claude wrote a continuation with a work-branch `git_ref` and kept the releasing worktree checked out on that same branch. Step off per `workflows/04-execute.md` `<release_work_branch>` so `/pickup` can claim the branch in another worktree.

**Multiple canonical continuations kept for one thread.** Claude created a new handoff while a mid-session artifact still described the same continuation. Reconcile the artifacts: rewrite one in place when appropriate, archive every superseded artifact, and leave exactly one canonical TODO session for the thread.

**Archive or prune touched unrelated sessions.** Claude archived a session outside `<RESOLVED_CLAIMED_SESSIONS>` or deleted a TODO/doing session during `--prune`. Stop and restore the queue state if possible; archive only resolved claimed sessions and superseded mid-session artifacts, and prune archive entries only.

</failure_modes>

<success_criteria>

A successful closure or handoff:

- [ ] All anchored nodes identified with status and TDD position (workflow 01)
- [ ] All six perspectives worked through (workflow 02)
- [ ] Existing coordination notes such as PLAN.md and ISSUES.md checked for staleness and reconciled before closure — updated, removed, or pursued now when Claude can still act (workflows 02–04)
- [ ] Existing `todo` and `doing` sessions searched by node path and topic before any continuation session is proposed or created (workflow 02)
- [ ] `<RESOLVED_CLAIMED_SESSIONS>` marker emitted into the conversation by workflow 02
- [ ] `<CONTINUATION_SIGNAL>` marker emitted by workflow 02, and `--no-session` honored only when it is `absent` or `status="existing-owner"` confirms another session owns the only remaining continuation and no local blocker remains
- [ ] Combined persistence proposal presented to user and approved items written (workflows 03–04)
- [ ] Session-owned spec, test, code, and coordination-note changes committed before closure (workflow 04)
- [ ] Continuation need explicitly decided: session file created via `spx session handoff`, rewritten in place from a mid-session artifact, or omitted under `--no-session` (workflow 04)
- [ ] Every session in the resolved claimed-session set archived after the canonical continuation is written, rewritten, or intentionally omitted (workflow 04)
- [ ] Any session file created is a thin coordination envelope — bulk of value persisted durably
- [ ] End state has zero, one, or several completely independent session files incorporating everything within the resolved claimed-session set
- [ ] Closure proof is present: workflow 02 markers exist, workflow 03 disposition names the canonical continuation and archive list, and workflow 04 confirmation names the committed work and archived sessions

</success_criteria>
