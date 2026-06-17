# Worktree Occupancy

PROVIDES a write-once per-agent worktree claim and an on-demand process-liveness check that reveal whether a bare-repository pool worktree is held by a live agent
SO THAT the session, handoff, pickup, and any flow that enters a pool worktree
CAN distinguish a held worktree from a free one instead of inferring occupancy from git cleanliness

The claim record at `.spx/worktrees/<name>.claim` carries the holding agent's session id, host, controlling-process id, and start time. Occupancy is read on demand from the process table — a same-host claim whose process is alive marks the worktree occupied, and a claim whose process is dead reads as stale and therefore free. The `spx` CLI owns the claim's atomic filesystem I/O, the liveness check, and the process-reuse guard, exposed as `spx worktree status`, `spx worktree claim`, and `spx worktree release`, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`. The bare-repository pool this enabler operates within is governed by `spx/21-spec-tree.enabler/11-repository-layout.pdr.md` and provisioned by `spx/21-spec-tree.enabler/12-worktree-provisioning.enabler`.

## Assertions

### Scenarios

- Given a session starts in a pool worktree with the `spx` CLI present, when the `SessionStart` hook fires, then it records a worktree-occupancy claim for the running worktree by invoking `spx worktree claim` against that worktree ([test](tests/test_worktree_occupancy.scenario.l1.py))
- Given a session starts and the `spx` CLI is absent, exits non-zero, or does not respond within the claim timeout, when the `SessionStart` hook fires, then it records no claim and degrades to a silent no-op ([test](tests/test_worktree_occupancy.scenario.l1.py))
- Given a `PreToolUse` payload in a spec-tree repository and the running worktree status is `stale` or `unclaimed`, when the gate hook fires with a session id and the `spx` CLI present, then it invokes `spx worktree claim --session-id <session-id>` before evaluating the tool gate and adds model-visible context that the claim was repaired ([test](tests/test_worktree_occupancy.scenario.l1.py))

### Compliance

- ALWAYS: `/pickup` reads worktree occupancy through `spx worktree status` before checking a work branch out into a pool worktree, and enters only a worktree that is unclaimed or whose claim is stale — never one a live agent holds ([audit])
- ALWAYS: `/handoff` removes the running worktree's claim through `spx worktree release` as it closes the session, so the released worktree reads as free for the next agent to claim ([audit])
- ALWAYS: occupancy is decided by process liveness on demand, not by git state and not by a refresh timer — a claim whose holder is alive on the same host marks the worktree occupied, a claim whose holder is dead reads as stale and therefore free, and a clean worktree detached at the default-branch tip is never inferred free without reading its claim ([audit])
- NEVER: an agent operates inside a worktree of a `.spx/` pool it does not participate in — a foreign pool's worktree is treated as occupied regardless of how free its git state looks, because the claim protocol coordinates only agents that share one pool ([audit])
- ALWAYS: every read, write, or removal of a `.spx/worktrees/` claim is performed by the `spx` CLI invoked as `spx worktree`; the `SessionStart` hook and the `/handoff` and `/pickup` skills reach claim state only through that subprocess, never by direct filesystem access, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ([audit])
