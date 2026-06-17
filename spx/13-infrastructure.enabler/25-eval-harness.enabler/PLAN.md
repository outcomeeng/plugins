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

## References

- **Workflow**: `.github/workflows/spec-tree-evals.yml`
- **Runner contract**: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md:16`
- **Gate-policy tests**: `spx/21-spec-tree.enabler/76-merging.enabler/tests/test_merge_gate_policy.mapping.l1.py`
- **PR-authority PDR**: `spx/15-merging.pdr.md`
- **Launch-in-CI + configurable-surface reference**: `outcomeeng/gh-actions` `spec-tree-review.yml`
