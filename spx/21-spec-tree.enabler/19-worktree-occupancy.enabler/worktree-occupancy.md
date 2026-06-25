# Worktree Occupancy

PROVIDES `/pickup` and `/handoff` coordination of bare-repository pool worktree occupancy through the `spx worktree` CLI
SO THAT concurrent agents sharing one `.spx/` pool
CAN enter only a worktree no live agent holds, instead of inferring occupancy from git cleanliness

The `/pickup` and `/handoff` skills coordinate occupancy entirely through the `spx` CLI — `spx worktree status`, `spx worktree claim`, and `spx worktree release` — and never read or write the `.spx/worktrees/` claim store directly. How `spx` records a claim and decides whether a worktree is held by a live agent is `spx`'s concern, specified in the `spx` CLI's own spec tree; this node specifies only the plugins' use of that capability. The bare-repository pool these skills operate within is governed by `spx/21-spec-tree.enabler/11-repository-layout.pdr.md` and provisioned by `spx/21-spec-tree.enabler/12-worktree-provisioning.enabler`.

## Assertions

### Compliance

- ALWAYS: `/pickup` reads worktree occupancy through `spx worktree status` before checking a work branch out into a pool worktree, claims the worktree it enters through `spx worktree claim --session-id <id>`, and enters only a worktree `spx` reports as not held by a live agent ([audit])
- ALWAYS: `/handoff` releases the running worktree's claim through `spx worktree release` as it closes the session, so the worktree is available for the next agent to claim ([audit])
- NEVER: a plugin reads, writes, or removes a `.spx/worktrees/` claim by direct filesystem access — occupancy is reached only through the `spx` CLI (`spx worktree` from the `/pickup` and `/handoff` skills, and `spx hook run session-start` from the `SessionStart` hook) ([audit])
- NEVER: an agent operates inside a worktree of a `.spx/` pool it does not participate in — a foreign pool's worktree is off-limits regardless of how free its git state looks, because the claim protocol coordinates only agents that share one pool ([audit])
- ALWAYS: the spec-tree plugin's `SessionStart` hook records the worktree-occupancy claim by delegating to `spx hook run session-start` (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); the hook embeds no claim logic of its own ([audit])
