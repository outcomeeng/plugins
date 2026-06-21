# Issues: Diagnostics Enabler

## Eval evidence authored; graded run pending CI

The node's six `[eval]` assertions in `diagnostics.md` now carry authored evidence:

- `evals/session-environment-check/` (6 cases)
- `evals/spx-reachability-check/` (6 cases)
- `evals/worktree-pool-check/` (6 cases)
- `evals/session-store-check/` (5 cases)
- `evals/marketplace-install-check/` (8 cases)
- `evals/diagnostic-report/` (5 cases)

Each suite loads cleanly through `outcomeeng_evals.definition.load_definition` and `outcomeeng_evals.case.load_cases`, and the `[eval]` links resolve, so the node is out of `spx/EXCLUDE` and `just check` link-integrity passes.

What remains is the **graded run** — replaying the cases through `claude --print` and scoring the verdicts (`outcomeeng-evals run`):

- The PR-time `spec-tree-evals.yml` workflow now lists the diagnostics surfaces in its `pull_request` and `push` path filters, so a diagnose PR triggers the eval workflow and grades the affected suites' `smoke_cases` under `CLAUDE_CODE_OAUTH_TOKEN` (subject to the `authorize` gate).
- The weekly `spec-tree-evals.yml` schedule discovers every non-manual `eval.toml` under the `spx` root and grades these suites in full under the same auth.
- `--bare` isolation arrives once the operator provisions `secrets.ANTHROPIC_API_KEY` per `spx/13-infrastructure.enabler/25-eval-harness.enabler/ISSUES.md`; the workflow already forwards it and degrades to OAuth while it is absent.
- No local run on this developer environment: it has no `ANTHROPIC_API_KEY` / OAuth token, so the runner cannot invoke `claude` here.

Required to move the assertions from declared-and-evidenced to graded-green: confirm the first PR-time or scheduled `spec-tree-evals` run grades these six suites at or above their `threshold` (0.8). Adjust cases/prompts if the graded pass rate falls short.
