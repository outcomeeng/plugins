<merge_cleanup>

Once `MERGE_READINESS` authorizes the merge and the mutation-point guard has produced `MERGE_READY:<head-sha>`, merge and clean up only in the assigned worktree. Never detach, clean, or delete a branch in a worktree a live agent holds.

Run every overlay-declared preflight check before the merge command and every post-cleanup check after detaching and before branch deletion. Use the overlay's merge flag; the default is `--rebase`. Always pass `--delete-branch=false` so branch cleanup remains explicit and worktree-safe.

```bash
base_from_pr=$(gh pr view <pr-number> --json baseRefName --jq '.baseRefName')
branch_from_pr=$(gh pr view <pr-number> --json headRefName --jq '.headRefName')
gh pr merge <pr-number> <overlay-merge-flag-or---rebase> --delete-branch=false
git fetch origin "$base_from_pr"
git switch --detach "origin/$base_from_pr"
# Run every post-cleanup check declared by spx/local/merging.md here; continue only when all pass.
remote_branch_status=0
git ls-remote --exit-code --heads origin "$branch_from_pr" >/dev/null || remote_branch_status=$?
case "$remote_branch_status" in
  0) git push origin --delete "$branch_from_pr" || exit $? ;;
  2) ;;
  *) exit "$remote_branch_status" ;;
esac
held_worktree=$(git worktree list --porcelain | awk -v branch="refs/heads/$branch_from_pr" '/^worktree /{path=substr($0,10)} $0=="branch " branch{print path; exit}')
if [ -n "$held_worktree" ]; then
  echo "Local branch kept: path=$held_worktree branch=$branch_from_pr"
elif git rev-parse --verify --quiet "refs/heads/$branch_from_pr" >/dev/null; then
  local_branch_sha=$(git rev-parse "refs/heads/$branch_from_pr")
  if git merge-base --is-ancestor "$local_branch_sha" "origin/$base_from_pr"; then
    git branch -d "$branch_from_pr"
  else
    echo "Local branch kept: branch=$branch_from_pr tip=$local_branch_sha reason=not-ancestor-of-origin/$base_from_pr"
  fi
fi
git status --porcelain
```

Merge while the branch is checked out, then detach, run post-cleanup checks, remove the remote ref when present, and delete the local branch only when unoccupied and fully merged by ancestry. Retain every branch that fails those predicates and report its exact evidence.

</merge_cleanup>
