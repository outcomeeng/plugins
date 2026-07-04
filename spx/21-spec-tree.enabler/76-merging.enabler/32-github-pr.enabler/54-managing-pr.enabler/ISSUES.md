# Issues: PR Managing Protocol

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario (FOLLOW-UP)

The reviewer-skipped-by-design exception — `/merging-standards` `<authority_gates>`, `/manage-pr` Step 8, the `MENTION_REVIEW_NEEDED` action token — has a `managing-pr.md` compliance assertion declaring the mention-trigger but no scenario exercising the skip path and no dedicated eval.

A scenario for the skip path would fit the node's eval pattern:

> Given the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file and no current-head review exists, when the managing flow evaluates `MERGE_READINESS`, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `managing-pr.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

## 2. Worktree-safe branch-deletion default lacks eval coverage for the deletion mechanism (FOLLOW-UP)

The `managing-pr.md` merge-command scenario declares two observable branch-deletion behaviors: the overlay-silent default runs the worktree-safe deletion sequence (`gh pr merge --rebase --delete-branch=false`, then detach this worktree onto the refreshed base tip and delete the local and remote branches separately), and an overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for always-single-worktree projects. The `merge-command-overlay-precedence` eval verifies only the merge-strategy flag and its source; no case exercises the deletion mechanism.

Required handling when an eval-coverage sweep happens:

- Add a scenario assertion to `managing-pr.md` (or extend the merge-command scenario) declaring the deletion-mechanism choice as a separately observable behavior.
- Create `evals/merge-cleanup-deletion/` with a verdict schema carrying a deletion-mechanism field, exercising the overlay-silent worktree-safe path and the single-worktree inline opt-in.
- Run the eval to populate `history.jsonl`.

Surfaced by the local `changes-reviewer` gate on `fix/worktree-safe-branch-deletion` (2026-06-07).

## 3. Review-thread GraphQL mutation needs a narrower command surface (FOLLOW-UP)

The `/manage-pr` skill's scoped `allowed-tools` list grants `Bash(gh api graphql:*)` so Step 8 can resolve review threads through the `resolveReviewThread` mutation. The prefix-matching allowed-tools syntax cannot restrict by GraphQL operation body, so the entry grants every GraphQL query and mutation the token can perform.

Required handling:

- Add a thin shipped script or another narrow invocation surface for the `resolveReviewThread` mutation.
- Replace `Bash(gh api graphql:*)` in `src/plugins/spec-tree/skills/manage-pr/SKILL.md` with the narrow wrapper command.
- Regenerate `dist/claude` and `dist/codex`.

Tracked because the bounded fix needs a wrapper design and portability review rather than another wildcard edit in the PR-management re-entry changeset.
