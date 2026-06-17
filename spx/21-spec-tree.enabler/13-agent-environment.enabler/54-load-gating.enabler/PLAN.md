# PLAN: Load-gating mechanism

The full design and scope rationale live in the parent
`spx/21-spec-tree.enabler/13-agent-environment.enabler/PLAN.md`. This node is converted to
the `spx hooks pre-tool-use` model: the plugin ships only the `PreToolUse` wiring entry,
and `spx hooks pre-tool-use` owns boundary detection, the marker scan, path-to-node
mapping, the worktree-occupancy refresh, and the allow-or-deny verdict, emitting the
`PreToolUse` decision plus a `specTree` descriptor per
`spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`.

## Remaining (separate repo: `@outcomeeng/spx`)

`spx hooks pre-tool-use` must be implemented to the contract in
`load-gating.md`, then published to npm with the `REQUIRED_SPX_VERSION` floor advanced and
CI `SPX_VERSION` bumped. Until then this node stays in `spx/EXCLUDE`; remove its entry when
the floor reaches the publishing release.

- **Boundary linchpin.** Scan only the transcript region after the most recent
  session-start / compaction boundary; a marker preserved only in a pre-compaction summary
  never satisfies a gate.
- **Gate A (foundation).** Deny the first tool call after the boundary while no
  `<SPEC_TREE_FOUNDATION>` marker exists in the segment; allowlist the
  `/spec-tree:understand` invocation that emits it; let purely-external tools pass.
- **Gate B (context).** Deny `Edit`/`Write`/mutating `Bash` whose path resolves under a
  spec-tree node while no `<SPEC_TREE_CONTEXT target="<node>">` for the owning node exists
  in the segment.
- **Verdict shape.** Emit the runtime's native `permissionDecision` envelope plus a
  `specTree` descriptor carrying `{ decision, owning_node, gate }`.
