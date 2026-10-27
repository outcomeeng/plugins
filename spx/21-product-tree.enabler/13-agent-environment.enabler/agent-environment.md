---
id: 01a0ebba-5f5b-7111-b282-43243ce96573
malleability: spec
---

# Agent Environment

PROVIDES a stable per-agent session identity and a per-runtime session directory keyed on it
SO THAT concurrent agent sessions sharing one `.spx/`
CAN scope work to the current agent without file-system heuristics or race conditions

The product-tree plugin's only runtime hook event is `SessionStart`, with two entries. The delegating entry, on every source, delegates to the `spx` CLI hook runner — `spx hook run <hook-name-kebab-case>`, here `spx hook run session-start` — through a hook-safety-compliant inline guard. On the normal path the `spx` hook runner delivers the session environment: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim. On the disabled-or-absent path the guard exits with a valid empty result and writes nothing. The compact entry, matched on `compact`, prints the post-compaction reminder resource the foundation-resource manifest names in its `compact_recovery` entry, found under the plugin root, through the shell's own read of that file; when the kill switch is set or the resource is unreadable it exits with a valid empty result and prints nothing. The plugin owns only the hook's wiring and its fail-open guard; it embeds no `.spx/`, git, transcript, or session logic of its own, per [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md) and [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md). The identity's distinctness and the per-session directory the `spx` CLI realizes are its own contract, verified by its suite; this node verifies the plugin's integration with it. This node holds the hook-wide constraint that spans its children.

## Assertions

### Scenarios

- Given a `SessionStart` payload and `spx` resolvable on `PATH`, when the delegating entry's command runs, then the `spx` hook runner delivers the session environment — `CLAUDE_SESSION_ID` reaches `$CLAUDE_ENV_FILE` and a worktree-occupancy claim is recorded under the project's `.spx/worktrees/` ([test](tests/test_agent_environment.scenario.l1.py))
- Given the kill switch `PRODUCT_TREE_SESSION_HOOK_DISABLED=1`, when the delegating entry's command runs, then it exits with a valid empty result and writes nothing — no identity, no claim, no `.spx/` state ([test](tests/test_agent_environment.scenario.l1.py))
- Given `spx` is unresolvable on `PATH`, when the delegating entry's command runs, then it exits with a valid empty result and writes nothing — the fail-open safety net for a consumer without `spx` installed ([test](tests/test_agent_environment.scenario.l1.py))
- Given the delegating entry runs end-to-end against the real `spx` CLI in a git worktree with the session's controlling process alive, when it completes, then `$CLAUDE_ENV_FILE` carries the correct values — `CLAUDE_SESSION_ID` for the payload and the resolved `CLAUDE_PROJECT_DIR` and `PROJECT_DIR` — and `spx worktree status` reports the worktree `running`, so spx itself recognizes the claim the entry recorded ([test](tests/test_agent_environment.scenario.l3.py))

- Given the reminder resource the foundation-resource manifest names in its `compact_recovery` entry is readable under the plugin root, when the compact entry's command runs, then it prints that resource's text and nothing else ([test](tests/test_agent_environment.scenario.l1.py))
- Given the kill switch `PRODUCT_TREE_SESSION_HOOK_DISABLED=1`, when the compact entry's command runs, then it exits with a valid empty result and prints nothing ([test](tests/test_agent_environment.scenario.l1.py))
- Given the reminder resource is unreadable under the plugin root, when the compact entry's command runs, then it exits with a valid empty result and prints nothing ([test](tests/test_agent_environment.scenario.l1.py))

### Conformance

- The product-tree plugin's `hooks.json` declares exactly one hook event — `SessionStart` — with two entries: the first, on every source, delegates to `spx hook run session-start` and names no plugin-shipped script path, and the second, matched on `compact`, names the shell's own read of the reminder resource found under the plugin root and names no script ([test](tests/test_agent_environment.conformance.l1.py))

### Compliance

- ALWAYS: the delegating `SessionStart` entry delegates session-identity, project-dir, and worktree-occupancy work to the `spx` CLI hook runner and embeds no `.spx/`, git, transcript, or session logic of its own; on the disabled-or-absent path it exits with a valid empty result, per [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md) ([audit])
- ALWAYS: the delegating `SessionStart` entry declares a 30-second timeout, the bound inside which `spx hook run session-start` finishes under the host load an orchestrated worktree pool produces, and the compact entry declares an explicit timeout of its own, per [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md) ([audit])
- NEVER: the compact entry's command runs a script, the `spx` CLI, or an external command, embeds `.spx/`, git, transcript, or session logic, or prints anything other than the reminder resource ([test](tests/test_agent_environment.compliance.l1.py))
- ALWAYS: the reminder resource the compact entry prints states the facts of the post-compaction reminder and instructs no step, per [`spx/21-product-tree.enabler/16-compact-continuity.pdr.md`](spx/21-product-tree.enabler/16-compact-continuity.pdr.md) ([audit])
- NEVER: the `SessionStart` hook carries compact-summary behavior; it is limited to session-environment, worktree-occupancy, and post-compaction reminder behavior, per [`spx/21-product-tree.enabler/16-compact-continuity.pdr.md`](spx/21-product-tree.enabler/16-compact-continuity.pdr.md) ([audit])
