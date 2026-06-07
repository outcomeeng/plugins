# Issues: PR Workflow Enabler

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario (FOLLOW-UP)

The reviewer-skipped-by-design exception — `/standardizing-merging` `<authority_gates>`, `/managing-pr` Step 8, the `MENTION_REVIEW_NEEDED` action token — has no `merging.md` scenario assertion exercising the skip path and no dedicated eval.

The node's gate scenarios (`review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence`) each carry an `[eval]` link. A scenario for the skip path would fit that pattern:

> Given the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file and no current-head review exists, when the managing flow evaluates `MERGE_READINESS`, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `merging.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

Not a retag of the `spx/15-agent-pr-authority.pdr.md` MUST rules: those are "the skill declares X" structural assertions, `[review]` per `spx/15-spec-coverage.adr.md`. The follow-up is the enabler-side scenario + eval, not a PDR evidence-tag change.

## 4. Heartbeat continuation-prompt payload shape is skill prose, not a spec assertion (FOLLOW-UP)

`/tracking-tasks` `<heartbeat_payload>` and `/standardizing-merging` `<heartbeat>` define the continuation prompt as exactly the skills to reload plus the pointers each skill handles, with the directive, finding assessments, and rationale reconstructed on wake-up from the durable artifacts. The constraint lives only as skill prose and a `/tracking-tasks` success-criterion; no `merging.md` assertion declares it and no eval verifies that a `/managing-pr` heartbeat prompt conforms to the two-item structure.

This is the deferred "declare in the spec" path: the change shipped as skill prose only by operator decision. To govern and verify the behavior when an eval-coverage sweep happens:

- Add a compliance assertion to `merging.md` declaring the heartbeat re-entry payload (skills + pointers, no reconstructable state), as the PR-flow instance of the `/tracking-tasks` rule.
- Create `evals/heartbeat-payload/` (`eval.toml`, `cases.jsonl`, `prompt.md`) exercising whether a `/managing-pr` heartbeat prompt carries only the skill re-entry and the PR-number pointer, with the directive, finding assessments, and rationale reconstructed rather than restated.
- Run the eval to populate `history.jsonl`.

Same shape as item 1: an enabler-side assertion + eval, not a `spx/15-agent-pr-authority.pdr.md` evidence-tag change.

## 5. Worktree-safe branch-deletion default lacks eval coverage for the deletion mechanism (FOLLOW-UP)

The `merging.md` merge-command scenario declares two observable branch-deletion behaviors: the overlay-silent default runs the worktree-safe deletion sequence (`gh pr merge --rebase` without `--delete-branch`, then detach this worktree onto the refreshed base tip and delete the local and remote branches separately), and an overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for always-single-worktree projects. The `merge-command-overlay-precedence` eval verifies only the merge-strategy flag and its source (`merge_flag` ∈ {`--rebase`, `--merge`, `--squash`}, `source` ∈ {`overlay`, `universal-default`}); no case exercises whether the agent runs the worktree-safe deletion sequence versus inline `--delete-branch`.

Same shape as items 1 and 4: a behavior declared in the spec and shipped as skill prose, awaiting eval coverage in an eval-coverage sweep. The merge-flag concern and the deletion-mechanism concern are distinct, so the coverage belongs in its own eval rather than overloading `merge-command-overlay-precedence`.

Required handling when an eval-coverage sweep happens:

- Add a scenario assertion to `merging.md` (or extend the existing merge-command scenario) declaring the deletion-mechanism choice as a separately observable behavior.
- Create `evals/merge-cleanup-deletion/` (`eval.toml`, `cases.jsonl`, `prompt.md`) with a verdict schema carrying a deletion-mechanism field, exercising the overlay-silent worktree-safe path and the single-worktree inline opt-in.
- Run the eval to populate `history.jsonl`.

Surfaced by the local `reviewing-changes` gate on `fix/worktree-safe-branch-deletion` (2026-06-07).
