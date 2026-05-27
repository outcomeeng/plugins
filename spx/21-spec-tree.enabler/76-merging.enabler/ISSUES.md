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

The `terminal-green` case-space is now complete: the missing cases were added — status-context `state == ERROR` (terminal-not-success), check-run `QUEUED` (non-terminal), and check-run `CANCELLED`/`TIMED_OUT`/`ACTION_REQUIRED` (terminal-not-success) — so the suite now covers every branch the `terminal-green` definition in `spx/15-agent-pr-authority.pdr.md` names (14 cases).

A local run against an OAuth developer session is not a faithful validation surface. The `outcomeeng_evals` runner spawns `claude` as a subprocess, and before the isolation fix it inherited the workstation's ambient instruction stack — `~/.claude/CLAUDE.md` plus the auto-discovered repo `AGENTS.md` — which leaked formatting and closing-protocol behavior into the graded verdict (markdown-fenced JSON, `AskUserQuestion` calls) and inflated every call toward the per-case budget cap. The runner now passes `--bare` (see `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`), which isolates the eval to the plugin-loaded skill but resolves auth strictly from `ANTHROPIC_API_KEY` / `apiKeyHelper`, not OAuth.

Required handling — runs belong in CI, which supplies `ANTHROPIC_API_KEY` (the eval-harness node's own CI-integration item tracks wiring the workflow):

- Run all five through the `outcomeeng-evals` CLI under `--bare` auth.
- Confirm each suite meets its `threshold` (`0.85`); tune cases or prompts if a gate's classification proves non-deterministic under pass@k.
- CI owns the canonical `history.jsonl` appends; a developer-machine run's appends are local noise that stays out of the commit.
