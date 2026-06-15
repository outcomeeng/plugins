# PLAN: Worktree-occupancy mechanism

## State

The marketplace half is implemented and verified; only the `spx` CLI half remains, in a separate repository. The settled design lives in `spx/21-spec-tree.enabler/76-sessions.enabler/ISSUES.md` ("Worktree occupancy is undetectable") — write-once PID claim + on-demand `kill -0`, no heartbeat, no TTL.

## Marketplace half (this repo) — landed

- `worktree-occupancy.md` declares the mechanism; the node is out of `spx/EXCLUDE` and its `[test]` assertions pass.
- The `SessionStart` hook (`src/plugins/spec-tree/scripts/session-start.py`) records the claim via `spx worktree claim`, no-ops when the CLI is absent or exits non-zero; covered by `tests/test_worktree_occupancy.scenario.l1.py` and the hermetic `outcomeeng_testing/harnesses/hooks.py` (`SPX_BIN` defaults to a missing binary).
- `/handoff` releases the claim (`spx worktree release`) on close; `/pickup` reads `spx worktree status` before entering a pool worktree and enters only an unclaimed-or-stale one; both state the foreign-pool guardrail.
- `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` is reconciled to admit the `spx worktree claim` subprocess while keeping the only direct hook write `$CLAUDE_ENV_FILE`.
- Gates passed: `spec-tree:adr-auditor` (ADR), `/aligning` (node), `spec-tree:test-evidence-auditor` (tests), `python:python-code-auditor` (hook + harness), `develop:skill-auditor` (handoff, pickup).

## `spx` CLI half (`~/Code/outcomeeng/spx/`) — remaining

- `spx worktree status` / `spx worktree claim` / `spx worktree release` commands.
- Atomic `.spx/worktrees/<name>.claim` I/O writing `{session_id, host, pid, started_at}`.
- On-demand liveness: same-host `kill -0 <pid>` → occupied; dead → stale → free. No heartbeat, no TTL, no refresh.
- Process-reuse guard: compare `started_at` / boot-id against `ps` so a reused PID is not misread as the original holder.
- The CLI owns all `.spx/worktrees/` filesystem I/O per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`; the marketplace hook and skills reach it only as a subprocess.

This half slots onto the per-runtime accumulator (`.spx/sessions/$RUNTIME_ID/`, runtime→session) by adding runtime→worktree; do not conflate the two. The marketplace hook and skills already invoke `spx worktree`, degrading silently until the CLI ships the subcommand.
