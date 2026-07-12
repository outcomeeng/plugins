---
name: handoff
description: ALWAYS invoke to close a spec-tree session or merge lifecycle closeout — archive claimed sessions, decide session-file creation, prepare continuation context, and produce operator-useful closeout — only once its goal is met with no continuation remaining, the user halted work, context is exhausted, or an external blocker prevents the next action. NEVER invoke while do-able in-scope work remains, and NEVER create a spec-tree session file without this skill.
argument-hint: "[--no-session] [--prune]"
allowed-tools: Read, Edit, Write, Bash(printf:*), Bash(printenv CODEX_THREAD_ID), Bash(printenv CLAUDE_SESSION_ID), Bash(spx session list:*), Bash(spx session show:*), Bash(spx session handoff:*), Bash(spx session archive:*), Bash(spx session delete:*), Bash(git status:*), Bash(git branch:*), Bash(git worktree list:*), Bash(git fetch:*), Bash(git push:*), Bash(git switch:*), Bash(git symbolic-ref:*), Bash(git rev-parse:*), Bash(git cherry:*), Bash(git ls-files:*), Bash(grep:*), Bash(pwd), AskUserQuestion, Glob, Grep, Skill
---

<context>
**Working Directory:**
!`pwd`

**Git Status:**
!`git status --short || echo "Not in a git repo"`

**Current Branch:**
!`git branch --show-current || echo "Not in a git repo"`

**Spec Tree:**
!`git ls-files spx | grep -E '^spx/[^/]+[.]product[.]md$' || echo 'No spec tree found'`

</context>

<precondition>
**Handoff is not a voluntary close. Run this skill only when the session is complete** — either the user's stated goal is met with no continuation remaining, or continuation by Claude now is impossible (the user halted the work, the context is exhausted, or an external blocker — operator input, a remote-state change Claude cannot effect — prevents the next action). Completion is a valid reason to run this skill; it then archives the claimed session and decides session-file creation per the rules below. While in-scope work Claude could do now remains — an unresolved `PLAN.md` item authored or touched this session, a `spx/EXCLUDE` entry covering the scope, a declared-but-unimplemented assertion, a branch with committed changes ahead of its resolved base for default-branch work, or any named-but-unbuilt part of the user's stated goal — STOP: do not run this skill; return to the work and continue. A clean working tree, a merge, a passing gate, or a freshly written coordination note is not a reason to hand off while committed changes remain outside the default branch on origin. Writing a `PLAN.md` or a session file to defer do-able work and then handing off is the banned closing reflex this precondition exists to prevent. Persisting coordination is correct; persisting it and handing off while able to continue is not. The workflows below run only after this precondition holds — see the `<closing_protocol>` loaded by `/understand`.

Merge lifecycle closeout uses this skill even when no session was claimed. The claimed-session set decides only which existing sessions are archived; it never decides whether a merge closeout is useful. A merge transport invokes this skill plain, without receiving `--no-session`, so the same workflow produces the operator-useful product summary and decides whether a continuation reader is needed.
</precondition>

<objective>
A closed spec-tree session with session-owned work committed and pushed, encountered coordination notes reconciled or fixed, the imperfection ledger drained, and continuation disposition recorded.
</objective>

<session_file_purpose>

A session file initializes Claude in the next session. Claude starts from a blank slate — none of what was achieved, learnt, or tried in this session will be known to Claude in the next session. The session file is an initialization prompt: it points at the relevant spec tree nodes and suggests the first action. This way, the user does not have to point Claude at information the repository holds. Claude will derive all details and skill choices from the spec tree, not from the session file.

- **Initialization session file** — every fact the next session needs lives in the repository. The file carries node and first-action pointers plus the coordination that cannot be reconstructed from the spec tree and git history.
- **Initialization session file with external state** — the same pointers and suggested actions plus the optional `<state_at_handoff>` section recording observable external state Claude cannot re-derive from the repository (live PR/run/image identifiers, deployed inventories, failed workflows to be re-started). Through this skill, Claude guides the next Claude's pickup from that external state in clear and unambiguous prose.

<what_not_to_add>

- NEVER duplicate or summarize coordination notes — they load via `/contextualize`
- NEVER summarize spec content — it is literally in the spec tree and is bound to become stale eventually
- NEVER narrate or otherwise log session activity — git commit messages and PRs carry that

</what_not_to_add>

Create a session file only when continuation by Claude is impossible now: the user halted the work, context is exhausted, or an external blocker prevents the next action. A session file is not a disposal path for coordination notes Claude can reconcile now.

**Nothing to archive is not nothing to hand off.** The claimed-session set (`CLAIMED_SESSIONS`, the `/pickup`'d sessions) decides only what gets archived. Whether to write a session file is a separate question decided by the stop condition, the coordinated-node state, and the existing session queue. Never infer one from the other.

**Coordination notes block closure while Claude can act.** A persisted `PLAN.md` or unresolved `ISSUES.md` entry on an anchored node means the session is not over unless continuation is impossible now. Reconcile notes in the same session: remove stale entries, fix safe local defects, update imprecise entries, or continue into the work they describe. When a clearly wrong note outside the original scope is observed, record it in the imperfection ledger and fix it if the correction is safe and local; if ownership, scope, or cost changes, ask the operator at the next checkpoint. Do not convert it into a new session file.

**Search before adding any continuation.** Before proposing or creating a continuation session, inspect existing `todo` and `doing` sessions with status-filtered reads: `spx session list --status todo --json` and `spx session list --status doing --json`. Compare their `specs`, `files`, `goal`, and `next_step` against the nodes and topic terms from this closure. Reconcile same-conversation artifacts through the workflow's closure-thread partitions: create a fresh session only when continuation remains without an existing owner, and use `zero-handoff` or `existing-owner` when no replacement reader is needed. Archive only sessions this conversation owns, and leave unrelated or ambiguous sessions untouched. Creating a new `todo` entry is valid only after this search shows no existing owner or only superseded same-conversation artifacts, and continuation by Claude is impossible now.

Closing a thread without creating a session file is appropriate when its workflow 02 `<thread>` record has `continuation="absent"`: its anchored nodes carry no actionable `PLAN.md`, unresolved `ISSUES.md` entry, `spx/EXCLUDE` entry, declared-but-unsatisfied assertion, or external blocker. It is also appropriate when that record has `owner_status="existing-owner"`, confirming another session carries the thread's continuation. A persisted coordination note that represents no future work is removed during closure, because a note no one will act on is deleted, not kept.

`--no-session` never authorizes skipping a thread whose record has `continuation="present"` without an existing owner. Surface that thread-specific contradiction in workflow 04 Path A — automation never skips a required continuation reader on the user's behalf. A thread with `continuation="absent"` omits its session file even for a plain merge lifecycle invocation. Every fresh session is written only after the existing-session search classifies its thread.

<no_excuses>

When the invocation of **`spx session handoff` refuses to create a session file,** e.g. on a linked worktree that is not cleanly detached at `origin/<default-branch>` because the persist-then-detach precondition is unmet (see `${CLAUDE_SKILL_DIR}/workflows/04-execute.md` `<release_work_branch>`), address the problem by properly executing `${CLAUDE_SKILL_DIR}/workflows/04-execute.md` rather than rationalizing that no session file is needed.

The refusal is not satisfied by **relocating** — running the handoff from a different worktree that is already clean while the work worktree keeps its branch. That records `git_ref` at unrelated state and leaves the work branch occupied, so `/pickup` cannot claim it: the handoff then points at the wrong place AND strands the work. The "keep the work worktree on its branch so it's ready to continue" instinct is the trap — that worktree is exactly the one the next agent cannot use. Step the worktree that holds the work off the branch — commit, push the work branch, detach it to `origin/<default-branch>` — and run the handoff there, so the recorded anchor and the freed branch both point at the work.

**Foreign-pool guardrail.** The worktree that holds the work is always one in Claude's own pool. Never relocate the work into, or run the handoff against, a `.spx/` pool Claude does not participate in — another product's checkout. A foreign pool's worktree is off-limits regardless of how free its git state looks; treat it as occupied, because the claim protocol coordinates only agents that share one pool. Relocating a continuation into a separate live product's pool is the exact boundary this guardrail exists to stop.

</no_excuses>

</session_file_purpose>

<claimed_session_invariants>
Three rules govern a conversation's claimed-session set:

1. The claimed-session set grows only by user confirmation (via `/pickup`).
2. Closure has exactly one acceptable end state per claimed session: archived after this workflow runs against it.
3. Quick-release shortcut via `/handoff --no-session` for a wrongly-claimed session the user releases within a few turns of pickup — valid only when every affected thread carries no actionable coordination note or do-able continuation, so each record has `continuation="absent"`.

Permission to archive comes from completing this workflow against the claimed-session set named in `<CLAIMED_SESSIONS ids="…">` — never from queue inspection. A handoff replaces incorporated context, never supplements it. Mid-session session files created by this conversation are workflow artifacts, not members of the claimed-session set.

Full algorithm in `${CLAUDE_SKILL_DIR}/references/claimed-session-resolution.md`.

</claimed_session_invariants>

<persistence_hierarchy>
Persist to the HIGHEST applicable tier.

| Tier | Where                                   | Durability                 | When to use                                                                                                                                                                                           |
| ---- | --------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Methodology (skills, CLAUDE.md)         | Durable                    | Reusable patterns, gotchas, clarifications etc.                                                                                                                                                       |
| 2    | Spec tree (`spx/`)                      | Durable                    | New or updated durable spec tree files such as decisions, specs and tests                                                                                                                             |
| 3    | Coordination notes (PLAN.md, ISSUES.md) | Until resolved or disposed | Remaining steps, known gaps and defects — committed for cross-session coordination. CAUTION: coordination notes are prone to go stale; always reconcile before use, discoverable via `/contextualize` |
| 4    | Session file                            | Ephemeral                  | Coordination only: node list, first action, external-infrastructure state, cross-cutting context                                                                                                      |

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
- `--no-session`: complete all workflows as mandated by this skill, including persisting coordination notes on a remote branch and archiving potentially claimed sessions. Claude skips only thread records with `continuation="absent"` or `owner_status="existing-owner"`. It never overrides a thread with `continuation="present"` and no existing owner — workflow 04 Path A surfaces that thread-specific contradiction instead of silently skipping.
- `--prune`: after a fresh handoff is created and archived-session cleanup is approved, delete archived sessions. Ignored when no fresh handoff is created.

Parse the whole invocation string `$ARGUMENTS` once before starting the workflows:

1. Split the trimmed string on whitespace. Empty `$ARGUMENTS` means both flags are absent.
2. Accept only `--no-session` and `--prune`, in either order.
3. Reject an unknown token or a duplicate flag before any repository, session, or external mutation. Report the invalid token and the accepted forms.
4. Emit exactly one normalized marker for the workflows:

```text
<HANDOFF_OPTIONS no_session="true|false" prune="true|false" />
```

Every option-dependent workflow reads the normalized marker rather than re-parsing `$ARGUMENTS`.

</arguments>

<required_reading>

Read these bundled references before executing the workflows:

- `${CLAUDE_SKILL_DIR}/references/claimed-session-resolution.md` — authoritative claimed-session and same-conversation artifact resolution
- `${CLAUDE_SKILL_DIR}/references/session-format.md` — canonical session payload, stdin forms, and stored-field verification

</required_reading>

<workflows>
Execute all four workflows in sequence. Each workflow has its own success criteria — do not proceed to the next until the current one is complete. Workflow 04 persists all work and coordination notes, then writes a session file only when a continuation reader is needed.

1. `${CLAUDE_SKILL_DIR}/workflows/01-anchor-to-nodes.md` — identify every node worked on this session
2. `${CLAUDE_SKILL_DIR}/workflows/02-reflect.md` — review imperfections, claimed sessions, and starting point
3. `${CLAUDE_SKILL_DIR}/workflows/03-propose.md` — present persistence proposal to user for approval
4. `${CLAUDE_SKILL_DIR}/workflows/04-execute.md` — create or update coordination notes, commit, then write or omit each thread's canonical continuation session file

</workflows>

<failure_modes>

**Continuation written before durable persistence.** Claude created the session file before approved coordination, spec, test, code, or generated-output changes were committed and pushed. Return to workflow 04 persistence, commit session-owned files first, push the work branch when it exists, then create the canonical continuation.

**Branch left occupied after handoff.** Claude wrote a continuation with a work-branch `git_ref` and kept the releasing worktree checked out on that same branch. Step off per `${CLAUDE_SKILL_DIR}/workflows/04-execute.md` `<release_work_branch>` so `/pickup` can claim the branch in another worktree.

**Multiple canonical continuations kept for one thread.** Claude created a new handoff while a mid-session artifact still described the same continuation. Reconcile the artifacts: create one fresh canonical handoff, archive every superseded same-conversation artifact, and leave exactly one canonical TODO session for the thread.

**Archive or prune touched unrelated sessions.** Claude archived a session outside `<RESOLVED_CLAIMED_SESSIONS>` or deleted a TODO/doing session during `--prune`. Stop, restore the queue state before continuing, archive only resolved claimed sessions and superseded mid-session artifacts, and prune archive entries only.

</failure_modes>

<success_criteria>

A closure or handoff is sound when:

- Every session-owned change and coordination decision is recoverable from committed, published repository state before any continuation document points at it.
- The continuation disposition matches observable state: no session when no reader is needed, one fresh canonical session per independent continuation thread when work cannot continue now, and no duplicate or mutated session artifact.
- Every claimed session and superseded same-conversation artifact is archived only after its replacement is verified or zero-handoff closure is established; unrelated and ambiguous sessions remain untouched.
- Any created session is a thin coordination envelope whose repository anchors, first action, and external-state facts let `/pickup` re-derive current truth without copying durable content.
- The operator-facing closeout explains product value and changed surface in product language, reports exact verification and inspection evidence, states delivered location and remaining work, and classifies every merge-lifecycle branch with full identities.

</success_criteria>
