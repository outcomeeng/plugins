---
name: manage-change
description: >-
  ALWAYS invoke this skill when claiming, releasing, submitting, advancing,
  lowering, closing Applied, or closing Abandoned a Change in the declared
  Change Store, or when recording a decision to work on a Submitted Change.
  NEVER assign a Change, write its Maturity or Lifecycle, or close its issue by
  hand.
argument-hint: "<claim|release|submit|advance|lower|applied|abandoned|work> <#N | owner/repo#N | issue-url> [Maturity] [reason | survivor]"
arguments: transition reference
allowed-tools: Read, Write, Glob, Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh pr view:*), Bash(gh pr checks:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(gh api repos/*/issues/*/dependencies/blocked_by --method GET -F per_page=100), Bash(git status:*), Bash(git fetch:*), Bash(git switch:*), Bash(git branch --list:*), Bash(git ls-remote --heads origin:*), Bash(git worktree list --porcelain), Bash(git rev-parse:*), Bash(git merge-base --is-ancestor:*), Bash(git push -u origin HEAD:*), Bash(spx worktree status:*), Bash(spx diagnose:*), Bash(spx spec status:*), Bash(spx verification run render:*), Bash(spx verification run input:*), Bash(id -un), Bash(hostname -s), Bash(printenv CODEX_THREAD_ID), collaboration.spawn_agent, collaboration.wait_agent
---

<objective>
One Transition made on one Change in the declared Change Store — its Transition comment the newest comment, every field it changes written to its home, and the complete state read back — or one decision to work on a Submitted Change recorded as its Lifecycle `Available`, or a refusal naming the state or the actor the move requires, with nothing written.
</objective>

<required_reading>

Use skill `product-tree:change-standards`. Its `<transitions>` table, `transition-actor`, and `<github_store>` rules govern every step below by their slugs. Read its `references/github-store.md` for every read and write, the Transition comment, and the write discipline.

Use skill `product-tree:commit-changes`. It commits the uncommitted session-owned work a `release` carries, in step 5, with the Change's `<owner>/<repo>#<N>` as its work item reference, so each commit's `Refs:` footer carries the Change's reference.

Use skill `product-tree:sync-base`. It brings the claimed branch current, in step 8.

</required_reading>

<intake>

Take `$transition` as one of the seven Transitions `claim`, `release`, `submit`, `advance`, `lower`, `applied`, and `abandoned`, or as `work`, the record of a decision to work on a Submitted Change, which is no Transition and runs `<work_decision>` in place of `<workflow>`; any other value, an empty one included, is refused naming the eight, with nothing read. Take `$reference` as `#N`, `owner/repo#N`, or an issue URL; any other form is refused naming the three. `advance` takes a target Maturity as its next token, and an `advance` to Applicable then takes the run token of the record's sealed audit run; `lower` takes a target Maturity and then its reason, the rest of the arguments; a missing or unknown Maturity, or a `lower` without a reason, is refused naming what it lacks. `claim` takes an optional absolute worktree root to claim for, which must hold no `.` or `..` segment; without it, the claim is for this session's worktree. `abandoned` takes an optional survivor reference, in one of the three forms, when a merge absorbs the Change; a survivor in another store than the declared one is refused naming both. No other Transition, and not `work`, takes a further token.

</intake>

<workflow>

1. **Read the Change.** Resolve the store under `<store_binding>` and read the issue, its fields, its comments, and its blockers under `<reads>`. Resolve the current login with `gh api user --jq .login`, the session id with `printenv CODEX_THREAD_ID`, the user and host with `id -un` and `hostname -s`, and the worktree with `git rev-parse --show-toplevel`. Derive the Change's type under `change-type` from the store's Parent values under `<reads>`. This session holds the Change when the issue's one assignee is the current login and the newest `claim` comment's `worktree` is this worktree; a session restart keeps the Claim under `claim-kept`, so the `session` may differ.
2. **Check the state.** Refuse the Transition, naming the state found, unless the Change stands in the state its `transitions` row requires: `claim` an open Available Change with no assignee; `release` a Change this session holds; `submit` an Available Change this session holds; `advance` an Available Change that meets the condition of each Maturity up to the target under `maturity-ready`, or a Sliced Leaf this session holds that meets the Applicable condition; `lower` a Framed, Sliced, or Applicable Change whose target is lower than its Maturity; `applied` and `abandoned` an open Change. A closed issue, or a Lifecycle of Applied or Abandoned, refuses every Transition under `terminal`.
3. **Check the actor.** Refuse the Transition, naming the actor `transition-actor` names, unless that actor makes it:
   - `claim`: any session.
   - `release` and `submit`: this session as holder.
   - `advance` to Framed or Sliced: the Operator's explicit direction, given in this conversation or in an order from the Operator, or this session as the delegate of that advance under `<delegate_grant>`.
   - `lower` for a reopened judgment, `abandoned` of a Change no merge absorbs, and `applied` of a Parent: the Operator's explicit direction, given in this conversation or in an order from the Operator.
   - `advance` of a Sliced Leaf to Applicable: this session as holder, once the Applicable condition holds as step 4 states.
   - `lower` to Sliced by the Applier, for a decision line that differs from the reviewed line or a failed Application check, and by any session whose publish wrote the body of an Applicable record: this session, naming that cause in the reason.
   - `lower` to Proposed for a reframe: this session as Refiner.
   - `abandoned` of a Change a merge absorbs: this session as Refiner, on the Operator's direction, with the survivor's reference; the survivor must name the absorbed Change in its `predecessors`, read under `<reads>`, and an `abandoned` with no survivor is the Operator's Abandoned close of a Change no merge absorbs.
   - `applied` of a Leaf: this session as holder.
4. **Check the condition.**
   - For an `advance` to Sliced or Applicable, confirm `github-binding`: read the body's edit history and the Base field's change events under `<reads>`, and require the current body and Base to equal those the review or the audit read, or the review to carry forward to them under `review-carry`. For Applicable, require each Node the record's infrastructure lines name to stand on the default branch with State Passing under `spx spec status --format json`, or a blocker to build it. Read the audit's sealed run with `spx verification run render --verification-type audit --scope-type file --scope <owner>/<repo>#<N> --run <run-token>` and its retained record with the same arguments to `spx verification run input`; advance only when the run is sealed `approved` with no finding and the retained record's body and `base` equal the current body and Base, under `audit-binding`.
   - For `applied` of a Leaf, require every part of `leaf-applied`. Take the merge commit from the newest `release` comment's `handoff`, or from the pull request this session merged, with `gh pr view <pr> --json state,mergeCommit`; run `git fetch origin <default>` and require `git merge-base --is-ancestor <merge-commit> origin/<default>` to exit zero. Require each Node the Declarations name to hold every result its Malleability requires under `spx spec status --format json`, and every Declarations line to stand on the default branch. Require the audit at close: launch `product-tree_change-auditor` once through the native subagent capability with the task message `<owner>/<repo>#<N> <absolute checkout root>`, and close only when its sealed run is `approved` with no finding. A failed condition refuses the Transition, naming the part that failed.
   - For `applied` of a Parent, require every Child closed under `<reads>`.
   - Before any write to Maturity or Lifecycle, run the option check of `<store_options>`; a field whose options differ stops the Transition naming the field.
5. **Prepare the checkout.** For a `claim` for another worktree, the comment's `worktree` is that root, and this step and step 8 leave every checkout as it is. For a `claim` for this worktree, run `spx worktree status` as a read-only check and require this session's `SessionStart` claim on the worktree; record no claim by hand. For `release`, run `git status --short --branch`, then `git fetch origin <default>` and `git log --format='%H%n%B%x00' origin/<default>..HEAD`, which lists the commits the checkout holds ahead of the default branch with their messages. A commit carries a Change's reference when its message names `<owner>/<repo>#<N>` of the declared Change Store, or `#<N>` when the checkout's `origin` is the Change Store's own repository. Take the first case that holds:
   - **The checkout is attached to a branch, at least one commit is ahead, and every commit ahead carries this Change's reference.** That branch is the Change's own work branch, also when no Handoff names it, as on a first release or on the `<branch>-<n>` step 8 brought. Commit uncommitted session-owned work of the Change on it through `product-tree:commit-changes` with the work item reference `<owner>/<repo>#<N>`, push it with `git push -u origin HEAD:refs/heads/<branch>`, and require the local and origin tips equal. The Handoff names that branch and its head.
   - **No commit is ahead, or a commit ahead carries another Change's reference.** The branch the checkout holds, or its detached commit, is never the Change's own work branch. The Handoff branch is the branch the newest `release` comment's `handoff.branch` names, when it names one other than `none`, and it is the own work branch when it exists. Take the first sub-case that holds:
     - **A Handoff branch exists and the session holds uncommitted work of the Change.** Stop before any write and report the Handoff branch, the branch or commit the checkout holds, and the uncommitted paths.
     - **A Handoff branch exists and the session holds no uncommitted work of the Change.** Push nothing. The Handoff names that branch and its head on origin.
     - **No Handoff branch exists and the session holds uncommitted work of the Change.** Run `git switch -c work/change-<N> origin/<default>`, which carries the uncommitted work onto a branch cut from the head of the default branch that holds no commit of another Change. When `git branch --list` or `git ls-remote --heads origin` already shows `work/change-<N>`, or the switch refuses because the work does not apply on the default branch, stop before any write and report the branch, the uncommitted paths and the refusal verbatim. Commit the work through `product-tree:commit-changes` with the work item reference `<owner>/<repo>#<N>`, push the branch as above, and name it and its head in the Handoff.
     - **No Handoff branch exists and the session holds no uncommitted work of the Change.** Push no branch, also when the checkout is attached to a branch that carries another Change's work. The Handoff holds `branch: none` and the head of the default branch.
   - **Otherwise** a commit ahead carries no Change's reference, or the checkout is detached at commits that all carry this Change's reference. Stop before any push and any write, and name each such commit by its full SHA and subject.

   Then run the preflight checks `spx/local/merging.md` declares, `git switch --detach`, and the post-cleanup checks it declares. The live worktree claim stays with the session; never release it.
6. **Write in order**, under `<write_discipline>`:
   - `claim`: add the assignee, then post the `claim` comment.
   - `release`: post the `release` comment with its `handoff`, remove the assignee, then write Lifecycle Available when it reads Submitted.
   - `submit`: write Lifecycle Submitted, then post the `submit` comment.
   - `advance`: write the target Maturity, then post the `advance` comment.
   - `lower`: write the target Maturity, then post the `lower` comment with its `reason`. After a lower other than the Applier's to write a decision line, make the `release` Transition next under `lower-claim`.
   - `applied`: post the `applied` comment, with `changeset` for a Leaf, remove the assignee, write Lifecycle Applied, then close the issue as completed.
   - `abandoned`: post the `abandoned` comment, remove the assignee, write Lifecycle Abandoned, then close the issue as not planned, or, for a Change a merge absorbs, as a duplicate of the survivor's issue, so that the absorbed issue's duplicate link names the survivor.
7. **Read back** under `<write_discipline>`: every field the Transition writes equals its target, every other field is unchanged, the assignee list is the intended holder or empty, and the Transition's own comment is the newest Transition comment.
8. **Bring the branch.** After a `claim` for this worktree, read the newest `release` comment's `handoff.branch`. For a branch on origin, `git fetch origin <branch>`; when `git worktree list --porcelain` shows another worktree holding it, run `git switch -c <branch>-<n> origin/<branch>` with the first `<n>` from 2 for which `git branch --list` and `git ls-remote --heads origin` print nothing; otherwise `git switch <branch>`. A failed fetch or switch leaves the Claim standing and the checkout unchanged, and is reported verbatim. Then use skill `product-tree:sync-base`.

</workflow>

<work_decision>

`work` records a decision of the Operator, or of a delegate, to work on a Submitted Change, under `work-decision` of `product-tree:change-standards`. It is no Transition.

1. **Read the Change** as step 1 of `<workflow>` states.
2. **Check the state.** Refuse, naming the state found, unless the issue is open and its Lifecycle reads `Submitted`.
3. **Check the actor.** Refuse, naming the Operator or a delegate as the actor the decision requires, unless the decision comes as the Operator's explicit direction, given in this conversation or in an order from the Operator, or this session is a delegate whose authorization in the grant record, read as `<delegate_grant>` states, names the decision to work on a Change of the Change's Product, or of every Product of the Change Store.
4. **Write.** Run the option check of `<store_options>` on Lifecycle, then write Lifecycle `Available`. Keep the assignee, and post no Transition comment.
5. **Read back** under `<write_discipline>`: Lifecycle reads `Available`, every other field and the assignee list are unchanged, and the newest Transition comment is the one that stood before.

A decision against the Change is no `work`: it is the `abandoned` Transition, on the Operator's direction.

</work_decision>

<delegate_grant>

A session is the delegate of an advance to Framed or Sliced only while the grant record names its authorization grant for that advance, under `transition-actor` and the delegate term of `<terms>` in `product-tree:change-standards`. Read the grant from the grant record alone; no mail, Handoff, comment, memory, or another session's word stands in for it.

1. Find the grant record. With Glob, find the `orchestration.toml` files under `${XDG_CONFIG_HOME:-$HOME/.config}/engineering.outcome/<owner>/`, where `<owner>` is the owner of the declared Change Store, and take the one whose `[[products]]` entry names the Change's Product. The grant record is the `orchestration.md` beside it. A missing file, or no such entry, refuses the advance, naming the path read.
2. Read its authorizations. Each level-two heading opens one authorization, which runs to the next level-two heading; its heading names a Position, a Product and rank, a Product, or `Every Position`, and the first non-blank line below it reads `Given: YYYY-MM-DD`.
3. Admit the advance only when an authorization whose heading names the Position this session holds, as the skill it holds that Position through reports it, names that advance, to the target Maturity, for the Change's Product or for every Product of the Change Store that holds the Change. A combined advance to Framed and Sliced needs an authorization that names both advances.
4. Before the advance, read the record body and the Base that stand at the advance, as `github-advance-read` requires of the delegate. The `advance` comment names the delegate's Position in `position`, and the result quotes the admitting authorization's heading and `Given` day.

Refuse the advance, naming the actor `transition-actor` names, for a session that holds no Position, or whose Position no authorization names for that advance.

</delegate_grant>

<result>

Return the issue URL, the Transition or `work`, the readback values verbatim, and, for a Transition, the comment's YAML block. A refusal returns the Transition or `work`, the state or the actor it required, the state found, and no write.

</result>

<failure_modes>

**The assignee stood in for the holding session.** Claude treated the assignee as proof that this session held the Change while a second session of the same account worked in another worktree. One account runs several sessions, so the newest `claim` comment's worktree names the session's place; the assignee alone names only the account.

**A release pushed another Change's branch.** Claude released a Change from a worktree attached to a branch that carried another Change's work, pushed that branch, and named it in the Handoff, so the next holder took the wrong branch. The attached branch is the Change's own work branch only when every commit it holds ahead of the default branch carries this Change's reference; a Change with no work branch of its own takes no push and `branch: none`.

**A partial Transition was repaired by guessing.** Claude's Lifecycle write failed after the comment landed, and Claude re-ran a later step to make the state look complete. Stop at the failed write, report the completed writes and the observed state, and leave the partial state visible.

</failure_modes>

<success_criteria>

- A Transition ran only on a Change in the state its row requires and for the actor `transition-actor` names; every other request was refused with nothing written.
- Each Transition posted exactly one comment, a YAML block with the keys `log-keys` names and only the extra its row admits.
- No write reached a Maturity, Lifecycle, Value, or Investment field whose options differ from the values the standards name.
- The issue carries at most one assignee, and the readback shows every written field at its target and every other field unchanged.
- A `work` ran only on an open Submitted Change, on the direction of the Operator or of a delegate, wrote Lifecycle `Available` alone, kept the assignee, and posted no comment.
- A release pushed only the Change's own work branch, or no branch and `branch: none` for a Change with no work branch of its own, and left the worktree detached; a claim brought the newest Handoff's branch into this worktree.

</success_criteria>
