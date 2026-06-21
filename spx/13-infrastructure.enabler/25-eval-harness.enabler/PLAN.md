# Eval Harness: Plan — selective eval CI workflow (active; follow-ups remain)

`.github/workflows/spec-tree-evals.yml` is authored and lint-clean. It
plans each suite before running it: PRs use changed paths plus `owned_paths`
and `smoke_cases` from each `eval.toml`, while `push` to main, the weekly
schedule, and manual dispatch run the full non-manual suite set under the
configured root. Each selected suite runs through `outcomeeng-evals run`,
using the suite's declared `plugin_dir` or the workflow fallback, and the job
gates on each selected suite's exit code. On main the appended `history.jsonl`
rows are committed back via the `OUTCOMEENG_EVAL_STORE` PAT.

The root merge-gate policy probes moved out of LLM evals and into
deterministic mapping tests at
`spx/21-spec-tree.enabler/76-merging.enabler/tests/test_merge_gate_policy.mapping.l1.py`.
The CI eval workflow now covers the authored PR management,
PR opening, review-changes, and TypeScript test-ownership evals directly.

Remaining before this plan is resolved:

1. **Provision the commit-back secret** — see this node's `ISSUES.md`: confirm
   the org secret `OUTCOMEENG_EVAL_STORE` is visible to `outcomeeng/plugins`
   and bypasses branch protection once `main` is protected.

Deferred follow-ups tracked in `ISSUES.md`: a CLI `--model` pin, the CLI
`--bare` / `--no-bare` overrides, cross-suite parallelism, and the
`just eval-run` recipe naming.

## Prompt-caching implementation (pending — governed by `15-prompt-caching.adr.md`)

`spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md`
declares that eval execution holds one prompt prefix per run so the cache serves
it warm. Its `### Testing` rules (one shared prefix per run; warmth from the
server cache, not a resident process) are testable with a recording runner but
carry no path yet — the path-bearing `[test]` assertions and their tests land in
`eval-harness.md` (likely a co-located child node, EXCLUDE'd until green) when
`/apply` builds the execution below. The telemetry that makes a run's caching
observable already ships (the per-run cache read and creation token aggregates
in `cost_summary` and `history.jsonl`). The execution side that captures the
saving is not yet built:

1. **Converge on one shared prefix.** Today suites point `plugin_dir` at
   different runtimes (and a minimal-`plugin_dir` budget workaround diverges
   them further); each distinct prefix is one avoidable cold write. Decide and
   implement a single shared context for a run rather than a per-suite prefix.
2. **Pack invocations within the time-to-live.** The CI workflow runs suites in
   sequence per `outcomeeng-evals run` invocations; ensure a run's invocations
   stay inside one warm window so the shared prefix is not re-written on
   time-to-live expiry.
3. **Resolve the simulation-vs-in-situ fork.** Some suites simulate the skill in
   a self-contained `prompt.md` (no real plugin load needed); others load the
   shipped plugin. The shared-context decision differs for each — record which
   suites need the real plugin prefix and which can run against a minimal stub.
4. **Retire the prototype once the measurement migrates.** When the harness (or
   the SPX CLI) gains a cache-aggregate reporting path that reproduces the
   amortization measurement, remove `prototypes/eval-cache-amortization/` — its
   `FINDINGS.md` result is the durable record; `measure.py` is the throwaway
   measurement tool, kept only until the harness absorbs it, per the
   prove-then-migrate-or-remove lifecycle in `spx/12-shipped-scripting.adr.md`.

Empirical grounding for the lever lives in the exploratory prototype
`prototypes/eval-cache-amortization/` (`FINDINGS.md`): a warm prefix reads at a
fraction of a cold write over the same prefix, and the server cache holds
several prefixes at once within the time-to-live, so the cost driver is the
count of distinct prefixes plus time-to-live expiry, not which suite runs when.
Per `spx/12-shipped-scripting.adr.md` the prototype proves the lever; proven
logic moves into the harness or the SPX CLI, not the script (step 4 above).

## References

- **Workflow**: `.github/workflows/spec-tree-evals.yml`
- **Runner contract**: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md:18`
- **Gate-policy tests**: `spx/21-spec-tree.enabler/76-merging.enabler/tests/test_merge_gate_policy.mapping.l1.py`
- **PR-authority PDR**: `spx/15-merging.pdr.md`
- **Launch-in-CI + configurable-surface reference**: `outcomeeng/gh-actions` `spec-tree-review.yml`
