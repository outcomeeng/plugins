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

## 2. The five gate evals run in CI; the node is in `passing` state (RESOLVED)

All five eval suites — `review-readiness`, `merge-readiness`, `production-readiness`, `terminal-green`, `merge-command-overlay-precedence` — passed at 100% in CI run `26720175044` on commit `58b097c` (PR #95), every case clearing the `0.85` threshold (5/5, 6/6, 4/4, 5/5, 15/15 = 35/35 cases). The dominant prior failure mode — graded verdicts rejected as `verdict is not a parseable JSON document` because the model wrapped correct JSON in triple-backtick fences — is fixed by the grader change (`parse_verdict` retries after stripping one fence wrapper) and the runner change (a single `_FORMAT_SUFFIX` appended to every rendered prompt instructing raw-JSON output). Per `durable-map.md`'s node-state taxonomy the node is now `passing`: spec, evals, and implementation (the merging-related skills under `dist/claude/spec-tree`) exist and every assertion verifies. The node is removed from `spx/EXCLUDE`.

The `terminal-green` case-space remains complete: status-context `state == EXPECTED`, `PENDING`, `SUCCESS`, `ERROR`, `FAILURE` and every check-run conclusion the `terminal-green` definition in `spx/15-agent-pr-authority.pdr.md` names (15 cases).

The canonical `history.jsonl` baseline commits on the post-merge run on `main` — the workflow's `Commit history.jsonl appends` step is gated to `refs/heads/main` per `.github/workflows/spec-tree-evals.yml`, so PR runs collect run artifacts but do not commit them. The OAuth developer-session contamination caveat — workstation ambient instructions leaking into the verdict — is a developer-machine concern only; CI runs on a clean runner image, so the result above is the faithful validation surface even before `ANTHROPIC_API_KEY` joins the job env (tracked in the eval-harness `ISSUES.md`) and the workflow gains the `--bare` defense.

## 3. The local reviewing-changes no-findings render (RESOLVED)

**Resolved** in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`. The local `reviewing-changes` renderer now reports a uniform per-severity census: each empty severity bucket renders its `none-<severity>.md` marker (`BLOCKING: none` / `DEBT: none` / `FOLLOW-UP: none`), and the single blocking-only `no-blockers.md` was replaced by `none-blocking.md` / `none-debt.md` / `none-followup.md`. This separates the reviewer's mechanical census from the consumer's merge judgment, superseding the originally-prescribed single-line alignment of `no-blockers.md` to `"No BLOCKING or DEBT findings."` (the earlier framing of `no-blockers.md` as a "no findings" message was imprecise — it was the BLOCKING-section empty-state; the census model reports every severity uniformly). Format parity between the local render and the GH CI `spec-tree-review` workflow's clean-review message lives in `outcomeeng/gh-actions` and is a separate concern if pursued.

## 4. Heartbeat continuation-prompt payload shape is skill prose, not a spec assertion (FOLLOW-UP)

`/tracking-tasks` `<heartbeat_payload>` and `/standardizing-merging` `<heartbeat>` define the continuation prompt as exactly the skills to reload plus the pointers each skill handles, with the directive, finding assessments, and rationale reconstructed on wake-up from the durable artifacts. The constraint lives only as skill prose and a `/tracking-tasks` success-criterion; no `merging.md` assertion declares it and no eval verifies that a `/managing-pr` heartbeat prompt conforms to the two-item structure.

This is the deferred "declare in the spec" path: the change shipped as skill prose only by operator decision. To govern and verify the behavior when an eval-coverage sweep happens:

- Add a compliance assertion to `merging.md` declaring the heartbeat re-entry payload (skills + pointers, no reconstructable state), as the PR-flow instance of the `/tracking-tasks` rule.
- Create `evals/heartbeat-payload/` (`eval.toml`, `cases.jsonl`, `prompt.md`) exercising whether a `/managing-pr` heartbeat prompt carries only the skill re-entry and the PR-number pointer, with the directive, finding assessments, and rationale reconstructed rather than restated.
- Run the eval to populate `history.jsonl`.

Same shape as item 1: an enabler-side assertion + eval, not a `spx/15-agent-pr-authority.pdr.md` evidence-tag change.
In the outcomeeng/plugins repo, change the spec-tree PR skills so the default post-merge branch deletion is done manually (a separate, worktree-safe
delete) instead of inline gh pr merge --delete-branch.

Motivation. gh pr merge <pr> --rebase --delete-branch, run from the worktree that is on the branch being merged, makes gh move that worktree to the base
branch as part of deleting the local branch. In a multi-worktree checkout where the base (e.g. main) is checked out in another worktree, that switch fails
with fatal: 'main' is already used by worktree at … — the merge completes on GitHub but the branch is left undeleted and the flow ends in an error state.
The manual sequence below is worktree-safe and works identically in single- and multi-worktree setups.

New default merge + cleanup sequence (replaces the inline --delete-branch default):

# merge only — NO --delete-branch (it triggers gh's switch-to-base, which fails

# when the base is checked out in another worktree)

gh pr merge <pr-number> --rebase
git fetch origin <base>
git switch --detach "origin/<base>" # step THIS worktree off the merged branch onto the new base tip
git branch -D <branch> # delete the now-unoccupied local branch (tolerate "not found")

# delete the remote branch unless the repo already auto-deleted it

git ls-remote --exit-code --heads origin <branch> >/dev/null 2>&1 && git push origin --delete <branch>
git status --porcelain

Order matters: do not detach before gh pr merge — gh fails with "could not determine current branch" from a detached HEAD even with an explicit PR number.
Merge while the branch is still checked out, then detach, then delete.

Where to change it:

1. standardizing-merging (the shared reference both PR flows load — it owns the default). Update every place the inline --delete-branch default appears:
   the <authority_gates> "Merge command" default and its overlay-silent code block, the <repo_local_overlay> "Merge command" topic, and any
   <success_criteria> line naming the default. Flip the polarity: the worktree-safe manual deletion becomes the universal default; the overlay MAY opt into
   inline gh pr merge --rebase --delete-branch for projects that are always single-worktree.
2. managing-pr — Step 8 (the merge action) and <commands_reference> show gh pr merge --rebase --delete-branch; replace both with the sequence above.
3. opening-pr — opens PRs and doesn't merge or delete, so it likely needs no change; grep it for --delete-branch and only touch it if it actually carries
   merge/deletion guidance.

Also add a failure-mode note to standardizing-merging (or managing-pr) documenting the 'main' is already used by worktree failure and why the default
avoids it, so the rationale survives.

Process. Edit the SOURCE skills under plugins/spec-tree/skills/… (not the built dist/…), preserve the existing XML section structure and atemporal voice,
then rebuild dist/ and run the repo's validation (markdown + skill-structure) per its CLAUDE.md/AGENTS.md. Keep it one focused change.
