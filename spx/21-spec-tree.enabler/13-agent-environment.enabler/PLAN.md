# PLAN: Move hook behavior into `spx hooks <event>`

## Decision (settled with the operator)

A spec-tree hook event, once converted, contributes only the runtime hook-wiring entry
mapping it to `spx hooks <event>`. `spx hooks <event>` owns the entire behavior:
spec-tree detection, git base-staleness inspection, `.spx/` and transcript I/O, the
`$CLAUDE_ENV_FILE` write, worktree-occupancy claim/refresh, queued-work query, directive
assembly, and the load-gate verdict.

The integration contract is the **process exit signal plus one stdout JSON document** in
the runtime's native hook-output schema, optionally carrying a `specTree` descriptor the
runtime ignores. Consumers (the runtime and this repo's tests) validate JSON and read key
values; they NEVER scan stdout for substrings. `spx` is a precondition for spec-tree
operation, so there is **no degrade-to-no-op** — an absent `spx` is a broken installation
surfaced by the runtime's hook error.

### `specTree` descriptor (what this repo's tests assert)

`spx hooks session-start` emits the native envelope plus:

```json
{
  "hookSpecificOutput": { "hookEventName": "SessionStart", "additionalContext": "<rendered prose>" },
  "specTree": {
    "directives": [
      { "kind": "understanding" },
      { "kind": "base-currency", "behind_count": 3, "default_branch": "origin/main" },
      { "kind": "queued-work", "sessions": [{ "id": "...", "goal": "...", "next_step": "..." }] }
    ]
  }
}
```

`spx hooks pre-tool-use` emits the native `permissionDecision` envelope plus a `specTree`
descriptor carrying `{ decision, owning_node, gate }`. `spx` detects the runtime from
`$CLAUDE_SESSION_ID` / `$CODEX_THREAD_ID` and emits that runtime's native envelope.

## Scope of this change: the cleanly-excludable events (rationale)

The conversion proceeds node by node because `spx/EXCLUDE` is **node-granular** — a node
is in the quality gate or out of it, whole. A node converts in a given change only if its
**entire `[test]` surface is the hook behavior**, so the whole node excludes cleanly while
its `spx hooks` dependency is unpublished.

- **Converted here — SessionStart + PreToolUse.** Their nodes are 100% hook behavior:
  `21-understanding-directive`, `21-base-currency`, `21-identity`,
  `21-queued-work-discoverability`, `43-session-directory` (SessionStart) and
  `54-load-gating`, `19-worktree-occupancy` (PreToolUse). Each excludes as a whole node.
  These are also the two events the operator reported broken (session-start) and noop
  (gate).
- **Deferred — PreCompact/PostCompact and PostToolUse.** PreCompact/PostCompact behavior
  lives in `76-sessions.enabler`, whose `test_sessions.scenario.l1.py` also covers
  `/handoff`, `/pickup`, and `spx session release` against the **published** `spx session`
  CLI (green). PostToolUse behavior lives in `65-applying.enabler` alongside the TDD-flow
  assertions. Excluding either whole node to defer its unpublished `spx hooks` dependency
  would drop coverage of working, published behavior. Converting them requires first
  **decomposing** the hook behavior into its own excludable child node — separate
  structural work. These hooks also already delegate correctly to `spx`
  (`spx compact store`/`retrieve`) or are pure local logic, so they are not the operator's
  reported pain.

The seam is the repo boundary plus node granularity: this marketplace declares the
contract and ships the wiring; `@outcomeeng/spx` implements `spx hooks <event>`.

## Where the truth enters the lower tree (this change)

- `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` — rewritten to the delegation +
  no-substring-scan + no-degrade contract, scoped to converted events with the rest
  declared converging.
- `13-agent-environment.enabler/agent-environment.md` — parent gains the **green**
  wiring-conformance `[test]` (hooks.json maps SessionStart/PreToolUse to `spx hooks` and
  the `session-start`/`load-gate` scripts are gone).
- SessionStart children re-specced to the descriptor contract; tests retargeted to invoke
  `spx hooks session-start` + parse JSON: `21-understanding-directive`, `21-base-currency`,
  `21-identity` (env-file write), `21-queued-work-discoverability`, `43-session-directory`.
- `54-load-gating.enabler/load-gating.md` + `13-enforcement-state.adr.md` (reworded) and
  `19-worktree-occupancy.enabler/worktree-occupancy.md` — retargeted to `spx hooks pre-tool-use`.
- `src/plugins/spec-tree/scripts/{session-start,load-gate,hook_runtime}.py` deleted;
  `src/plugins/spec-tree/hooks/hooks.json` repoints SessionStart and PreToolUse to
  `spx hooks <event>` (PreCompact/PostCompact/PostToolUse stay on Python until converted).
- `outcomeeng_testing/harnesses/hooks.py` — `run_session_start`/`run_pretool_gate`
  retargeted to invoke `spx hooks <event>` and return the JSON document.
- `spx/EXCLUDE` — the seven converted SessionStart/PreToolUse behavior nodes, until the
  spx release publishes.

## Remaining downstream work

1. **`@outcomeeng/spx` (separate repo):** implement `spx hooks session-start` and
   `spx hooks pre-tool-use` to the contract above, **publish to npm**, advance
   `REQUIRED_SPX_VERSION`, bump CI `SPX_VERSION`. Then remove the seven nodes from
   `spx/EXCLUDE`. While un-EXCLUDEing, broaden the now-runnable tests to full scenario
   coverage against the published contract: `test_worktree_occupancy.scenario.l1.py` to
   cover every declared scenario (claim recorded for the running worktree; stale/unclaimed
   reclaim before the gate; `CLAUDE_WORKTREE_CLAIMED=0` on a failed claim), beyond the
   three observable-boundary assertions it ships with; and
   `test_queued_work_discoverability.compliance.l1.py` `test_no_directive_outside_spec_tree`
   to verify the durable `spx/` tree, not `.spx/` session state, is what suppresses the
   directive outside a spec tree — confirming a seeded `.spx/sessions/todo` entry is left
   unread (distinguishing "not a spec tree" from "empty queue").
2. **Decompose then convert the deferred events:** isolate the PreCompact/PostCompact hook
   behavior in `76-sessions.enabler` and the PostToolUse hook behavior in `65-applying.enabler`
   into their own excludable child nodes, then convert them to `spx hooks pre-compact` /
   `post-compact` / `post-tool-use` (deleting `pre-compact.py`, `post-compact.py`,
   `enforce-gates.py`), rewording `21-compact-continuity.pdr.md` to the no-degrade model
   (the summary-fallback-when-the-stash-is-empty survives as `spx hooks post-compact`
   resilience, distinct from the removed spx-absent degrade).
