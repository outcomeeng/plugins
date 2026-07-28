# Plan: provisioning after the worktree lifecycle lands in the SPX CLI

The worktree lifecycle — creating a pool worktree on demand, archiving it,
restoring it, disposing of it — is `spx worktree` behavior, and `spx` is a
separate product with its own spec tree. This node's sibling
`spx/21-spec-tree.enabler/19-worktree-occupancy.enabler` already records the
boundary: how `spx` manages a worktree is `spx`'s concern, and a node here
specifies only the plugins' use of that capability. The lifecycle design is
filed in the `spx` queue as handoff `2026-07-28_05-56-33`; no decision in this
repository declares it.

The published `@outcomeeng/spx` CLI exposes `spx worktree claim`, `status`, and
`release` only. Per the root guide a capability is available here only once it
is published to npm, `REQUIRED_SPX_VERSION` in
`outcomeeng/validation/spx_version.py` advances to it, and `SPX_VERSION` in
`.github/workflows/check.yml` is bumped at or above the floor. No skill or
script here may invoke a lifecycle verb before then.

## Pending, once `spx` decides and publishes the lifecycle

- Whatever this node still owes is the *plugins' use* of the published verbs —
  which skill invokes them and when — expressed as assertions here. The verbs
  themselves are specified in the `spx` tree, not restated in this one.
- If the published lifecycle populates the live set on demand, provisioning
  keeps only its migration role: classify, push every local ref, bare-clone,
  place the main checkout, carry gitignored state, hand off the husk. The
  `init-worktrees` skill's pool-name gathering and its `--worktree` flag, and
  the tests that request N worktrees and assert N exist, follow that change —
  not this note. None of it moves before the capability publishes.
- Renaming this node and the skill to match a migration-only role is a
  `/refactor` operation, not an edit, and waits on the same trigger.

Provisioning a *fresh* pool needs no migration at all — a bare clone plus one
`git worktree add` for the main checkout, with no husk, no ref push, and no
gitignored carry. The 476-line provisioner exists for the retrofit case, which
is the exception rather than the main flow; its extraction is tracked in this
node's `ISSUES.md` behind the same publish gate.
