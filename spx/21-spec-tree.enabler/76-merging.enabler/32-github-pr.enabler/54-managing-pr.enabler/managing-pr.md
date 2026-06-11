# PR Managing Protocol

PROVIDES the open pull-request management protocol — three-surface review and check inspection, two-severity finding triage, follow-up pushes, `MERGE_READINESS` evaluation, and the worktree-safe merge with branch cleanup
SO THAT the GitHub-PR transport's `/pr` orchestration
CAN drive an open pull request to an autonomous merge once `MERGE_READINESS` and `PRODUCTION_READINESS` hold, per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given a clean current-head CI review exists — matching the reviewing shape, complete and valid, reporting no unresolved `BLOCKING` or `DEBT` finding (stated directly, or with every such finding individually dropped as unbacked; a `DEBT` finding the author tracks out of scope with a recorded reason not unresolved, its absence never satisfying the predicate) — every other required check is terminal-green, and branch hygiene and PR state hold (`OPEN`, not draft, head SHA matches origin, rebased onto base), when `/managing-pr` evaluates `MERGE_READINESS` and `PRODUCTION_READINESS` holds, then it merges autonomously without separate human instruction ([eval](evals/merge-readiness/eval.toml))
- Given `MERGE_READINESS` and `PRODUCTION_READINESS` are satisfied, when `/managing-pr` selects the merge command, then it follows the overlay's declared merge command if any; when the overlay is silent, it runs rebase merge followed by a worktree-safe manual branch deletion (`gh pr merge --rebase --delete-branch=false`, then detaching this worktree onto the refreshed base tip and deleting the local and remote branches separately) as the universal default ([eval](evals/merge-command-overlay-precedence/eval.toml))
- Given a PR inspection pass, when `/managing-pr` gathers review state, then every `gh pr view` field list that inspects PR-level issue comments includes `comments`, and the pass separately inspects review-thread comments via the pull-request comments API ([eval](evals/review-inspection-comments/eval.toml))

### Compliance

- ALWAYS: when the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file, `/managing-pr` fires the mention-triggered reviewer with the project's configured trigger phrase (default `@spec-tree`) and treats its posted findings as the current-head review, per `spx/15-merging.pdr.md` ([review])
