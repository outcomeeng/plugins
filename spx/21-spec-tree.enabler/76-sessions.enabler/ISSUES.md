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

### Status — marketplace half landed; CLI half remains

The marketplace-repo half is implemented and governed durably:
`spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` records
the decision; `sessions.md` declares the origin-persistence precondition and the
no-relocation-bypass rule (`[audit]`); the `/handoff` skill enforces both — the
`<release_work_branch>` why-driven precondition + push, and the `<no_excuses>`
relocation-bypass naming — the session-format template carries the `work_branch`
anchor, and `/pickup` fetches and checks it out.

**Remaining — the `spx` CLI half (separate repo, `~/Code/outcomeeng/spx/`).** Item 3
above is unfixed: let `spx session handoff` accept an explicit work-branch ref in its
stdin JSON header (recorded as `git_ref`) so a pool-worktree handoff anchors `git_ref`
at the feature branch rather than the `origin/<default>` base SHA. Until then the
marketplace half names the branch in the session body's `work_branch` field. When the
CLI lands, reconcile the `<release_work_branch>` mechanics with the new accepted-context
set and add a `git_ref`-accepts-explicit-ref `[test]` assertion in the `spx` repo's spec.

## Worktree occupancy is undetectable — "clean and detached" is not "free" (gap)

In a bare-repository worktree pool an agent cannot tell whether a worktree is held by a
live agent. Git state is not a reliable signal: a worktree that is clean and detached at
the `origin/<default>` tip can still be actively held — between commits, doing read-only
work, or mid-think. Reading "clean ⇒ free" lets one agent operate inside another live
agent's worktree.

### Why a heartbeat is the wrong fix

A claim refreshed every turn and aged out by a TTL is `O(turns)` of token and IO cost,
and it reinvents something the OS already maintains for free: whether a process is alive.

### What to fix and how

- **Write-once PID claim + on-demand liveness check.** The SessionStart hook (already
  runs) writes a claim once: `.spx/worktrees/<name>.claim = {session_id, host, pid,
  started_at}`, where `pid` is the agent's own controlling process. Occupancy is checked
  on demand — same host AND `kill -0 <pid>` succeeds → occupied; otherwise the holder is
  dead → stale → free. The process table is the liveness signal: no heartbeat, no TTL, no
  refresh. `/handoff` close removes the claim; a crashed agent's stale claim reads as free
  at the next check. Guard PID reuse by comparing `started_at` / boot-id against `ps`.
  Cost is `O(claim events + check events)`, never `O(turns)`.

- **Owner: the `spx` CLI** per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`
  (the CLI is the single owner of `.spx/` state), exposed as `spx worktree
  status/claim/release` and slotting onto the session-scope accumulator in
  `spx/21-spec-tree.enabler/76-sessions.enabler/PLAN.md` — which already maps
  runtime→session via `.spx/sessions/$RUNTIME_ID/`; this adds runtime→worktree. Governed
  by `spx/21-spec-tree.enabler/11-repository-layout.pdr.md` (the pool layout).

- **Zero-infrastructure guardrail (applies now, before the claim mechanism exists):** never
  operate inside another product's pool. A foreign `.spx/` pool is off-limits regardless of
  how free a worktree looks — the claim protocol coordinates agents only within a single
  pool they each participate in. Treat any worktree in a pool you are not a participant in
  as occupied.

**Evidence:** an agent closing a marketplace session relocated a continuation into a
separate live product's worktree pool (`~/Code/outcomeeng/spx/`) — running `spx session
handoff` from that pool's main checkout and moving a pool worktree's HEAD — operating
inside a worktree a live agent held, because "clean + detached" was misread as "free."
