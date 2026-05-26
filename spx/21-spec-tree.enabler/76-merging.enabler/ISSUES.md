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

## 2. The five gate evals are authored but unrun (FOLLOW-UP)

The node's five `[eval]` directories — `review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence` — each carry `eval.toml`, `cases.jsonl`, and `prompt.md`, so every `merging.md` `[eval]` link resolves. None has been run: no `history.jsonl` exists, matching the node's prior state (the two pre-existing evals were also authored-but-unrun).

Required handling when an eval-run budget window opens:

- Run all five through the `outcomeeng-evals` CLI as a single deliberate, load-checked batch.
- Restore any unrelated `git diff` noise the local appends produce before committing.
- Confirm each suite meets its `threshold` (`0.85`); tune cases or prompts if a gate's classification proves non-deterministic under pass@k.
- Complete the `terminal-green` eval's state-space coverage: it exercises `SUCCESS`, `PENDING`, `FAILURE`, the check-run `COMPLETED` conclusions `SUCCESS`/`FAILURE`/`SKIPPED`/`NEUTRAL`, plus absent and `IN_PROGRESS`, but not the status-context `state == ERROR` branch nor the check-run `QUEUED` (non-terminal) and `CANCELLED`/`TIMED_OUT`/`ACTION_REQUIRED` (terminal-not-success) conclusions named in `spx/15-agent-pr-authority.pdr.md`. Add those cases and run them. (Deferred FOLLOW-UP from the PR #80 spec-tree review on head `d3cf4aa`.)

Deferred deliberately: replaying graded cases through `claude --print` spends API budget beyond this change's spec/skill/doc cascade deliverable.
