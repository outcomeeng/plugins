# Eval Harness: Plan — eval CI workflow (authored; validation pending)

`.github/workflows/spec-tree-evals.yml` is authored and lint-clean. It
discovers each `eval.toml` under the configured root and runs it through
`outcomeeng-evals run` with `--plugin-dir dist/claude/spec-tree`, gating the
job on each suite's exit code (threshold `0.85`). Triggers: every
`pull_request` touching the spec-tree plugin / its evals / the harness
(collaborator-authorized so untrusted PRs never get the OAuth secret), `push`
to main, a weekly `schedule`, and `workflow_dispatch`. On main the appended
`history.jsonl` rows are committed back via the `OUTCOMEENG_EVAL_STORE` PAT.

Remaining before this plan is resolved:

1. **First-run validation** — dispatch the workflow once (`workflow_dispatch`)
   and confirm all five merging suites exit 0 and meet their `0.85` threshold.
   Tune cases/prompts in the owning `evals/<rule>/` directory if a gate is
   non-deterministic under pass@k.
2. **Provision the commit-back secret** — see this node's `ISSUES.md`: confirm
   the org secret `OUTCOMEENG_EVAL_STORE` is visible to `outcomeeng/plugins`
   and bypasses branch protection once `main` is protected.

Deferred follow-ups (tracked in `ISSUES.md`, out of scope for the first cut):
the 4 reviewing-changes evals and the 1 typescript eval (per-eval plugin-dir
mapping the `eval.toml` does not yet declare), a CLI `--model` pin, the CLI
`--bare` / `--no-bare` CLI overrides (the env-derive default makes the common case automatic; the CLI overrides are deferred until either case surfaces), and the `just eval-run` recipe naming.

## References

- **Workflow**: `.github/workflows/spec-tree-evals.yml`
- **Runner contract**: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md:16`
- **Gate-eval node**: `spx/21-spec-tree.enabler/76-merging.enabler/merging.md` and its `ISSUES.md` item 2
- **PR-authority PDR**: `spx/15-agent-pr-authority.pdr.md`
- **Launch-in-CI + configurable-surface reference**: `outcomeeng/gh-actions` `spec-tree-review.yml`
