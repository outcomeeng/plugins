# Load Gating

PROVIDES mechanical `PreToolUse` gates that deny a tool call until the methodology foundation and the edited node's context are loaded since the most recent session-start or compaction boundary
SO THAT every agent acting in a spec-tree repository, including one resuming after a compaction whose continuation prompt frames the work as "resume as if the break never happened"
CAN be stopped from investigating or editing on unloaded methodology, rather than depending on an injected directive the harness resume prompt out-prioritizes

A gate hook on `PreToolUse` forwards the tool name, the tool's path argument when present, the session id, and the transcript path to the `spx` CLI, which scans the transcript after the most recent session-start or compaction boundary for the `<SPEC_TREE_FOUNDATION>` marker (the foundation gate) and the `<SPEC_TREE_CONTEXT target="<node>">` marker (the context gate), maps an edited path to its owning node, and returns an allow-or-deny verdict with a denial message. The hook emits the `PreToolUse` decision and degrades to allowing the call when the CLI is absent. Before evaluating the gate, the same `PreToolUse` hook refreshes stale or unclaimed worktree occupancy through the `spx worktree` CLI contract declared in `spx/21-spec-tree.enabler/19-worktree-occupancy.enabler/worktree-occupancy.md`. The `spx` CLI owns the transcript I/O, `.spx/` state I/O, boundary detection, marker scan, path-to-node mapping, and verdict per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`; the principle of keying enforcement on tracked load-state rather than on work category or path-noticing is governed by `spx/21-spec-tree.enabler/13-agent-environment.enabler/54-load-gating.enabler/13-enforcement-state.adr.md`. Spec-tree detection reuses the `spx/*.product.md` convention of `spx/21-spec-tree.enabler/13-agent-environment.enabler/21-understanding-directive.enabler`, and the boundary the gate scopes against is the same compaction boundary governed by `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md`.

## Assertions

### Scenarios

- Given a `PreToolUse` payload in a spec-tree repository and a `spx` CLI that returns a deny verdict, when the gate hook runs, then it emits a `PreToolUse` deny decision carrying the CLI's verdict message ([test](tests/test_load_gating.scenario.l1.py))
- Given a `spx` CLI that returns an allow verdict, when the gate hook runs, then it emits no denial and the tool call proceeds ([test](tests/test_load_gating.scenario.l1.py))
- Given the `spx` CLI is absent, exits non-zero, or exceeds the gate timeout, when the gate hook runs, then it degrades to allowing the call and emits no denial ([test](tests/test_load_gating.scenario.l1.py))
- Given the `spx` CLI exits zero but returns stdout the gate cannot parse as a verdict, when the gate hook runs, then it degrades to allowing the call and emits no denial ([test](tests/test_load_gating.scenario.l1.py))
- Given a `PreToolUse` payload that carries no tool name, when the gate hook runs, then it allows the call and does not invoke the `spx` CLI ([test](tests/test_load_gating.scenario.l1.py))
- Given a project directory that is not a spec-tree repository (no `spx/*.product.md`), when the gate hook runs, then it allows the call and does not invoke the `spx` CLI ([test](tests/test_load_gating.scenario.l1.py))
- Given a `PreToolUse` payload, when the gate hook invokes the `spx` CLI, then it forwards the tool name, each path-bearing tool argument present (`file_path` as `--path`, a `Bash` `command` as `--command`), the session id, and the transcript path, and does not read or parse the transcript itself — the CLI performs that I/O ([test](tests/test_load_gating.scenario.l1.py))

### Compliance

- ALWAYS: gate occupancy is decided over the transcript region after the most recent session-start or compaction boundary — a `<SPEC_TREE_FOUNDATION>` or `<SPEC_TREE_CONTEXT>` marker that survives only in a pre-compaction summary never satisfies a gate ([audit])
- ALWAYS: the foundation gate denies the first tool call after a boundary while no `<SPEC_TREE_FOUNDATION>` marker exists in the current segment, allowlisting the `/spec-tree:understanding` invocation that emits the marker and letting purely-external tools pass ([audit])
- ALWAYS: the context gate denies an `Edit`, `Write`, or mutating `Bash` call whose path resolves under a spec-tree node while no `<SPEC_TREE_CONTEXT target="<node>">` marker for that owning node exists in the current segment, where the owning node is the nearest ancestor directory of the path that is an `*.enabler` or `*.outcome` ([audit])
- ALWAYS: boundary detection, the marker scan, the path-to-node mapping, and the verdict are performed by the `spx` CLI invoked as a subprocess; the gate hook forwards locators and emits the decision, holding no gate logic, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ([audit])
- NEVER: a gate keys its decision on the work category the agent believes it is performing or on the agent noticing a path — the gate reads tracked load-state and the hook reads the tool's path argument, so the agent's attention is never the trigger, per `spx/21-spec-tree.enabler/13-agent-environment.enabler/54-load-gating.enabler/13-enforcement-state.adr.md` ([audit])
