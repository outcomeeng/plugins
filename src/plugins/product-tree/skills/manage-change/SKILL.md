---
name: manage-change
description: >-
  ALWAYS invoke this skill when claiming, releasing, submitting, advancing,
  lowering, closing Applied, or closing Abandoned a Change in the declared
  Change Store. NEVER assign a Change, write its Maturity or Lifecycle, or close
  its issue by hand.
argument-hint: "<claim|release|submit|advance|lower|applied|abandoned> <#N | owner/repo#N | issue-url> [Maturity] [reason]"
arguments: transition reference
allowed-tools: Read, Write, Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh pr view:*), Bash(gh pr checks:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(gh api repos/*/issues/*/dependencies/blocked_by --method GET -F per_page=100), Bash(git status:*), Bash(git fetch:*), Bash(git switch:*), Bash(git branch --list:*), Bash(git ls-remote --heads origin:*), Bash(git worktree list --porcelain), Bash(git rev-parse:*), Bash(git merge-base --is-ancestor:*), Bash(git push -u origin HEAD:*), Bash(spx worktree status:*), Bash(spx diagnose:*), Bash(spx spec status:*), Bash(spx verification run render:*), Bash(spx verification run input:*), Bash(id -un), Bash(hostname -s),{!% if target == 'claude' %!} Bash(printenv CLAUDE_CODE_SESSION_ID), Agent,{!% else %!} Bash(printenv CODEX_THREAD_ID), {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}},{!% endif %!} {{! tool('use_skill') !}}
---

<objective>
One Transition made on one Change in the declared Change Store — its Transition comment the newest comment, every field it changes written to its home, and the complete state read back — or a refusal naming the state or the actor the Transition requires, with nothing written.
</objective>

<required_reading>

Use skill `product-tree:change-standards`. Its `<transitions>` table, `transition-actor`, and `<github_store>` rules govern every step below by their slugs. Read its `references/github-store.md` for every read and write, the Transition comment, and the write discipline.

Use skill `product-tree:commit-changes`. It commits the uncommitted session-owned work a `release` carries, in step 5.

Use skill `product-tree:sync-base`. It brings the claimed branch current, in step 8.

</required_reading>

<intake>

Take `$transition` as one of `claim`, `release`, `submit`, `advance`, `lower`, `applied`, and `abandoned`; any other value, an empty one included, is refused naming the seven, with nothing read. Take `$reference` as `#N`, `owner/repo#N`, or an issue URL; any other form is refused naming the three. `advance` takes a target Maturity as its next token, and an `advance` to Applicable then takes the run token of the record's sealed audit run; `lower` takes a target Maturity and then its reason, the rest of the arguments; a missing or unknown Maturity, or a `lower` without a reason, is refused naming what it lacks. `claim` takes an optional absolute worktree root to claim for, which must hold no `.` or `..` segment; without it, the claim is for this session's worktree. No other Transition takes a further token.

</intake>

<workflow>

1. **Read the Change.** Resolve the store under `<store_binding>` and read the issue, its fields, its comments, and its blockers under `<reads>`. Resolve the current login with `gh api user --jq .login`, the session id with `{!% if target == 'claude' %!}printenv CLAUDE_CODE_SESSION_ID{!% else %!}printenv CODEX_THREAD_ID{!% endif %!}`, the user and host with `id -un` and `hostname -s`, and the worktree with `git rev-parse --show-toplevel`. Derive the Change's type under `change-type` from the store's Parent values under `<reads>`. This session holds the Change when the issue's one assignee is the current login and the newest `claim` comment's `worktree` is this worktree; a session restart keeps the Claim under `claim-kept`, so the `session` may differ.
2. **Check the state.** Refuse the Transition, naming the state found, unless the Change stands in the state its `transitions` row requires: `claim` an open Available Change with no assignee; `release` a Change this session holds; `submit` an Available Change this session holds; `advance` a Submitted Change that meets the condition of each Maturity up to the target under `maturity-ready`, or a Sliced Leaf this session holds that meets the Applicable condition; `lower` a Framed, Sliced, or Applicable Change whose target is lower than its Maturity; `applied` and `abandoned` an open Change. A closed issue, or a Lifecycle of Applied or Abandoned, refuses every Transition under `terminal`.
3. **Check the actor.** Refuse the Transition, naming the actor `transition-actor` names, unless that actor makes it:
   - `claim`: any session.
   - `release` and `submit`: this session as holder.
   - `advance` to Framed or Sliced, `lower` for a reopened judgment, `abandoned` of a Change no merge absorbs, and `applied` of a Parent: the Operator's explicit direction, given in this conversation or in an order from the Operator's delegate.
   - `advance` of a Sliced Leaf to Applicable: this session as holder, once the Applicable condition holds as step 4 states.
   - `lower` to Sliced by the Applier, for a decision line that differs from the reviewed line or a failed Application check, and by any session whose publish wrote the body of an Applicable record: this session, naming that cause in the reason.
   - `lower` to Proposed for a reframe: this session as Refiner.
   - `abandoned` of a Change a merge absorbs: this session as Refiner, on the Operator's direction.
   - `applied` of a Leaf: this session as holder.
4. **Check the condition.**
   - For an `advance` to Sliced or Applicable, confirm `github-binding`: read the body's edit history and the Base field's change events under `<reads>`, and require the current body and Base to equal those the review or the audit read, or the review to carry forward to them under `review-carry`. For Applicable, require each Node the record's infrastructure lines name to stand on the default branch with State Passing under `spx spec status --format json`, or a blocker to build it. Read the audit's sealed run with `spx verification run render --verification-type audit --scope-type file --scope <owner>/<repo>#<N> --run <run-token>` and its retained record with the same arguments to `spx verification run input`; advance only when the run is sealed `approved` with no finding and the retained record's body and `base` equal the current body and Base, under `audit-binding`.
   - For `applied` of a Leaf, require every part of `leaf-applied`. Take the merge commit from the newest `release` comment's `handoff`, or from the pull request this session merged, with `gh pr view <pr> --json state,mergeCommit`; run `git fetch origin <default>` and require `git merge-base --is-ancestor <merge-commit> origin/<default>` to exit zero. Require each Node the Declarations name to hold every result its Malleability requires under `spx spec status --format json`, and every Declarations line to stand on the default branch. Require the audit at close: launch {!% if target == 'codex' %!}`product-tree_change-auditor`{!% else %!}`product-tree:change-auditor`{!% endif %!} once through the native subagent capability with the task message `<owner>/<repo>#<N> <absolute checkout root>`, and close only when its sealed run is `approved` with no finding. A failed condition refuses the Transition, naming the part that failed.
   - For `applied` of a Parent, require every Child closed under `<reads>`.
   - Before any write to Maturity or Lifecycle, run the option check of `<store_options>`; a field whose options differ stops the Transition naming the field.
5. **Prepare the checkout.** For a `claim` for another worktree, the comment's `worktree` is that root, and this step and step 8 leave every checkout as it is. For a `claim` for this worktree, run `spx worktree status` as a read-only check and require this session's `SessionStart` claim on the worktree; record no claim by hand. For `release`, run `git status --short --branch`: commit uncommitted session-owned work through `product-tree:commit-changes`, on the work branch `work/change-<N>` when the checkout is detached or on the default branch; push the branch with `git push -u origin HEAD:refs/heads/<branch>` and require the local and origin tips equal; run the preflight checks `spx/local/merging.md` declares, then `git switch --detach`, and the post-cleanup checks it declares. The live worktree claim stays with the session; never release it.
6. **Write in order**, under `<write_discipline>`:
   - `claim`: add the assignee, then post the `claim` comment.
   - `release`: post the `release` comment with its `handoff`, remove the assignee, then write Lifecycle Available when it reads Submitted.
   - `submit`: write Lifecycle Submitted, then post the `submit` comment.
   - `advance`: write the target Maturity, then post the `advance` comment.
   - `lower`: write the target Maturity, then post the `lower` comment with its `reason`. After a lower other than the Applier's to write a decision line, make the `release` Transition next under `lower-claim`.
   - `applied`: post the `applied` comment, with `changeset` for a Leaf, remove the assignee, write Lifecycle Applied, then close the issue as completed.
   - `abandoned`: post the `abandoned` comment, remove the assignee, write Lifecycle Abandoned, then close the issue as not planned.
7. **Read back** under `<write_discipline>`: every field the Transition writes equals its target, every other field is unchanged, the assignee list is the intended holder or empty, and the Transition's own comment is the newest Transition comment.
8. **Bring the branch.** After a `claim` for this worktree, read the newest `release` comment's `handoff.branch`. For a branch on origin, `git fetch origin <branch>`; when `git worktree list --porcelain` shows another worktree holding it, run `git switch -c <branch>-<n> origin/<branch>` with the first `<n>` from 2 for which `git branch --list` and `git ls-remote --heads origin` print nothing; otherwise `git switch <branch>`. A failed fetch or switch leaves the Claim standing and the checkout unchanged, and is reported verbatim. Then use skill `product-tree:sync-base`.

</workflow>

<result>

Return the issue URL, the Transition, the readback values verbatim, and the comment's YAML block. A refusal returns the Transition, the state or the actor it required, the state found, and no write.

</result>

<failure_modes>

**The assignee stood in for the holding session.** Claude treated the assignee as proof that this session held the Change while a second session of the same account worked in another worktree. One account runs several sessions, so the newest `claim` comment's worktree names the session's place; the assignee alone names only the account.

**A partial Transition was repaired by guessing.** Claude's Lifecycle write failed after the comment landed, and Claude re-ran a later step to make the state look complete. Stop at the failed write, report the completed writes and the observed state, and leave the partial state visible.

</failure_modes>

<success_criteria>

- A Transition ran only on a Change in the state its row requires and for the actor `transition-actor` names; every other request was refused with nothing written.
- Each Transition posted exactly one comment, a YAML block with the keys `log-keys` names and only the extra its row admits.
- No write reached a Maturity, Lifecycle, Value, or Investment field whose options differ from the values the standards name.
- The issue carries at most one assignee, and the readback shows every written field at its target and every other field unchanged.
- A release left the work branch pushed and the worktree detached from it, and a claim brought the newest Handoff's branch into this worktree.

</success_criteria>
