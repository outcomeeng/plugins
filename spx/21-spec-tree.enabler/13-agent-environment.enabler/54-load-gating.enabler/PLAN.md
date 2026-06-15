# PLAN: Load-gating mechanism

## State

The marketplace half is specced and (in this PR) implemented; the `spx` CLI half — which owns the transcript scan and the verdict — lands in a separate repository. The enforce-on-tracked-state design lives in `13-enforcement-state.adr.md`; the hook-delegation contract lives in `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` (amended to admit the `PreToolUse` gate).

## Marketplace half (this repo)

- `load-gating.md` declares the two gates, the boundary linchpin, the CLI-delegation contract, and the degrade-when-CLI-absent behavior; the node ships with its `[test]` assertions passing and is not in `spx/EXCLUDE` — only the CLI half below remains.
- A thin `PreToolUse` gate hook (`src/plugins/spec-tree/scripts/`) forwards `{tool name, tool path, session id, transcript path}` to the `spx` CLI, emits the CLI's allow-or-deny verdict, no-ops outside a spec-tree repo (no `spx/*.product.md`), and degrades to allowing the call when the CLI is absent, exits non-zero, or times out.
- `src/plugins/spec-tree/hooks/hooks.json` registers the hook under `PreToolUse`.
- The `SessionStart` understanding directive (`21-understanding-directive.enabler`) is reframed to point at the mechanical gate (informational only); the base-staleness directive is unchanged.
- Covered by `tests/test_load_gating.scenario.l1.py` against the hooks harness (`outcomeeng_testing/harnesses/hooks.py`), with a fake `spx` returning crafted verdicts and an absent-CLI path.

## `spx` CLI half (`~/Code/outcomeeng/spx/`) — remaining

A `spx` subcommand (e.g. `spx gate`) that receives the forwarded locators and returns the verdict:

- **Boundary linchpin.** Parse the transcript JSONL, find the most recent session-start / compaction boundary, and scan only the region after it. A `<SPEC_TREE_FOUNDATION>` or `<SPEC_TREE_CONTEXT>` marker preserved only in a pre-compaction summary must not satisfy a gate.
- **Gate A (foundation).** Deny the first tool call after the boundary while no `<SPEC_TREE_FOUNDATION>` marker exists in the segment. Allowlist the `/spec-tree:understanding` invocation that emits the marker; let purely-external tools (web) pass.
- **Gate B (context).** Deny `Edit`/`Write`/mutating `Bash` whose path resolves under a spec-tree node while no `<SPEC_TREE_CONTEXT target="<node>">` for the owning node exists in the segment. The owning node is the nearest ancestor directory of the path that is an `*.enabler` or `*.outcome`.
- **Verdict shape.** Return a structured allow-or-deny with the denial message the hook surfaces (`PreToolUse` decision).
- **Engagement.** Only act in a spec-tree repository (`spx/*.product.md` present); otherwise allow.

The CLI owns all transcript I/O and `.spx/` resolution per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`; the marketplace hook reaches it only as a subprocess and degrades silently until the subcommand ships. The denial wording proposals in the originating task are product-agnostic; the CLI parameterizes by product and never hard-codes `spx`.
