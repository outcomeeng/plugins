# Worktree Occupancy

PROVIDES the `SessionStart` hook's and the Change Lifecycle skills' coordination of bare-repository pool worktree occupancy through the `spx worktree` CLI
SO THAT concurrent agents sharing one `.spx/` pool
CAN keep each agent's work inside its own assigned, hook-claimed worktree and off any worktree a live agent holds, instead of inferring occupancy from git cleanliness

The `SessionStart` hook records the running session's worktree-occupancy claim by delegating to `spx hook run session-start`; `claim-change` then brings a Handoff's work branch into that assigned, hook-claimed worktree, reading occupancy through `spx worktree status` only as a read-only check and recording no claim of its own, and `release-change` preserves the live runtime claim while freeing the Git branch by stepping the checkout off it after the push. These surfaces reach occupancy entirely through the `spx` CLI and never read or write the `.spx/worktrees/` claim store directly. How `spx` records a claim and decides whether a worktree is held by a live agent is `spx`'s concern, specified in the `spx` CLI's own spec tree; this node specifies only the plugins' use of that capability. The assigned-worktree discipline the Lifecycle skills follow — each agent conducts its git work in the assigned, hook-claimed worktree, never entering or creating another — is governed by `spx/15-merging.pdr.md`, and the hook's claim delegation by `spx/21-spec-tree.enabler/13-agent-environment.enabler/` and `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`. The bare-repository pool these skills operate within is governed by `spx/21-spec-tree.enabler/11-repository-layout.pdr.md` and provisioned by `spx/21-spec-tree.enabler/12-worktree-provisioning.enabler`.

## Assertions

### Compliance

- ALWAYS: `claim-change` brings a Handoff's work branch into the assigned, hook-claimed worktree, first confirming through `spx worktree status` (a read-only check that records nothing) that the worktree carries the running session's `SessionStart`-hook claim, and surfacing a diagnostic when the claim is absent rather than recording one of its own ([audit])
- NEVER: a Lifecycle skill records a worktree-occupancy claim by hand (`spx worktree claim`), or enters or creates a pool worktree other than the assigned one — recording the claim is the `SessionStart` hook's sole job, and the agent stays in its assigned worktree and branches there ([audit])
- NEVER: `release-change` releases the running worktree's live claim through `spx worktree release`; it frees the Git branch by stepping the checkout off it after the push, while the live process keeps its occupancy claim until a later claim replaces it or liveness marks it free ([audit])
- NEVER: a plugin reads, writes, or removes a `.spx/worktrees/` claim by direct filesystem access — occupancy is reached only through the `spx` CLI (`spx worktree status` from `claim-change` and `release-change`, and the claim that `spx hook run session-start` records from the `SessionStart` hook) ([audit])
- NEVER: an agent operates inside a worktree of a `.spx/` pool it does not participate in — a foreign pool's worktree is off-limits regardless of how free its git state looks, because the claim protocol coordinates only agents that share one pool ([audit])
- ALWAYS: the spec-tree plugin's `SessionStart` hook records the worktree-occupancy claim by delegating to `spx hook run session-start` (`spx/21-spec-tree.enabler/13-agent-environment.enabler/`); the hook embeds no claim logic of its own ([audit])
