# Issues: PR Managing Protocol

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario

The reviewer-skipped-by-design exception — `/merging-standards` `<authority_gates>`, `/manage-pr` Step 8, the `MENTION_REVIEW_NEEDED` action token — has a `managing-pr.md` compliance assertion declaring the mention-trigger but no scenario exercising the skip path and no dedicated eval.

A scenario for the skip path would fit the node's eval pattern:

> Given the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file and no current-head review exists, when the managing flow evaluates `MERGE_READINESS`, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `managing-pr.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

## 2. Worktree-safe branch-deletion default lacks eval coverage for the deletion mechanism

The `managing-pr.md` merge-command scenario declares two observable branch-deletion behaviors: the overlay-silent default runs the worktree-safe deletion sequence (`gh pr merge --merge --delete-branch=false`, then detach this worktree onto the refreshed base tip and delete the local and remote branches separately), and an overlay MAY opt into inline `gh pr merge --merge --delete-branch` for always-single-worktree projects. The retired `merge-command-overlay-precedence` eval verified only the merge-strategy flag and its source; no case exercised the deletion mechanism.

Required handling when an eval-coverage sweep happens:

- Add a scenario assertion to `managing-pr.md` (or extend the merge-command scenario) declaring the deletion-mechanism choice as a separately observable behavior.
- Create `evals/merge-cleanup-deletion/` with a verdict schema carrying a deletion-mechanism field, exercising the overlay-silent worktree-safe path and the single-worktree inline opt-in.
- Run the eval to populate `history.jsonl`.

Surfaced by the local `changes-reviewer` gate on `fix/worktree-safe-branch-deletion` (2026-06-07).

## 3. Retired merge-management evals need producer-backed replacements

The retired eval suites under `evals/merge-readiness/`,
`evals/merge-command-overlay-precedence/`, `evals/pr-check-wait/`, and
`evals/review-inspection-comments/` modeled `/manage-pr` behavior by prompting a
model to classify supplied JSON plans or state. They did not run the producing
`/manage-pr` skill, did not exercise the live PR inspection commands, and did
not prove the producer behavior declared by the node's assertions. The affected
assertions now use `[audit]` evidence until replacement evals can drive the real
producer surface and score parseable outputs.

Revisit condition:

- Add producer-backed evals for `MERGE_READINESS`, reviewer-skipped handling,
  merge-command selection, review-surface inspection, and foreground PR-check
  wait/re-entry behavior.
- Keep the eval prompts focused on the real producer artifact rather than a
  copied policy simulation.
- Run the canonical eval commands and commit each `history.jsonl`.

## 4. Review-thread resolver extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/manage-pr/scripts/resolve_review_thread.py` runs to 313 lines — resolution of one GitHub pull-request review thread. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; the resolver has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository.

**Resolution shape**: port thread resolution into the SPX CLI, publish it, advance the floor, and reduce the shipped skill to its instruction with no script. Thread resolution mutates pull-request state, so the ported surface keeps that mutation behind the same explicit-instruction boundary the product-level compliance rule requires and the `inspect-github-actions` mutation gate enforces today, tracked in `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/ISSUES.md`. Revisit when the capability publishes.
