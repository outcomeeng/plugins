# Issues: Diagnostics Enabler

## Eval evidence authored; graded run pending CI

The node's three behavior assertions in `diagnostics.md` now carry authored `[eval]` evidence:

- `evals/session-environment-check/` (5 cases)
- `evals/spx-reachability-check/` (3 cases)
- `evals/diagnostic-report/` (5 cases)

Each suite loads cleanly through `outcomeeng_evals.definition.load_definition` and `outcomeeng_evals.case.load_cases`, and the `[eval]` links resolve, so the node is out of `spx/EXCLUDE` and `just check` link-integrity passes.

What remains is the **graded run** — replaying the cases through `claude --print` and scoring the verdicts (`outcomeeng-evals run`). It is not run on this changeset:

- No local run: the developer environment has no `ANTHROPIC_API_KEY` / OAuth token, so the runner cannot invoke `claude`.
- The PR-time `spec-tree-evals.yml` workflow is path-filtered to specific nodes and does not list the diagnostics surfaces, so it does not run these suites on a diagnose PR (and it is not a required check).
- The weekly `spec-tree-evals.yml` schedule discovers every non-manual `eval.toml` under the `spx` root and will run these suites — once the workflow forwards usable auth (`CLAUDE_CODE_OAUTH_TOKEN` today, `ANTHROPIC_API_KEY` for `--bare`, per `spx/13-infrastructure.enabler/25-eval-harness.enabler/ISSUES.md`).

Required to move the assertions from declared-and-evidenced to graded-green: confirm the first scheduled `spec-tree-evals` run grades these three suites at or above their `threshold` (0.8), or run them locally once auth is available. Adjust cases/prompts if the graded pass rate falls short.
