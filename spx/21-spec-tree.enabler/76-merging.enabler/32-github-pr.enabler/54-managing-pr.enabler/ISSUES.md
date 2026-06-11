# Issues: PR Managing Protocol

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario (FOLLOW-UP)

The reviewer-skipped-by-design exception — `/standardizing-merging` `<authority_gates>`, `/managing-pr` Step 8, the `MENTION_REVIEW_NEEDED` action token — has a `managing-pr.md` compliance assertion declaring the mention-trigger but no scenario exercising the skip path and no dedicated eval.

A scenario for the skip path would fit the node's eval pattern:

> Given the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file and no current-head review exists, when the managing flow evaluates `MERGE_READINESS`, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `managing-pr.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

## 2. Heartbeat continuation-prompt payload shape is skill prose, not a spec assertion (FOLLOW-UP)

`/tracking-tasks` `<heartbeat_payload>` and `/standardizing-merging` `<heartbeat>` define the continuation prompt as exactly the skills to reload plus the pointers each skill handles, with the directive, finding assessments, and rationale reconstructed on wake-up from the durable artifacts. The constraint lives only as skill prose and a `/tracking-tasks` success-criterion; no `managing-pr.md` assertion declares it and no eval verifies that a `/managing-pr` heartbeat prompt conforms to the two-item structure.

To govern and verify the behavior when an eval-coverage sweep happens:

- Add a compliance assertion to `managing-pr.md` declaring the heartbeat re-entry payload (skills + pointers, no reconstructable state).
- Create `evals/heartbeat-payload/` (`eval.toml`, `cases.jsonl`, `prompt.md`).
- Run the eval to populate `history.jsonl`.

## 3. Worktree-safe branch-deletion default lacks eval coverage for the deletion mechanism (FOLLOW-UP)

The `managing-pr.md` merge-command scenario declares two observable branch-deletion behaviors: the overlay-silent default runs the worktree-safe deletion sequence (`gh pr merge --rebase --delete-branch=false`, then detach this worktree onto the refreshed base tip and delete the local and remote branches separately), and an overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for always-single-worktree projects. The `merge-command-overlay-precedence` eval verifies only the merge-strategy flag and its source; no case exercises the deletion mechanism.

Required handling when an eval-coverage sweep happens:

- Add a scenario assertion to `managing-pr.md` (or extend the merge-command scenario) declaring the deletion-mechanism choice as a separately observable behavior.
- Create `evals/merge-cleanup-deletion/` with a verdict schema carrying a deletion-mechanism field, exercising the overlay-silent worktree-safe path and the single-worktree inline opt-in.
- Run the eval to populate `history.jsonl`.

Surfaced by the local `changes-reviewer` gate on `fix/worktree-safe-branch-deletion` (2026-06-07).

## 4. Multi-worktree post-merge sync gap (FOLLOW-UP)

The merge overlay's Post-merge section (`spx/local/merging.md`) and the root `AGENTS.md` Sync step describe detaching the current worktree onto the merged `main` and running `just sync-marketplace`. In a bare-repo worktree pool (per `spx/21-spec-tree.enabler/11-repository-layout.pdr.md`) that is insufficient: the marketplace source is the `main` worktree, a different worktree from the pool worktree where the agent did the work. After a merge the agent must additionally fast-forward the `main` worktree's branch (`git -C <main-worktree> merge --ff-only origin/main`) before `just sync-marketplace`, or the sync re-reads stale `dist/` from the source worktree.

Observed on PR #143 (init-worktrees, 2026-06-08).

**Resolution shape**: the Post-merge section of `spx/local/merging.md` (and the `AGENTS.md` Sync step) should state, for the multi-worktree case, that the marketplace-source worktree (the one holding the default branch) is fast-forwarded to `origin/<default>` before `sync-marketplace`. Consider having `just sync-marketplace` detect and fast-forward the default-branch source worktree itself.

## 5. `merge-readiness` eval data model carries the removed `follow_up` severity (FOLLOW-UP)

The two-severity model (`spx/15-merging.pdr.md`, which absorbs the prior severity-disposition decision) carries only `blocking`/`debt`; the author judges disposition. The prose surfaces were aligned, but the `evals/merge-readiness/` data model still types each modeled `ci_review` finding's `severity` as `blocking | debt | follow_up` and uses a `valid follow_up` case to exercise "a valid finding that does not withhold the gate."

Under two severities that case becomes "a `valid` `debt` finding the author tracked out of scope (with a recorded reason) does not withhold the gate" — which the eval's finding model cannot express without a disposition/scope field. This is a coordinated `prompt.md` + `cases.jsonl` schema change requiring a live eval re-run.

Required handling when an eval-coverage sweep happens:

- Add a `scope`/`disposition` field (e.g., `in_scope` | `tracked_out_of_scope`) to the modeled finding in `evals/merge-readiness/prompt.md` and `cases.jsonl`, drop `follow_up` from the `severity` enum, and re-key the "does not withhold" case onto a `valid` `debt` finding marked tracked-out-of-scope.
- Model the bounded-vs-deferrable rule (`spx/15-merging.pdr.md`): a bounded `debt` fix is in-scope and withholds the gate until fixed; only a genuinely-separate-larger-concern `debt` is tracked out of scope and non-blocking.
- Re-run the eval to repopulate `history.jsonl` and confirm the threshold holds.

Surfaced during the two-severity propagation (2026-06-10).
