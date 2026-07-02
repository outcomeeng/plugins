# Eval Harness: Plan — prompt-caching implementation (gated)

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

The `OUTCOMEENG_EVAL_STORE` org secret is visible to `outcomeeng/plugins`, and
the token account can bypass `main` branch protection for commit-back pushes.

Deferred follow-ups tracked in `ISSUES.md` include optional per-eval model
pinning and cross-suite parallelism.

## Prompt-caching implementation (decided; gated on CLI regression #34629)

The prompt-caching decision is reconciled.
`spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md`
keeps prefix reuse as the cost lever and records the corrected mechanism:
**capture the amortization on the subscription `claude --print` path via a base
session loaded with every plugin once and forked per case**, so each case reads
the shared prefix warm and writes only its case-specific suffix, keeping the
`NEVER`-route-to-a-metered-API stance. The supporting investigation is recorded
in `prototypes/eval-cache-amortization/investigation.md` (outside `spx/`;
conclusion corrected from the earlier single-turn-only reading); the empirical
fixed-prefix payoff is `prototypes/eval-cache-amortization/FINDINGS.md` (5.45× per
call, ~73–80% per suite).

Realization is gated on an upstream CLI regression: since v2.1.69
(`anthropics/claude-code#34629`; installed CLI 2.1.185 is affected),
`claude --print --resume`/`--fork-session` stops reusing the cached conversation
history, so a forked case cold-writes the prefix exactly as the current
single-turn shape does. The harness keeps its current single-turn invocation
until the regression clears. The telemetry that makes a run's caching observable
already ships (the per-run cache read and creation token aggregates in
`cost_summary` and `history.jsonl`).

When the regression clears — upstream fix, a pinned pre-regression CLI (v2.1.68),
or the published community cache fix — implement and validate:

1. **Validate fork-per-case empirically.** Extend
   `prototypes/eval-cache-amortization/measure.py` to load a base session with the
   plugin, fork it per case with *differing* questions, and confirm each fork reads
   the plugin prefix warm (read ≈ full prefix, write ≈ question only). This is the
   one claim the existing measurements do not yet cover directly — Result 1 used an
   identical prompt; real cases vary the question.
2. **Build the base-session-fork-per-case runner.** Load every plugin once into a
   base session, then fork it per case so each case reads the shared prefix warm
   and writes only its suffix; keep cases independent (fork the same clean base,
   never accumulate). The path-bearing `[test]` assertions (one shared warm prefix;
   warmth from the server cache, not a resident process) land in `eval-harness.md`
   (likely a co-located child node, EXCLUDE'd until green) when `/apply` builds it.
3. **Pack invocations within the time-to-live** so the shared prefix is not evicted
   and re-written mid-run.
4. **Retire the prototype once the measurement migrates.** When the harness (or the
   SPX CLI) reproduces the amortization measurement, remove
   `prototypes/eval-cache-amortization/` — its `FINDINGS.md`/`investigation.md` are
   the durable record; `measure.py` is the throwaway measurement tool, kept only
   until the harness absorbs it, per the prove-then-migrate-or-remove lifecycle in
   `spx/12-shipped-scripting.adr.md`.

## References

- **Workflow**: `.github/workflows/spec-tree-evals.yml`
- **Runner contract**: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md:18`
- **Gate-policy tests**: `spx/21-spec-tree.enabler/76-merging.enabler/tests/test_merge_gate_policy.mapping.l1.py`
- **PR-authority PDR**: `spx/15-merging.pdr.md`
- **Launch-in-CI + configurable-surface reference**: `outcomeeng/gh-actions` `spec-tree-review.yml`
- **Prompt-caching decision**: `spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md`
- **Cache investigation + measurement**: `prototypes/eval-cache-amortization/investigation.md`, `prototypes/eval-cache-amortization/FINDINGS.md`
- **CLI cache regression**: `anthropics/claude-code#34629`
