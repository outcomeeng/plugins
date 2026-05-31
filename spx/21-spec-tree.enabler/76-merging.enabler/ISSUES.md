# Issues: PR Workflow Enabler

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario (FOLLOW-UP)

The reviewer-skipped-by-design exception — `/standardizing-merging` `<authority_gates>`, `/managing-pr` Step 8, the `MENTION_REVIEW_NEEDED` action token — has no `merging.md` scenario assertion exercising the skip path and no dedicated eval.

The node's gate scenarios (`review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence`) each carry an `[eval]` link. A scenario for the skip path would fit that pattern:

> Given the CI `spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main" and no current-head review exists, when the managing flow evaluates `MERGE_READINESS`, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `merging.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

Not a retag of the `spx/15-agent-pr-authority.pdr.md` MUST rules: those are "the skill declares X" structural assertions, `[review]` per `spx/15-spec-coverage.adr.md`. The follow-up is the enabler-side scenario + eval, not a PDR evidence-tag change.

## 2. The five gate evals run in CI; the node is in `failing` state (FOLLOW-UP)

The node's five `[eval]` directories — `review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence` — each carry `eval.toml`, `cases.jsonl`, and `prompt.md`, so every `merging.md` `[eval]` link resolves. The CI workflow now runs all five (first end-to-end execution on PR #95 head `ffb37b7`, run `26712350116`); every suite is below the `0.85` threshold — `review-readiness` at 20% (1/5), `terminal-green` at 13% (2/15), and similar across the rest. Most failing cases report `verdict is not a parseable JSON document` — claude returns prose or partial structure instead of the structured verdict the grader expects. A small number of cases do pass (e.g. `deterministic-failed-withholds`, `check-run-completed-success`), so the prompt is reachable but unreliable across the case set. Per `durable-map.md`'s node-state taxonomy, this is the `failing` state: spec, tests, and implementation (the eval prompts + grader contract) exist; the implementation is in violation of the spec assertions. The node is recorded in `spx/EXCLUDE` so `spx test passing` already skips it.

The `terminal-green` case-space is complete: status-context `state == EXPECTED`, `PENDING`, `SUCCESS`, `ERROR`, `FAILURE` and every check-run conclusion the `terminal-green` definition in `spx/15-agent-pr-authority.pdr.md` names (15 cases).

A local run against an OAuth developer session is not a faithful validation surface: the workstation's ambient instruction stack — `~/.claude/CLAUDE.md` plus an auto-discovered repo `AGENTS.md` — leaks formatting and closing-protocol behavior into the graded verdict (markdown-fenced JSON, `AskUserQuestion` calls) and inflates every call toward the per-case budget cap. The `outcomeeng_evals` runner derives `--bare` from the inherited environment (see `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`): a developer with `ANTHROPIC_API_KEY` exported runs isolated, while a developer under `CLAUDE_CODE_OAUTH_TOKEN` or an OAuth login session runs without `--bare` and accepts the contamination. CI is the canonical execution surface either way: it lives on a runner image with no auto-discoverable instruction files and (once `ANTHROPIC_API_KEY` is added to its job env — tracked in the eval-harness `ISSUES.md`) runs with `--bare` for the full isolation defense.

Required handling — runs belong in CI, now wired as `.github/workflows/spec-tree-evals.yml` (every PR touching the plugin / evals / harness, plus push-to-main, schedule, and dispatch). This item stays open until the suites run green in CI and the canonical `history.jsonl` baseline is committed:

- Run all five through the `outcomeeng-evals` CLI in the canonical CI execution surface (the runner's env-derived default takes `--bare` when `ANTHROPIC_API_KEY` is forwarded to the job env per the eval-harness `ISSUES.md` follow-up; until that lands, the workflow runs without `--bare` under `CLAUDE_CODE_OAUTH_TOKEN`).
- Confirm each suite meets its `threshold` (`0.85`); tune cases or prompts if a gate's classification proves non-deterministic under pass@k.
- CI owns the canonical `history.jsonl` appends; a developer-machine run's appends are local noise that stays out of the commit.
