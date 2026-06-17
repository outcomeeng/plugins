# Load Gating

PROVIDES mechanical `PreToolUse` gates that deny a tool call until the methodology foundation and the edited node's context are loaded since the most recent session-start or compaction boundary
SO THAT every agent acting in a spec-tree repository, including one resuming after a compaction whose continuation prompt frames the work as "resume as if the break never happened"
CAN be stopped from investigating or editing on unloaded methodology, rather than depending on an injected directive the harness resume prompt out-prioritizes

`spx hooks pre-tool-use`, invoked directly by the runtime on every tool call, scans the transcript after the most recent session-start or compaction boundary for the `<SPEC_TREE_FOUNDATION>` marker (the foundation gate) and the `<SPEC_TREE_CONTEXT target="<node>">` marker (the context gate), maps an edited path to its owning node, and emits the `PreToolUse` permission decision in the hook JSON document with a `specTree` descriptor carrying the decision, the owning node, and which gate fired. It owns the transcript I/O, `.spx/` state I/O, boundary detection, marker scan, path-to-node mapping, and verdict per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`; the principle of keying enforcement on tracked load-state rather than on work category or path-noticing is governed by `spx/21-spec-tree.enabler/13-agent-environment.enabler/54-load-gating.enabler/13-enforcement-state.adr.md`. Before evaluating the gate it refreshes stale or unclaimed worktree occupancy per `spx/21-spec-tree.enabler/19-worktree-occupancy.enabler/worktree-occupancy.md`, skipping that repair when the session environment already records a successful session-start claim. Spec-tree detection reuses the `spx/*.product.md` convention of `spx/21-spec-tree.enabler/13-agent-environment.enabler/21-understanding-directive.enabler`, and the boundary the gate scopes against is the compaction boundary governed by `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md`.

## Assertions

### Scenarios

- Given a `PreToolUse` payload in a spec-tree repository whose current segment lacks a `<SPEC_TREE_FOUNDATION>` marker, when `spx hooks pre-tool-use` runs, then its JSON document carries a `permissionDecision` of `deny` and a `specTree` descriptor naming the foundation gate ([test](tests/test_load_gating.scenario.l1.py))
- Given a `PreToolUse` payload whose current segment carries the markers the gate requires, when `spx hooks pre-tool-use` runs, then its JSON document carries a `permissionDecision` of `allow` and the tool call proceeds ([test](tests/test_load_gating.scenario.l1.py))
- Given a `PreToolUse` payload that carries no tool name, when `spx hooks pre-tool-use` runs, then it allows the call ([test](tests/test_load_gating.scenario.l1.py))
- Given a project directory that is not a spec-tree repository (no `spx/*.product.md`), when `spx hooks pre-tool-use` runs, then it allows the call ([test](tests/test_load_gating.scenario.l1.py))

### Compliance

- ALWAYS: boundary detection, the marker scan, the path-to-node mapping, and the verdict are performed by `spx hooks pre-tool-use`; the spec-tree plugin ships no gate logic in any script, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ([audit])
- ALWAYS: gate occupancy is decided over the transcript region after the most recent session-start or compaction boundary — a `<SPEC_TREE_FOUNDATION>` or `<SPEC_TREE_CONTEXT>` marker that survives only in a pre-compaction summary never satisfies a gate ([audit])
- ALWAYS: the foundation gate denies the first tool call after a boundary while no `<SPEC_TREE_FOUNDATION>` marker exists in the current segment, allowlisting the `/spec-tree:understand` invocation that emits the marker and letting purely-external tools pass ([audit])
- ALWAYS: the context gate denies an `Edit`, `Write`, or mutating `Bash` call whose path resolves under a spec-tree node while no `<SPEC_TREE_CONTEXT target="<node>">` marker for that owning node exists in the current segment, where the owning node is the nearest ancestor directory of the path that is an `*.enabler` or `*.outcome` ([audit])
- NEVER: a gate keys its decision on the work category the agent believes it is performing or on the agent noticing a path — the gate reads tracked load-state and `spx hooks pre-tool-use` reads the tool's path argument, so the agent's attention is never the trigger, per `spx/21-spec-tree.enabler/13-agent-environment.enabler/54-load-gating.enabler/13-enforcement-state.adr.md` ([audit])
