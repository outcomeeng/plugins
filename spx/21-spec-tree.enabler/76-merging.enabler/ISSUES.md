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

## 2. The five gate evals are authored but unrun — runs deferred to CI (FOLLOW-UP)

The node's five `[eval]` directories — `review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence` — each carry `eval.toml`, `cases.jsonl`, and `prompt.md`, so every `merging.md` `[eval]` link resolves. None has a committed `history.jsonl`: the suites have not been validated against their `0.85` thresholds.

The `terminal-green` case-space is complete: status-context `state == EXPECTED`, `PENDING`, `SUCCESS`, `ERROR`, `FAILURE` and every check-run conclusion the `terminal-green` definition in `spx/15-agent-pr-authority.pdr.md` names (15 cases).

A local run against an OAuth developer session is not a faithful validation surface: the workstation's ambient instruction stack — `~/.claude/CLAUDE.md` plus an auto-discovered repo `AGENTS.md` — leaks formatting and closing-protocol behavior into the graded verdict (markdown-fenced JSON, `AskUserQuestion` calls) and inflates every call toward the per-case budget cap. CI is the canonical execution surface because its execution surface has no auto-discoverable instruction files; the `outcomeeng_evals` runner invokes `claude` without `--bare` by default (see `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`) and accepts the `CLAUDE_CODE_OAUTH_TOKEN` job secret that the existing `spec-tree` and `spec-tree-review` workflows already use.

Required handling — runs belong in CI (the eval-harness node's own CI-integration item tracks wiring the workflow):

- Run all five through the `outcomeeng-evals` CLI in the canonical CI execution surface (default invocation, no `--bare`, auth via `CLAUDE_CODE_OAUTH_TOKEN`).
- Confirm each suite meets its `threshold` (`0.85`); tune cases or prompts if a gate's classification proves non-deterministic under pass@k.
- CI owns the canonical `history.jsonl` appends; a developer-machine run's appends are local noise that stays out of the commit.
