# Issues: Diagnostics Enabler

## Eval evidence authored; graded green in CI

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

Confirmed graded-green: CI eval run `27902017867` (2026-06-21, on PR #294) graded all six diagnostics suites at or above their `0.8` threshold — session-environment, spx-reachability, worktree-pool, session-store, marketplace-install, and diagnostic-report (100% / 87.5% / 83.3% / 100% / 100% / 100%, with the sub-threshold misses being single-case LLM variance well above the floor). The weekly schedule and future diagnose PRs re-grade them; revisit cases/prompts only if a later run dips below `0.8`.

## Marketplace-install smoke case dips below threshold (PR #296)

On PR #296 (the diagnose-engine ADR, a spec-only change), the PR-time eval run graded the `marketplace-install-check` smoke subset at 66.67% (verdict FAIL, threshold `0.8`): the `installed-both-surfaces-current` case failed on two CI runs (head `18000906` and a rerun), while the other two smoke cases (`drifted-codex-surface-stale`, `unregistered-claude-surface`) passed. The same case passed on an earlier run (head `aa5cfce3`).

- **Not a regression.** The shipped skill is byte-identical across the passing and failing runs (`dist/` unchanged by the spec-only diff). The variance is in the model's classification output, scored by `claude --print`.
- **Smoke-subset sensitivity.** The PR-time run grades only the three `smoke_cases`, so one fragile case is a 33% swing under the `0.8` threshold. The full eight-case suite absorbs a single miss at 87.5% (the weekly schedule grades the full suite).
- **Disposition.** PR #296 merged over the red `evals` check by operator decision — `check` and `spec-tree-review` were green and `main` is unprotected; the failure is pre-existing eval-quality variance unrelated to the spec-only changeset.
- **Resolution options (separate from this node's spec):** widen the marketplace-install `smoke_cases`, raise `trials`/pass@k for that suite, or harden the `installed-both-surfaces-current` case prompt. All are superseded once `spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md` moves the classification into `spx diagnose` with deterministic `[test]` evidence — the LLM-classification non-determinism this case exhibits is exactly what that ADR removes.
