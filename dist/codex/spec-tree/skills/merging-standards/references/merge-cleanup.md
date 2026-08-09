<merge_cleanup>

Once `MERGE_READINESS` authorizes the merge and the mutation-point guard has produced `MERGE_READY:<head-sha>`, merge and clean up only in the assigned worktree. Never detach, clean, or delete a branch in a worktree a live agent holds.

Run every overlay-declared preflight check before the merge command and every post-cleanup check after detaching and before branch deletion. Use the overlay's merge flag; the default is `--merge`. A merge commit keeps every branch commit reachable, so the merged tip is a true ancestor of the base and `git branch -d` alone proves the branch deletable; the rebase and squash opt-ins rewrite commit identities and reach deletion only through the patch-equivalence fallback below. Always pass `--delete-branch=false` so branch cleanup remains explicit and worktree-safe.

```bash
base_from_pr=$(gh pr view <pr-number> --json baseRefName --jq '.baseRefName')
branch_from_pr=$(gh pr view <pr-number> --json headRefName --jq '.headRefName')
gh pr merge <pr-number> <overlay-merge-flag-or---merge> --delete-branch=false
git fetch origin "$base_from_pr"
git switch --detach "origin/$base_from_pr"
# Run every post-cleanup check declared by spx/local/merging.md here; continue only when all pass.
# Occupancy is established BEFORE any ref is removed, because a deleted remote ref
# cannot be restored from a retained local branch alone.
held_worktree=$(git worktree list --porcelain | awk -v branch="refs/heads/$branch_from_pr" '/^worktree /{path=substr($0,10)} $0=="branch " branch{print path; exit}')
if [ -n "$held_worktree" ]; then
  echo "Branch kept: path=$held_worktree branch=$branch_from_pr reason=held-by-live-worktree"
  exit 0
fi
# A worktree DETACHED at the branch tip holds no `branch` line, so the check above
# misses it while its uncommitted work still derives from this branch. `git branch
# --merged` hides that work too, so status is the only proof it is safe to delete.
if branch_tip=$(git rev-parse --verify --quiet "refs/heads/$branch_from_pr"); then
  dirty_at_tip=$(git worktree list --porcelain | awk '/^worktree /{print substr($0,10)}' \
    | while IFS= read -r wt_path; do
        [ "$(git -C "$wt_path" rev-parse HEAD 2>/dev/null)" = "$branch_tip" ] || continue
        [ -n "$(git -C "$wt_path" status --porcelain 2>/dev/null)" ] || continue
        printf '%s\n' "$wt_path"
      done)
  if [ -n "$dirty_at_tip" ]; then
    echo "Branch kept: branch=$branch_from_pr reason=uncommitted-work-at-branch-tip"
    printf '%s\n' "$dirty_at_tip" | while IFS= read -r wt_path; do
      echo "  worktree=$wt_path"
      git -C "$wt_path" status --porcelain
    done
    exit 0
  fi
fi
remote_branch_status=0
git ls-remote --exit-code --heads origin "$branch_from_pr" >/dev/null || remote_branch_status=$?
case "$remote_branch_status" in
  0) git push origin --delete "$branch_from_pr" || exit $? ;;
  2) ;;
  *) exit "$remote_branch_status" ;;
esac
if git rev-parse --verify --quiet "refs/heads/$branch_from_pr" >/dev/null; then
  local_branch_sha=$(git rev-parse "refs/heads/$branch_from_pr")
  if git merge-base --is-ancestor "$local_branch_sha" "origin/$base_from_pr"; then
    git branch -d "$branch_from_pr"
  elif cherry_output=$(git cherry "origin/$base_from_pr" "$local_branch_sha") && ! printf '%s\n' "$cherry_output" | grep -q '^+'; then
    # A rebase merge rewrites commit identities one-to-one, so ancestry fails while
    # every branch patch exists upstream; a git cherry that succeeds and reports no
    # `+` commit proves patch equivalence, and `git branch -D` is required because
    # `-d` re-checks ancestry. A failed git cherry proves nothing and falls through
    # to retention, as does a multi-commit squash, which collapses its patches into
    # one upstream commit that no per-commit patch-id matches.
    git branch -D "$branch_from_pr"
  else
    echo "Local branch kept: branch=$branch_from_pr tip=$local_branch_sha reason=not-proven-merged-by-ancestry-or-patch-equivalence-to-origin/$base_from_pr"
    git cherry -v --abbrev=40 "origin/$base_from_pr" "$local_branch_sha" || true
  fi
fi
git status --porcelain
```

Merge while the branch is checked out, then detach, run post-cleanup checks, and establish occupancy before removing any ref. Occupancy has two proofs and both precede deletion: `git worktree list` names a worktree holding the branch, and `git status` in every worktree sitting at the branch tip proves no uncommitted work would be lost. A worktree detached at the tip carries no `branch` line, so the worktree-list check alone misses it, and `git branch --merged` hides its uncommitted work — status is the only proof. Both checks run before `git push origin --delete`, because a removed remote ref cannot be restored from a retained local branch alone. Only then remove the remote ref when present, and delete the local branch when unoccupied and fully merged — its tip an ancestor of the fetched base, or every branch commit patch-equivalent to an upstream commit, the state a rebase merge or single-commit squash leaves behind. A multi-commit squash collapses its patches into one upstream commit that no per-commit patch-id matches, so that branch fails the proof, and a `git cherry` invocation that itself fails proves nothing. Retain every branch whose proof fails or cannot run and report its exact evidence, including the `git cherry` output naming each unmatched commit.

The tip check matches a worktree by commit alone, so a worktree parked at that same commit for an unrelated reason — one detached at the base right after a fast-forward merge, where base and branch tip are the same commit — reads as holding this branch's work. The match errs toward retention and never toward deletion, so the cost is a branch kept and reported with another worktree's status rather than uncommitted work lost.

</merge_cleanup>

<base_checkout_refresh>

The merge advanced the base on origin while the checkout that holds the base branch stayed at the pre-merge commit, so every worktree, tool, and later context load that resolves against it reads a stale commit. Cleanup closes by bringing that one checkout current.

Identifying it is `spx`'s job, never a ref scan: the pool diagnosis reports the one valid main checkout, and the same reading carries the health predicates that make it safe to name. Occupancy is a separate reading, because a clean working tree never proves a checkout is free.

1. Run `spx diagnose --format json` and read the `worktree-pool` record. Continue only when exactly one such record exists, its `verdict` is `compliant`, `readings.mainCheckoutBranchRead` is `true`, `readings.mainCheckoutBranch` equals `readings.defaultBranch`, and `readings.mainCheckoutPath` is a non-empty absolute path that differs from the assigned worktree root. Any other reading — including a layout with no pool and therefore no such record — skips the refresh with `reason=no-main-checkout`.
2. Run `spx worktree status --format json <main-checkout-path>`, passing the resolved path so the reading names that one checkout rather than requiring a match across an inventory. Continue only when its `status` is `free`. A `running` status skips with `reason=held-by-live-session`, naming the reported session; a checkout another session holds is never mutated on its behalf, exactly as a worktree holding the feature branch is never cleaned above.
3. Run `git -C <main-checkout-path> status --porcelain` and continue only when it prints nothing. Any output skips with `reason=uncommitted-work` — a fast-forward would carry those changes onto a different commit. Neither `spx` reading answers this, so it is a separate command.
4. Fast-forward it in place with `git -C <main-checkout-path> merge --ff-only origin/<base>`. A fast-forward advances the branch pointer only when the local branch is already an ancestor of the merged tip, so a checkout carrying its own unmerged commits fails the command and is reported with `reason=not-fast-forwardable` rather than rewritten.

Step 4 writes to a path outside the assigned worktree, and no skill's `allowed-tools` pre-authorizes it. That omission is deliberate. A harness declares the working directory a session may act in, and a write outside it is the operator's decision to approve, once per write — pre-clearing a write whose path is resolved at run time would convert that decision into a blanket grant over any path `spx` happens to report, because no pattern can name the one intended checkout in portable skill content. The refresh therefore surfaces its own approval prompt in a harness that enforces the boundary, and the prompt names the exact checkout being advanced. Never add a grant to suppress it, and never restate the command in a form built to match a broader existing pattern. Step 3's `status --porcelain` reads that same path and needs no such approval; it sits beside Step 4 because it guards it, not because a read carries the same weight as a write.

Every skipped case names its reason and leaves the checkout exactly as found. A stale base checkout is a reported condition, never a reason to force, reset, stash, or check the base branch out anywhere else.

</base_checkout_refresh>
