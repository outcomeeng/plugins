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
    printf 'Local branch deletion authorized: mode=safe branch=%s\n' "$branch_from_pr"
  elif cherry_output=$(git cherry "origin/$base_from_pr" "$local_branch_sha") && ! printf '%s\n' "$cherry_output" | grep -q '^+'; then
    # A rebase merge rewrites commit identities one-to-one, so ancestry fails while
    # every branch patch exists upstream; a git cherry that succeeds and reports no
    # `+` commit proves patch equivalence, and `git branch -D` is required because
    # `-d` re-checks ancestry. A failed git cherry proves nothing and falls through
    # to retention, as does a multi-commit squash, which collapses its patches into
    # one upstream commit that no per-commit patch-id matches.
    printf 'Local branch deletion authorized: mode=force branch=%s\n' "$branch_from_pr"
  else
    echo "Local branch kept: branch=$branch_from_pr tip=$local_branch_sha reason=not-proven-merged-by-ancestry-or-patch-equivalence-to-origin/$base_from_pr"
    git cherry -v --abbrev=40 "origin/$base_from_pr" "$local_branch_sha" || true
  fi
fi
git status --porcelain
```

Every proof run ends with `git status --porcelain`. An authorized literal
deletion receives a second status check after the direct deletion command.

When the proof block authorizes local deletion, type the printed branch name
literally into one direct `git branch` command. Use `-d` for `mode=safe` and
`-D` for `mode=force`. Never pass a variable, command substitution, array, or
glob to either form, including after `--` or inside quotes. After the literal
deletion command, run `git status --porcelain`.

Merge while the branch is checked out, then detach, run post-cleanup checks, and establish occupancy before removing any ref. Occupancy has two proofs and both precede deletion: `git worktree list` names a worktree holding the branch, and `git status` in every worktree sitting at the branch tip proves no uncommitted work would be lost. A worktree detached at the tip carries no `branch` line, so the worktree-list check alone misses it, and `git branch --merged` hides its uncommitted work — status is the only proof. Both checks run before `git push origin --delete`, because a removed remote ref cannot be restored from a retained local branch alone. Only then remove the remote ref when present, and authorize literal local-branch deletion when the branch is unoccupied and fully merged — its tip an ancestor of the fetched base, or every branch commit patch-equivalent to an upstream commit, the state a rebase merge or single-commit squash leaves behind. The proof reports the required deletion mode and resolved branch name; the deletion itself uses that name as a literal token in a separate direct command. A multi-commit squash collapses its patches into one upstream commit that no per-commit patch-id matches, so that branch fails the proof, and a `git cherry` invocation that itself fails proves nothing. Retain every branch whose proof fails or cannot run and report its exact evidence, including the `git cherry` output naming each unmatched commit.

The tip check matches a worktree by commit alone, so a worktree parked at that same commit for an unrelated reason — one detached at the base right after a fast-forward merge, where base and branch tip are the same commit — reads as holding this branch's work. The match errs toward retention and never toward deletion, so the cost is a branch kept and reported with another worktree's status rather than uncommitted work lost.

The merge advances the base on origin while the checkout that holds the base branch stays at the pre-merge commit. That checkout belongs to the environment rather than to the changeset, so bringing it current is the environment mutation `DEPLOY` governs, declared by a project in its overlay, never a step of this cleanup. Cleanup removes what the lifecycle created, and every ref it mutates is mutated from the assigned worktree — the `git -C` inspections above read other worktrees to prove a deletion is safe and mutate nothing.

</merge_cleanup>
