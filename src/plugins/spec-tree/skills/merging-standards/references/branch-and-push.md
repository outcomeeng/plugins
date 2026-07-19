<git_lifecycle>

<branch_state_closeout>

After a default-branch merge, every transport produces branch-state closeout evidence before the final operator closeout. The GitHub-PR transport builds the full branch-state closeout record during post-merge management, continues remaining in-scope work, and passes the record into `/handoff` when the session is complete. The direct-push transport preserves merge-time facts and delegates full record construction to `/handoff`, which computes the record from this section using its own closeout tool surface. The record removes ambiguity about which refs still exist, which are safe to delete, and which require operator attention.

The closeout record includes:

- PR number and merge commit SHA when the transport used a pull request; direct-push transports record the default-branch HEAD SHA after publication.
- Merged branch name.
- Whether the remote branch still exists.
- Whether the local branch still exists.
- Whether the local branch is fully merged into `origin/<base>`.
- Whether any live worktree checks out the local branch.
- Whether any preservation branch was created.
- For each preservation branch, whether its commits are exact ancestors of `origin/<base>`.
- For each non-ancestor preservation branch, `git cherry -v --abbrev=40 origin/<base> <branch>` output as patch-equivalence evidence.
- Final worktree state: clean or dirty, branch or detached, and current full HEAD SHA.
- Release-source worktree state when a declared release or marketplace refresh used a separate source worktree: path, branch, full HEAD SHA, clean or dirty, and sync status.

Use full branch names and full commit SHAs. Do not abbreviate identity values in the record, in commands, or in the final closeout.

Safe cleanup policy:

- If the remote feature branch exists after merge, delete it through the merge lifecycle's approved deletion command.
- If the local feature branch exists, its remote ref is absent, no live worktree checks it out, and its tip is an ancestor of `origin/<base>`, delete it with `git branch -d <branch>` regardless of upstream configuration.
- If a preservation branch has no remote and all substantive commits are present on `origin/<base>` by ancestry or patch equivalence, report it as safe to delete and delete it unless the branch name or operator instruction marks it as retained evidence.
- Never delete a branch checked out in another live worktree. Report the exact worktree path and branch instead.
- Never delete a branch whose commits are neither ancestors nor patch-equivalent to `origin/<base>`. Report the unmatched full SHAs and keep the branch.

Use git state observations rather than memory for every record field. The patch-equivalence observation is `git cherry -v --abbrev=40 origin/<base> <branch>`.

The final `/handoff` closeout includes a compact **Remaining Branches** section with exactly these groups:

- **Deleted locally**
- **Deleted remotely**
- **Retained, with reason**
- **Needs operator decision, with exact evidence**

</branch_state_closeout>

<local_deterministic_scope>

Local deterministic verification is the author-side validation and testing predicate for the exact changeset about to be published. It is scoped to the touched evidence by default:

- **Validation**: run the narrow validation lane that covers changed specs, skill files, generated plugin output, validation configuration, or implementation files. For Markdown-only skill/spec changes, this usually means the documented skill/doc or markdown validation commands rather than the full repository gate.
- **Testing**: run the node, package, module, or language test commands that exercise the assertions, source contracts, and implementation files the changeset touched.
- **Escalation**: run broader local validation/testing only when the overlay, governing node, or risk evidence requires it — for example a change to validation infrastructure, test runner wiring, generated distribution, package manager config, shared runtime code, or a broad refactor whose touched-scope commands cannot cover the contract.

CI owns full-repository deterministic regression detection. The author still owns all verification types locally: validate, test, review, and audit run before publication, but local validate/test are scoped while review/audit inspect the changeset and the touched node(s).

Run long or verbose deterministic commands with complete stdout/stderr redirected to a temporary log path, then inspect the summary, exit status, and failing sections. Do not stream passing-test logs through the session transcript. Keep the log path only when a failure requires later inspection; a passing run needs the command, exit code, and concise summary.

</local_deterministic_scope>

<assigned_cwd_worktree_discipline>

The changeset's git work — branch, commit, push, base-sync, PR management, merge, and its cleanup — happens in the **assigned worktree**, the repository working directory the session started in. The constraint that decides what is off-limits is **occupancy**, not worktree identity: a worktree is held by a live agent (claimed) or free, and in a bare-repository pool the default branch is unattached and claimable by any worktree.

- NEVER run the changeset's git work in a worktree **a live agent holds** — that collision is what this discipline prevents. NEVER create a worktree to carry the work, and NEVER use `git stash`; a dirty tree is cleared by committing per `<base_sync>`, never by stashing.
- A worktree or branch conflict is never a stopping point — it is branch-here-and-continue. When the assigned worktree is on the default branch, a detached HEAD, a dirty branch, or a branch name another worktree holds, create a fresh task branch in the assigned worktree from the resolved base and continue. When a PR branch is held in another worktree it is unavailable locally: stay in the assigned worktree, create a fresh branch there from the correct base or remote head, and push or open the PR from that branch.

Claude NEVER stops with blocked-by-worktree, cannot-use-other-worktree, or cannot-create-worktree reasoning. Branch in the assigned worktree and continue.

</assigned_cwd_worktree_discipline>

<branch_hygiene>

Conditions that must hold before every push (initial or follow-up). The consuming flow MUST set `active_base` from the classified topology and `publication_phase` to exactly `initial` or `follow-up` before applying this gate. The active base is the repository default for a peer, the previous stack branch while a stacked PR's base remains unmerged, and the repository default after stack reconstruction. Branch hygiene consumes both values and never re-derives them. The existing-open-PR predicate applies only to `publication_phase=initial`; a follow-up publication already has the PR that `/manage-pr` is advancing. A branch-state failure is resolved in place per `<assigned_cwd_worktree_discipline>` — branch in the assigned worktree and continue, never switch to another worktree and never stash; the remaining conditions stop the lifecycle until resolved.

| Condition (must hold)                                    | Failure response                                                                                                                    |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Current branch is not `main`, `master`, or detached HEAD | Create a fresh task branch in the assigned worktree from the resolved base and continue, per `<assigned_cwd_worktree_discipline>`.  |
| Working tree is clean (no uncommitted changes)           | Commit via /commit-changes before pushing — never stash.                                                                            |
| Branch is at least one commit ahead of `active_base`     | STOP. Confirm the active topology base — there is nothing to PR.                                                                    |
| Branch is not behind `active_base` (no upstream commits) | Rebase onto `origin/<active-base>` per `<base_sync>`, then re-run this gate.                                                        |
| Branch topology is classified as peer or stacked         | STOP. Apply `<branch_topology>` before continuing.                                                                                  |
| Work branch is not tracking `active_base`                | STOP. Replace the upstream before pushing.                                                                                          |
| Initial publication has no existing open PR              | Record the full open PR URL, invoke `/manage-pr <pr-url>`, and exit the opening protocol. Skip this predicate for follow-up pushes. |
| `gh auth status` reports an authenticated token          | STOP. Resolve auth before continuing.                                                                                               |

Commands:

```bash
gh auth status
git branch --show-current
git status --porcelain
: "${active_base:?active lifecycle base must be set before branch hygiene}"
: "${publication_phase:?publication phase must be initial or follow-up}"
case "${publication_phase}" in
  initial | follow-up) ;;
  *) echo "STOP: publication phase must be initial or follow-up" >&2; exit 1 ;;
esac
git fetch origin "${active_base}"
git log --oneline "origin/${active_base}..HEAD"
git diff "origin/${active_base}...HEAD" --stat
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [ "${upstream}" = "origin/${active_base}" ]; then
  echo "STOP: work branch tracks the active lifecycle base" >&2
  exit 1
fi
if [ "${publication_phase}" = "initial" ]; then
  existing_url=$(gh pr view --json url,state --jq 'select(.state == "OPEN") | .url' 2>/dev/null)
  [ -n "$existing_url" ] && echo "PR already exists: $existing_url"
fi
```

The `exit 1` inside the upstream-safety check is a STOP for the lifecycle.

</branch_hygiene>

<branch_topology>

Every PR branch is one of two shapes:

| Shape   | Meaning                                                                               | Required handling                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Peer    | Targets the repository default branch and contains only its own review payload.       | Create from the current default branch. Refuse stale sibling merge commits.                                                               |
| Stacked | Intentionally depends on another unmerged branch and targets that branch as its base. | Name the exact base PR URL and branch in the PR body. Keep draft until that PR merges, then reconstruct onto default base and open ready. |

**Peer-gate** (all must hold): `origin/${base}` is an ancestor of `HEAD`; the commit list contains only the intended payload; the changed file list matches the PR scope; no merge commits from sibling work.

```bash
base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git fetch origin "${base}"
git merge-base --is-ancestor "origin/${base}" HEAD
git log --merges "origin/${base}..HEAD"
git log --oneline "origin/${base}..HEAD"
git diff --name-only "origin/${base}...HEAD"
```

**Peer-gate failure path.** Pick exactly one repair before pushing:

1. **Repair as peer** — divergence unintentional. Rebase onto `origin/${base}`, drop sibling merge commits, re-run the gate.
2. **Reclassify as stacked** — dependency on an unmerged base is intentional. Before a PR exists, use an exact stack-base PR pointer already known to this skill or acquire one through the active structured-question capability, resolve its host-observed URL and `headRefName` with `gh pr view`, set that branch as the active base and `<base>` argument for `gh pr create`, and run the pre-create stacked classification against it.

**Pre-create stacked classification** (all must hold): an exact stack-base PR pointer is already known or obtained through the active structured-question capability; `gh pr view` resolves that pointer to an open pull request; its host-observed URL and `headRefName` are recorded as `stack_base_pr_url` and `stack_base`; `origin/${stack_base}` is an ancestor of `HEAD`; and the commit and changed-file lists against `origin/${stack_base}` contain only the intended stacked payload.

**Existing-PR stacked gate** (all must hold): the PR base is the recorded `stack_base`; the PR body's `## Stack` section names the exact recorded `stack_base_pr_url` and `stack_base`; the URL resolves to that branch's pull request; the current PR remains draft while that exact base PR is unmerged; after the base PR merges, the branch is rebased onto the updated default branch before final merge.

Before the current PR exists, identify stack topology only from an exact stack-base PR pointer already known to this skill or obtained through the active structured-question capability. Resolve that pointer with `gh pr view`, require the base PR to be open, and record its host-observed URL and `headRefName` as `stack_base_pr_url` and `stack_base`; these values govern pre-open base sync, verification scope, the `gh pr create --base` argument, and the new PR body's `## Stack` section. After the current PR exists, identify stack topology from that durable `## Stack` section. When the section is absent for a non-default-base or draft PR, use an exact base-PR pointer already supplied by the operator or ask for one through the active structured-question capability. Never infer a stack base from branch naming or reconstruct merged-PR identity from a branch label.

```bash
base_branch="<previous-stack-branch>"
gh pr view "<stack-base-pr-url>" --json number,url,state,mergedAt,headRefName,headRefOid,baseRefName
git fetch origin "${base_branch}"
git merge-base --is-ancestor "origin/${base_branch}" HEAD
git log --oneline "origin/${base_branch}..HEAD"
git diff --name-only "origin/${base_branch}...HEAD"
```

**Post-merge reconstruction.** Once the exact stack-base PR URL reports merged, repeat the publication protocol to re-target the PR at the default branch, replace its body without the complete `## Stack` section or any retired stack-base reference, re-classify it as peer, and mark it ready exactly once. GitHub auto-retargets the PR base on the API side, but the local branch must still be rebased onto the updated default and the manifest version re-evaluated against the new base.

</branch_topology>

<push_semantics>

Always push with an explicit destination ref:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"          # first push
git push    origin HEAD:refs/heads/"${branch}"          # subsequent pushes
git push --force-with-lease origin HEAD:refs/heads/"${branch}"  # after a rebase (see <base_sync>)
```

The bare `git push` and `git push -u origin <branch>` forms are forbidden because `push.default=tracking` would publish feature-branch commits to whatever upstream is configured locally — including `main` when the branch was created from `main` without an upstream reset. The `HEAD:refs/heads/<branch>` form makes the remote branch explicit and removes the dependency on local upstream configuration.

A rebase rewrites branch history, so the post-rebase push cannot fast-forward. `--force-with-lease` performs the non-fast-forward push but refuses if the remote branch advanced since the last fetch, which keeps it safe on a single-author PR branch. Plain `git push --force` stays forbidden — it overwrites the remote unconditionally.

If the product defines a custom branch-push command, follow the product convention from {{! file('root_guide') !}} — the explicit destination ref must remain part of any custom command.

</push_semantics>

<base_sync>

Base drift is checked on the same checkpoint that inspects reviews — every management pass reads review state and the `origin/<base>` position together. When the branch is behind `origin/<base>`, sync immediately through `/sync-base`, independent of whether a review has landed and independent of whether any landed review carries findings.

`/sync-base` owns the mechanism: it fetches the base, rebases the branch onto `origin/<base>`, and never uses `git reset` to integrate base movement. Claude NEVER asks the operator whether to rebase — base-sync is a mechanical consequence of observable git state, not a decision to surface; surfacing "should I rebase?" through a structured question or in prose is a defect. A clean rebase runs to completion with no operator interaction. A conflict `/sync-base` cannot resolve autonomously is reported as `conflict` with a structured `conflict` object; the rebase remains active so the operator can inspect, resolve and continue, or abort. A `dirty_tree` outcome — uncommitted tracked changes blocking the rebase — is not a conflict: commit the working changes through `/commit-changes`, then re-run `/sync-base`. Never stash, and Claude never surfaces a dirty tree as an operator decision.

Rebase on drift, not at merge time. A branch behind base is superseded by a rebase before it can merge, so every check run and every review posted against the un-rebased head is wasted effort. Rebasing the moment drift appears aims CI and reviewers at the head that will actually merge, and surfaces a conflicted ("nasty") rebase early during review/check convergence instead of at merge time, where an unexpected conflict or an integration regression costs a full extra review round on the critical path.

Invoke `/sync-base` with the active lifecycle base passed as `--base ${base}` rather than letting it re-derive one. After a PR exists, capture `${base}` from `gh pr view --json baseRefName`, which returns the actual base for peer and stacked topologies. Before a PR exists, use the active topology established by `<branch_topology>`: the repository default from `gh repo view --json defaultBranchRef` for a peer, or the host-observed `stack_base` resolved from the explicit stack-base PR pointer for a stack.

When `/sync-base` reports `rebased`, the rebased tree is a fresh integration — this branch replayed on newly merged work — and the consuming flow re-establishes all `VERIFICATION_READINESS` predicates on it before the `--force-with-lease` push from `<push_semantics>`, fixing any failure or unaddressed valid finding in the same pass. The `preservation` proof in the `/sync-base` result scopes how much of that work the base movement actually invalidated, so a rebase that moved an unrelated part of the tree does not force a full re-run:

- **Local review.** Reuse the converged `changes-reviewer` verdict when `preservation.branch_diff_unchanged` is true **and** no `preservation.base_delta_paths` entry appears in `verification_contract.governance_surfaces`. Otherwise re-establish the review per `<local_review_invocation>` on the rebased diff.
- **Evidence-auditor predicates.** Reuse a prior evidence-auditor verdict only when `preservation.branch_diff_unchanged` is true and no `preservation.base_delta_paths` entry touches a governed evidence surface. Otherwise re-dispatch the applicable evidence auditors before local review.
- **Deterministic verification.** Run the narrowest local validation/testing lane `verification_contract` maps `preservation.base_delta_paths` to per `<local_deterministic_scope>`; widen only when an entry is unclassified, `preservation.path_overlap` is non-empty, `preservation.branch_patch_changed` is true, or the contract or risk evidence requires it.

The proof scopes pre-push local work only. After the push, `MERGE_READINESS` still requires every current-head required check terminal-green and a clean current-head CI review — a preservation proof never substitutes for either. When `verification_contract` declares no lane mapping, run its full deterministic-verification command and re-establish the review on every rebase.

Integrate base movement only by rebase through `/sync-base`. The same prohibition binds the review-convergence loop, where Claude reorganizes the branch's own commits: NEVER `git reset` onto `origin/<base>` — not to integrate base movement, and not to reword or re-split the branch's own commits. `origin/<base>` advances as concurrent worktree-pool branches merge, so a reset onto it silently re-bases the branch onto whatever it became; with `--soft` the working tree is left on the old basis while HEAD jumps forward, desyncing the tree (files present in HEAD show as deleted, files the new base changed show as modified, none of it the branch's work). To reword or re-split the branch's own commits, reset to a FIXED ancestor on the branch — `git reset --soft HEAD~N` where N is the branch's own commit count, or the fork-point SHA from `git merge-base HEAD origin/<base>` — never onto `origin/<base>`. After any history rewrite, confirm `git diff --stat origin/<base>...HEAD` shows only the intended files and `git status` reports no surprise deletions before the `<push_semantics>` push; surprise files mean the base moved under the rewrite — stop and re-derive, do not push.

</base_sync>

<local_review_invocation>

The local `changes-reviewer` gate is the author-side, pre-push instance of the same review kind the CI review runs post-push — the two are the same class of gate on opposite sides of each push. Invoke it the way CI invokes its reviewer, passing nothing that narrows it:

- **Let the review resolve its own scope.** `changes-reviewer` self-discovers the worktree it runs in and computes the diff itself. Make the base explicit only when the changeset's base is not `origin/HEAD` (a stacked PR), and pass nothing else — no file list, no changed-area summary, no "the important part is …".
- **Add no interpretive scope.** Do not tell the reviewer which layers, files, or concerns to weight. It reviews the whole diff against the whole taxonomy.
- **Add no severity pre-filter.** Do not ask only for `BLOCKING`, do not suppress `DEBT`. The reviewer emits every finding; handling is by validity and phase per `<review_classification>`, downstream of the review and never inside its invocation.
- **Add no emphasis steering.** Do not tell the reviewer what to conclude or what matters most. It reads the repository's own instructions ({{! file('root_guide') !}} and the standards skills) and the shared taxonomy itself.

Run it via the `changes-reviewer` agent. The isolated context keeps the verdict from being biased by what the operator's main context has been doing. Iterate to convergence: each round, act on findings by validity and phase per `<review_classification>`, until no valid finding remains unaddressed.

This is the review predicate `VERIFICATION_READINESS` reads, and it runs against the diff before every opening and follow-up push. Narrowing the invocation diverges the local gate from the CI reviewer it parallels, so its convergence no longer means what `VERIFICATION_READINESS` claims it means.

</local_review_invocation>

</git_lifecycle>
