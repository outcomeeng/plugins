# PR Managing Protocol

PROVIDES the open pull-request management protocol — three-surface review and check inspection, two-severity finding triage, follow-up pushes, `MERGE_READINESS` evaluation, and the worktree-safe merge with branch cleanup
SO THAT the GitHub-PR transport's `/github-pr` orchestration
CAN drive an open pull request to an autonomous merge once `MERGE_READINESS` and `PRODUCTION_READINESS` hold, per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given a clean current-head CI review exists — matching the reviewing shape, complete and valid, reporting no unresolved `BLOCKING` or `DEBT` finding (stated directly, or with every such finding individually dropped as unbacked; a `DEBT` finding the author tracks out of scope with a recorded reason not unresolved, its absence never satisfying the predicate) — every other required check is terminal-green, and branch hygiene and PR state hold (`OPEN`, not draft, head SHA matches origin, rebased onto base), when `/managing-pr` evaluates `MERGE_READINESS` and `PRODUCTION_READINESS` holds, then it merges autonomously without separate human instruction ([eval](evals/merge-readiness/eval.toml))
- Given GitHub reports a PR as mergeable or would accept `gh pr merge`, but the freshly re-read current-head reviewing-kind check or another required check is absent, pending, failed, stale, or head-mismatched, when `/managing-pr` reaches the merge mutation point, then the pre-merge guard emits the appropriate wait/block token and no merge command is legal unless the guard first produces `MERGE_READY:<head-sha>` for the inspected head ([eval](evals/merge-readiness/eval.toml))
- Given `MERGE_READINESS` and `PRODUCTION_READINESS` are satisfied, when `/managing-pr` selects the merge command, then it follows the overlay's declared merge command if any; when the overlay is silent, it runs rebase merge followed by a worktree-safe manual branch deletion (`gh pr merge --rebase --delete-branch=false`, then detaching this worktree onto the refreshed base tip and deleting the local and remote branches separately) as the universal default ([eval](evals/merge-command-overlay-precedence/eval.toml))
- Given a PR inspection pass, when `/managing-pr` gathers review state, then every `gh pr view` field list that inspects PR-level issue comments includes `comments`, and the pass separately inspects review-thread comments via the pull-request comments API ([eval](evals/review-inspection-comments/eval.toml))
- Given a PR has a non-terminal required check, a non-terminal reviewing-kind check, or missing current-head CI review output while another current-head check is non-terminal, when `/managing-pr` waits for GitHub PR check completion, then it runs exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30` as the foreground wait command and, after the command exits, performs a full merge-gate inspection across PR state, check rollup, PR-level comments, formal reviews, and review-thread comments before deciding the next action ([eval](evals/pr-check-wait/eval.toml))

### Compliance

- ALWAYS: when the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file, `/managing-pr` fires the mention-triggered reviewer with the project's configured trigger phrase (default `@spec-tree`) and treats its posted findings as the current-head review, per `spx/15-merging.pdr.md` ([review])
- ALWAYS: `/managing-pr` presents payload-bearing `gh pr comment` and `gh pr review` commands by supported harness environment — quoted heredoc for interactive Claude Code and Codex sessions, and one physical `printf '%s\n' ... | gh pr ... --body-file -` line for programmatic runners that require single-line commands — per `spx/15-agent-tools.pdr.md` ([audit])
