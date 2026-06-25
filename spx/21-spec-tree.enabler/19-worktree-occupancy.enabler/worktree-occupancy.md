# Worktree Occupancy

PROVIDES a write-once per-agent worktree claim and an on-demand process-liveness check that reveal whether a bare-repository pool worktree is held by a live agent
SO THAT the session, handoff, pickup, and any flow that enters a pool worktree
CAN distinguish a held worktree from a free one instead of inferring occupancy from git cleanliness

The claim record at `.spx/worktrees/<name>.claim` carries the holding agent's session id, host, controlling-process id, and start time. Occupancy is a stateless two-state classification read on demand from the process table — a same-host claim whose process is alive marks the worktree `running`, and a worktree with no claim or whose claiming process is dead reads as `free`. The `spx` CLI owns the claim's atomic filesystem I/O, the liveness check, and the process-reuse guard, exposed as `spx worktree status`, `spx worktree claim`, and `spx worktree release`; the `/pickup` and `/handoff` skills reach claim state only through that CLI, never a runtime hook. The bare-repository pool this enabler operates within is governed by `spx/21-spec-tree.enabler/11-repository-layout.pdr.md` and provisioned by `spx/21-spec-tree.enabler/12-worktree-provisioning.enabler`.

## Assertions

### Compliance

- ALWAYS: `/pickup` reads worktree occupancy through `spx worktree status` before checking a work branch out into a pool worktree, claims that worktree through `spx worktree claim --session-id <id>`, and enters only one that reads `free` — never one a live agent holds (`running`) ([audit])
- ALWAYS: `/handoff` removes the running worktree's claim through `spx worktree release` as it closes the session, so the released worktree reads as free for the next agent to claim ([audit])
- ALWAYS: occupancy is decided by process liveness on demand, not by git state and not by a refresh timer — a claim whose holder is alive on the same host marks the worktree `running`, a worktree with no claim or whose holder is dead reads as `free`, and a clean worktree detached at the default-branch tip is never inferred `free` without reading its claim ([audit])
- NEVER: an agent operates inside a worktree of a `.spx/` pool it does not participate in — a foreign pool's worktree is treated as `running` regardless of how free its git state looks, because the claim protocol coordinates only agents that share one pool ([audit])
- ALWAYS: every read, write, or removal of a `.spx/worktrees/` claim is performed by the `spx` CLI — `spx worktree` from the `/handoff` and `/pickup` skills, and `spx hook run session-start` from the `SessionStart` hook — never by direct filesystem access ([audit])
- ALWAYS: the spec-tree plugin's `SessionStart` hook records the worktree-occupancy claim by delegating to `spx hook run session-start` (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); the hook embeds no claim logic of its own — the `spx` CLI hook runner performs the claim on session start, the same owner `spx worktree claim` uses for `/pickup` on work entry ([audit])
