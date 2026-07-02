# Issues: PR Managing Protocol

## 1. Worktree-safe branch-deletion default lacks eval coverage for the deletion mechanism (FOLLOW-UP)

The `managing-pr.md` merge-command scenario declares two observable branch-deletion behaviors: the overlay-silent default runs the worktree-safe deletion sequence (`gh pr merge --rebase --delete-branch=false`, then detach this worktree onto the refreshed base tip and delete the local and remote branches separately), and an overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for always-single-worktree projects. The `merge-command-overlay-precedence` eval verifies only the merge-strategy flag and its source; no case exercises the deletion mechanism.

Required handling when an eval-coverage sweep happens:

- Add a scenario assertion to `managing-pr.md` (or extend the merge-command scenario) declaring the deletion-mechanism choice as a separately observable behavior.
- Create `evals/merge-cleanup-deletion/` with a verdict schema carrying a deletion-mechanism field, exercising the overlay-silent worktree-safe path and the single-worktree inline opt-in.
- Run the eval to populate `history.jsonl`.

Surfaced by the local `changes-reviewer` gate on `fix/worktree-safe-branch-deletion` (2026-06-07).

## 2. Merge-readiness review-check eval cases need execution evidence (FOLLOW-UP)

The `merge-readiness` eval carries updated cases for the current-head
review-kind check mapping, but the eval run is not recorded for this change
because the operator instructed the session not to run evals.

Unverified cases:

- `self-modifying-review-skip-mentions-review`
- `non-design-review-skip-blocks`
- `review-check-terminal-failure-blocks`
- `host-mergeable-review-check-in-progress-waits`
- `old-inline-comments-do-not-satisfy-current-review`

Required handling:

- Run `just eval spx/21-spec-tree.enabler/76-merging.enabler/32-github-pr.enabler/54-managing-pr.enabler/evals/merge-readiness/eval.toml`.
- Commit the resulting `history.jsonl` entry when the eval passes.
- Remove this issue once the eval history records the updated case set passing.

Surfaced by CI review on PR #398 (2026-07-01).
