# Issues: Sessions Enabler

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

### Status — marketplace half landed; CLI half remains

The marketplace-repo half is implemented and governed durably as its own node,
`spx/21-spec-tree.enabler/19-worktree-occupancy.enabler`: `worktree-occupancy.md` declares
the write-once PID claim and on-demand liveness mechanism (out of `spx/EXCLUDE`, its `[test]`
assertions passing); the `SessionStart` hook records the claim via `spx worktree claim` and
no-ops when the CLI is absent; `/handoff` releases it via `spx worktree release` and `/pickup`
reads `spx worktree status` before entering a pool worktree, entering only an unclaimed-or-stale
one; and `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` admits the `spx worktree
claim` subprocess while keeping the SessionStart hook's only direct write `$CLAUDE_ENV_FILE`.
The settled design in this section is the design-of-record that node references.

**Remaining — the `spx` CLI half (separate repo, `~/Code/outcomeeng/spx/`).** The
`spx worktree status` / `spx worktree claim` / `spx worktree release` commands, the atomic
`.spx/worktrees/<name>.claim` I/O writing `{session_id, host, pid, started_at}`, the on-demand
same-host `kill -0 <pid>` liveness check, and the process-reuse guard land in that repo via its
own coordination. Until they ship, the marketplace hook and skills invoke `spx worktree` and
degrade silently. The zero-infrastructure foreign-pool guardrail above applies now, before the
CLI lands.
