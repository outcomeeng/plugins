# Issues: Sessions Enabler

## Handoff does not enforce origin-branch persistence (BLOCKING gap)

A handoff is only valid when **all work is persisted on an origin branch** and a
session document **points at that branch**. The current `/handoff` skill and the
`sessions.md` spec do not enforce this, so an agent can produce a "handoff" that
a fresh session cannot recover. This actually happened: asked to create a
handoff, the agent produced a **chat-only summary** (no commit, no push, no
session file) and offered to *maybe* persist it. A new session on a clean
checkout — or a different machine — would have recovered nothing.

### Why a non-persisted handoff is worthless

1. Uncommitted WIP in a worktree is invisible to a new session.
2. A session document is a **pointer** — it "initializes the next agent through
   repository-derived pointers… so the next agent re-derives detail from the
   spec tree" (`sessions.md`). If the spec-tree state it points at is not pushed
   to origin, the pointer dangles.
3. A local-only branch is not reachable from another session/checkout/machine.

### Specific gaps

1. **No origin-persistence precondition.** Nothing in the handoff flow asserts
   that the working tree is clean and the work branch is **pushed to origin**
   before the session document is written. The skill should refuse (or first
   commit-and-push) rather than emit a session doc pointing at unrecoverable
   state.

2. **`git_ref` cannot capture a feature branch from a pool worktree.**
   `spx session handoff` gates the git context: from a root worktree on a named
   branch it records the branch name; from a linked (pool) worktree it requires
   a clean detached HEAD at the `origin/<default>` tip and records that SHA,
   refusing any other linked-worktree state (`SessionHandoffBaseError`). In the
   bare-repo worktree pool (`spx/21-spec-tree.enabler/11-repository-layout.pdr.md`)
   feature work lives on a **named branch in a pool worktree** — exactly the
   refused state — while the root `main` worktree must stay on `main`. So **no
   worktree records the feature branch as `git_ref`.** The agent must encode the
   branch in prose, which the skill neither requires nor validates.

3. **The skill does not reject the invalid handoff.** A dirty tree or an unpushed
   branch should make the handoff fail loudly, not silently produce a dangling
   pointer.

### What to fix and how

- **Make origin-persistence a hard precondition.** Add an assertion in
  `sessions.md` (enforced by the `/handoff` skill): a handoff is valid only when
  the working tree is clean AND the work branch's `@{upstream}` exists on origin
  and is not ahead of it. If dirty/unpushed, the skill runs `/committing-changes`
  and pushes the work branch to origin **before** writing the session document.
  "Persist everything on an origin branch, then point at it" becomes the gate.

- **Point the session document at the origin work branch explicitly.** The body
  (and a frontmatter field) must name `origin/<work-branch>` to fetch and the
  pool worktree to check it out in. `/pickup` fetches + checks out that branch in
  a pool worktree before reading the spec tree.

- **Reconcile the git-context gate with the bare-pool layout.** Let
  `spx session handoff` accept an explicit work-branch ref in its stdin JSON
  header (recorded as `git_ref`) rather than only the worktree's own ref, so a
  handoff made from any accepted context can point at a feature branch living in
  a pool worktree. (The current gate makes a faithful feature-branch handoff
  impossible in the pool layout.)

- **Surface the requirement loudly** so an agent never proposes a chat-only or
  local-only handoff — the exact failure that prompted this issue.

**Evidence:** 2026-06-08/09 session. Agent produced a chat-only handoff; operator
corrected that the only valid handoff persists everything on an origin branch and
creates a session file pointing at it. This branch (`work/handoff-lint-enforcement`)
is the corrected handoff and the carrier of this diagnosis.

## Handoff silently honors `--no-session` when continuation work remains (gap)

`sessions.md` line 42 permits closing without a session file "when the user passes
`--no-session`" — treating the flag as an unconditional user-intent escape. But the
PR lifecycle hardcodes it: `/pr` Step 7 (the `pr` skill body and the GitHub-PR
transport's `/pr` orchestration spec, `spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/github-pr.md`)
and `spx/local/merging.md`'s post-merge step both say "run `/handoff --no-session`"
as the fixed post-merge closure. So automation passes a user-intent override on the
user's behalf, and the handoff skill silently honors it — skipping the session file
even when unresolved in-scope continuation work exists. This directly defeats
`sessions.md` lines 41–42 (create a session whenever continuation remains; PLAN.md is
not a substitute).

### What to fix and how

1. **Make `--no-session` answerable to continuation state.** In the handoff skill
   (`workflows/02-reflect.md` computes the signal, `04-execute.md` acts on it),
   detect unresolved in-scope continuation work — node-local `PLAN.md` pending
   items, `spx/EXCLUDE` entries, or declared-but-unimplemented spec assertions
   touched this session. When `--no-session` is passed but that signal is present,
   do NOT silently honor it: surface the contradiction and create the session (or
   require explicit re-confirmation). Amend `sessions.md` line 42 to drop the
   unconditional `--no-session` escape — `--no-session` asserts "there is no
   continuation," never "skip the session regardless."

2. **De-hardcode `--no-session` in the lifecycle.** `/pr` Step 7 (the `pr` skill
   body + `github-pr.md`) and `spx/local/merging.md`'s post-merge step must invoke
   `/handoff` PLAIN. Automation must never pass a user-intent override on the
   user's behalf; the skill decides per `sessions.md` lines 41–42.

Distinct from the origin-branch-persistence gap above (that is about *persisting*
the handoff; this is about the *session-creation decision*), but the same class of
fix — make the handoff's preconditions answerable to state rather than silently
bypassable.

**Evidence:** closing PR #163 (transport-neutral merging, merged 2026-06-12 as
`04ee6ffa`). The agent proposed `/handoff --no-session` following the hardcoded
`/pr` Step 7 default, despite having just authored `76-merging.enabler/PLAN.md` with
deferred continuation (the `/merge` build, `/pr` refocus, direct-push execution, the
eval recalibration). Operator caught it.
