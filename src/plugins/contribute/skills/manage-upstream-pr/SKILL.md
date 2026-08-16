---
name: manage-upstream-pr
description: >-
  ALWAYS invoke this skill when continuing an open pull request against a repository the operator does not control — answering review, publishing a revision, or reporting its current state.
  NEVER comment on or push to such a pull request without this skill.
argument-hint: "[pull request number or URL]"
allowed-tools: Read, Skill,{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}},{!% endif %!} {{! tool('ask_user') !}}, Bash(git remote get-url origin), Bash(gh repo view:*), Bash(git status --porcelain), Bash(gh pr view:*), Bash(gh pr list:*), Bash(gh pr comment:*), Bash(gh api repos/*/pulls/*/comments:*), Bash(gh api user:*), Bash(git fetch:*), Bash(git switch:*), Bash(git rev-list:*), Bash(git branch --show-current), Bash(git add:*), Bash(git commit:*), Bash(git push origin HEAD:refs/heads/*), Bash(printf:*)
---

<objective>
Every valid review finding answered in the head branch, and — when any finding needed a disposition — one comment on the open pull request stating what changed.
</objective>

<workflow>

**Step 1 — Load the standards and resolve the pull request.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

`$ARGUMENTS` is a pull-request number or URL. A bare number is the number; a URL's trailing path segment is the number. Both the URL check and the empty-input lookup need the resolved base, so Step 2 settles them.

**Step 2 — Establish the target, then the pull request.** Read the live `<UPSTREAM_TARGET>` marker; invoke `/upstream` when none is live. A classification other than `upstream-contribution` means this pull request does not belong to this flow; stop and report the classification and `detail` verbatim.

With `base` resolved, settle the number. A URL's `owner/name` segments must equal that `base`; a mismatch stops the flow rather than being reconciled. When `$ARGUMENTS` is empty, look the pull request up for the current branch and stop when none exists:

```bash
gh pr list --repo "<base>" --head "$(git branch --show-current)" --json number,headRefName,headRepository,headRepositoryOwner
```

`--head` filters by branch name only — `gh` does not accept `<owner>:<branch>` there — so two forks carrying the same branch name both match. Select the entry whose `headRepositoryOwner` and `headRepository` equal the resolved `head`, and stop when none does rather than taking the first.

**Step 3 — Read current state once.** Substitute the resolved values literally per `/contribution-standards` `<resolution>`:

```bash
gh pr view "<number>" --repo "<base>" --json state,isDraft,reviewDecision,mergeStateStatus,statusCheckRollup,comments,reviews,author,title,headRefName,headRepository,headRepositoryOwner,url
```

`author` and `title` are read here because Step 4 gates on them, and this is the one read of the pull request this pass performs.

Read review threads through the API when line-anchored comments matter, because `gh pr view` carries the PR-level conversation and not the comments tied to a file and line:

```bash
gh api repos/"<base>"/pulls/"<number>"/comments --paginate --jq '.[] | {user: .user.login, in_reply_to_id, path, line, body}'
```

That endpoint returns every line-anchored comment on the pull request, not only a reviewer's. Keeping `user` and `in_reply_to_id` is what separates the three kinds it mixes: a maintainer's finding, a reply this flow posted on an earlier pass, and a line comment from anyone else. Dropping them leaves Step 5 rereading its own answers as new findings and re-fixing what it already fixed, pass after pass, on a repository the operator does not control. Read the authenticated login, which is the side of that comparison the pull request does not supply — Step 4 gates on it too, and this is the read both use:

```bash
gh api user --jq '.login'
```

Take as findings the comments carrying no `in_reply_to_id` from a login other than that one, and read the rest as the thread around them.

Read the state one time — a maintainer answers on their own schedule, and `/contribution-standards` forbids polling, watching, and sleeping on the artifact.

Report `state`, `reviewDecision`, and each required check's conclusion verbatim. `reviewDecision` stays `CHANGES_REQUESTED` until the maintainer looks again; nothing on the contributor's side clears it, and that is not a defect to work around.

**STOP when `state` is `CLOSED` or `MERGED`.** Report that outcome and return. This gate precedes every later step, because a management pass on a finished pull request would otherwise fix findings, push, and post a reply to a thread nobody is going to act on.

**STOP when `headRepositoryOwner`/`headRepository` do not equal the resolved `head`.** A number or URL names a pull request from any fork, and Step 6 pushes this checkout's `HEAD`; without this check a fix reaches an unrelated fork's branch while the reply claims this pull request was revised.

**STOP when there is no finding to verify.** A state-only invocation, and the immediate handoff `/open-upstream-pr` performs on a pull request nobody has reviewed yet, both end here: report what Step 3 read and return. Every command from Step 4 onward moves this checkout's branch or writes to the base repository, and neither is something a request to read state asked for.

**Step 4 — GATE: Establish that this artifact is the operator's, then take its branch.** Compare `author.login` from the Step 3 read against the login that read reported; those two fields are the whole comparison.

A pull request the operator opened is the artifact they already authorized, and a revision continues it. One anyone else opened — a collaborator on the same organization fork reaches this flow through an explicit number or URL, and the head-repository check above passes for them — is an unrelated artifact: `/contribution-standards` `<invariants>` "Authorization covers the artifact and its revisions" gives it its own in-turn authorization, so present through the runtime's structured-question tool the resolved `base`, the pull-request number and title, its author, and the choice to revise it or to stop. Take no branch and write nothing until the operator authorizes it in this turn.

This gate precedes the checkout below, and not only Step 6's push. The checkout resets a local branch, and a reset performed for someone else's pull request is already a change to the operator's own worktree.

With that settled, check out `headRefName`, so the branch being fixed is the branch the pull request carries. That fetch reads through `origin`, so verify `origin` first per `/contribution-standards` `<resolution>` "Verify `origin` before pushing or fetching through it" — a remote name is a local label, and an `origin` pointing elsewhere fetches a same-named branch from an unrelated repository:

```bash
gh repo view "$(git remote get-url origin)" --json nameWithOwner --jq '.nameWithOwner'
```

**STOP when that does not equal the resolved `head`.**

Two conditions must hold before the branch moves. The checkout must carry no uncommitted work, because the reset below takes those edits onto the pull request's branch, where Step 5 reproduces findings against them and Step 6 can commit one that overlaps a fixed path:

```bash
git status --porcelain
git fetch origin "<headRefName>"
git rev-list --count FETCH_HEAD..refs/heads/"<headRefName>"
```

**STOP when `git status --porcelain` prints anything.** Report the paths; committing or setting aside someone's in-progress work is theirs to decide, not this flow's.

The third command runs only when that branch already exists locally, and its count is the commits the local branch carries that the fetched pull-request tip does not. **STOP when the count is not zero**: those commits are work the pull request has never seen, and the next command discards them.

With a clean tree and nothing unpushed to lose, base the branch on the fetched tip:

```bash
git switch -C "<headRefName>" FETCH_HEAD
```

`-C` is required. Plain `git switch` selects an existing local branch without moving it, so a branch left behind from an earlier pass verifies Step 5's findings against stale code and Step 6's push is rejected as non-fast-forward. An invocation already sitting on that branch still runs this, because Step 6 pushes `HEAD`.

**Step 5 — GATE: Verify each finding before fixing it.** Reproduce the finding against the branch and report which findings confirmed. A finding the branch does not exhibit is answered with the evidence rather than with a change.

**Step 6 — Fix, commit, verify, append.** Apply every confirmed finding as a defect class: fix the cited site and every parallel instance the same rule reaches. Re-run the base repository's declared checks per `/contribution-standards`. Editing those files and running those checks are both discovered work rather than commands this skill can name, so they proceed per `/contribution-standards` `<capability_scope>`.

**When no finding produced a change, skip to Step 7.** A pass where every finding failed reproduction reaches this step with nothing to commit. `git commit` with no staged change exits non-zero, which would strand the evidence Step 7 owes the maintainer for the findings that did not reproduce. There is nothing to push either — the pull request already carries what it carried.

Commit the fixes before pushing. A push transfers commits, so an uncommitted fix leaves the pull request exactly as the maintainer left it while Step 7 posts a reply announcing a revision that is not there:

```bash
git add <fixed-paths>
git commit -m "<message in the base repository's commit style>"
git push origin HEAD:refs/heads/"$(git branch --show-current)"
```

`git commit` takes its message on the command line. Bare `git commit` opens an editor, and no step here runs on a terminal that can answer one.

Confirm the pull request carries the pushed commit before continuing to Step 7. `git commit` reported the new commit and `git push` reports the ref update it performed; `Everything up-to-date` means it moved nothing. Then read what the pull request itself now points at:

```bash
gh pr view "<number>" --repo "<base>" --json headRefOid --jq '.headRefOid'
```

Stop when it does not equal the commit just pushed. Step 7 would otherwise announce a revision the pull request does not carry.

The push updates the open pull request in place and needs no fresh authorization beyond Step 4's, because it revises the artifact that gate established as the operator's. NEVER force-push a branch a reviewer has already read.

**Step 7 — GATE: Review the reply, then post it.** A reply answers a review. A pass where every finding failed reproduction still reaches this step with a disposition to give, because the maintainer is owed the evidence for what did not reproduce.

With findings to answer, draft the comment per `<reply_shape>` and review it per `/contribution-standards` `<invariants>` "Outward-facing text is permanent" — the prose plugin's `prose-auditor` thin agent where installed, `<outward_text>` unassisted where not.

```bash
printf '%s\n' '<line>' '<line>' | gh pr comment "<number>" --repo "<base>" --body-file -
```

That comment is the re-request. Requesting a reviewer is a maintainer-side action; `gh pr edit --add-reviewer` fails on a base the operator does not control, and the failure is the expected path.

**Step 8 — Return.** Report the pull-request URL, the state read in Step 3, what changed, and what the maintainer has been asked to look at — or, on a pass Step 3 ended for having no finding to verify, what it read and that nothing needed a reply. Do not wait for the response.

</workflow>

<reply_shape>

A reply answers the review. Structure it by finding:

- Open with what was confirmed and, when a fix was pushed, what was pushed, in one line. A pass that changed nothing says what it verified, and claims no revision.
- One section per finding, naming the finding and what changed. Quote the evidence rather than describing it.
- A finding that did not reproduce gets the evidence that shows it did not, not an argument.
- Close with what the maintainer is being asked to look at.

Cut every sentence about the contribution's own process — attempts made, time taken, lessons learned. Never characterize the maintainer's review as right or wrong; report what changed.

</reply_shape>

<worked_example>

One reply on a fictional `acme/parser` pull request that makes the config file yield to `--strict`, to compare a draft against. Two line-anchored findings arrived, one confirmed and one did not:

```text
src/config.py:88  This still reads the flag before the file — same bug one level up.
src/cli.py:12     --strict needs to be in the help text.
```

The reply:

```text
Confirmed the precedence finding and pushed 9e1b330. The help-text finding did
not reproduce.

**src/config.py:88 — flag read before file.** Confirmed. `merge_options` read
`args.strict` ahead of `file_opts`, and `merge_flags` at src/config.py:141 had
the same order. Both read the file first now:

$ printf 'strict: false\n' > parser.yml
$ parser --strict sample.txt; echo "exit $?"
sample.txt:1:5: unexpected '='
exit 1

**src/cli.py:12 — --strict missing from help text.** Did not reproduce on this
branch:

$ parser --help | grep -- --strict
  --strict              Fail on any parse error

That line landed in 4f9c2a1, which this branch is based on.

Ready for another look at src/config.py.
```

The opening line states what was confirmed and what was pushed, in that order, and claims one commit rather than "the fixes". The confirmed finding names the parallel instance at `src/config.py:141` that the same rule reached, because Step 6 fixes a finding as a defect class rather than at its cited line. The unconfirmed finding receives the command output that shows it did not reproduce, with no argument about whether the reviewer misread. The close names one file for the maintainer to look at.

</worked_example>

<constraints>

- MUST read the pull request's state exactly once per invocation and return without waiting.
- NEVER fix, commit, push, or comment when `state` is `CLOSED` or `MERGED`. Report that outcome and return; nobody is going to act on a reply to a finished pull request.
- NEVER move the branch or push when `headRepositoryOwner`/`headRepository` do not equal the resolved `head`. A number or URL names a pull request from any fork, and Step 6 pushes this checkout's `HEAD`.
- MUST end the pass at Step 3 when it has no finding to verify. Every command from Step 4 onward moves this checkout's branch or writes to the base repository, and a state-only invocation asked for neither.
- MUST compare the pull request's `author.login` against the authenticated login before Step 4's checkout, and obtain authorization in the same turn for one the operator did not open. The head-repository check passes for every collaborator on that fork, so it is not evidence the artifact is the operator's.
- MUST verify a finding against the branch before changing code for it.
- MUST confirm `origin` resolves to the resolved head before the Step 4 fetch, not only before the Step 6 push. The fetch reads through `origin` too, and the reset that follows it moves the branch to whatever that fetch returned.
- MUST require a clean working tree before the Step 4 reset, and commit nothing the operator left in progress.
- NEVER commit or push when no confirmed finding produced a change; Step 7 still owes the maintainer the evidence for what did not reproduce.
- NEVER post a comment when the pass had no finding to answer at all — a state-only invocation, or a handoff on a pull request nobody has reviewed yet, returns what Step 3 read and writes nothing.
- MUST name the base repository with `--repo` on every `gh` write.
- NEVER force-push the head branch. The `Bash(git push origin HEAD:refs/heads/*)` grant matches by prefix, so it admits `--force` and `--force-with-lease` too; this constraint is the whole containment for those flags.
- NEVER pass `--force` or `--discard-changes` to `git switch`. The `Bash(git switch:*)` grant matches by prefix and admits both, and either one drops uncommitted work in the invocation checkout. `-C` moves the branch pointer and is required by Step 4; neither of those flags is.
- NEVER run the `-C` reset before the commit count proves the local branch carries nothing the fetched tip lacks. `-C` moves the branch to `FETCH_HEAD`, so a local commit the pull request has not seen is lost without that check.
- NEVER stage by wildcard. The `Bash(git add:*)` grant matches by prefix, so it admits `-A` and `.`, either of which sweeps unrelated work in the invocation checkout into a commit destined for someone else's repository. Name the fixed paths.
- NEVER pass `--no-verify` to `git commit`. The `Bash(git commit:*)` grant matches by prefix and admits it. Hooks run from this checkout's own configuration, which conforming to the base repository's conventions is what installs, so skipping them drops part of the verification `/contribution-standards` requires. No hook being configured right now is not a reason to pass the flag.
- MUST keep `user` and `in_reply_to_id` in the review-thread projection, and select findings from them. A projection that drops either one cannot tell a maintainer's finding from a reply this flow already posted, so Step 5 re-fixes what it fixed on the previous pass.
- MUST read `gh api user` only for the reply-selection and Step 4 authorship comparisons. `/contribution-standards` `<invariants>` "Establish permission from the API" rules the authenticated account out as evidence of permission on the base; it is evidence of identity and nothing else.
- NEVER write through `gh api` — the `Bash(gh api repos/*/pulls/*/comments:*)` and `Bash(gh api user:*)` grants exist to read review threads and the authenticated login, and matching by prefix they also admit `-X DELETE` and `-X PATCH` against a maintainer's comment and against the operator's own GitHub account. Read only.
- NEVER pass `--edit-last` or `--delete-last` to `gh pr comment`. The `Bash(gh pr comment:*)` grant matches by prefix and admits both, and either one rewrites or removes a comment a reviewer may already have read. `/contribution-standards` `<invariants>` "Iterate by appending" is the rule; this constraint is its containment here.
- NEVER call `gh pr edit --add-reviewer`, `gh pr review`, or any maintainer-side action against a base the operator does not control.
- NEVER treat `reviewDecision: CHANGES_REQUESTED` as a state the contributor can clear.

</constraints>

<failure_modes>

**A structural permission failure was retried.** Claude ran `gh pr edit --add-reviewer` after pushing fixes, read `does not have the correct permissions to execute RequestReviewsByLogin`, and retried it. The call fails on every base the operator does not control. Post the comment stating what changed and stop.

**A gate was described before it existed.** Step 3 told the pass that `origin` had been "confirmed above" and fetched the pull request's head branch through it. The confirmation sat two steps later — so the fetch, and the reset that moved the branch to whatever it returned, both ran on an unverified remote label. Place a gate before the command it protects, and state it there rather than asserting elsewhere that it already happened.

**A request to read state moved the operator's branch.** The checkout of the pull request's head branch sat inside the state read, so an invocation asking only what the pull request currently says fetched, reset a local branch to the fetched tip, and left the checkout on it. Nothing was written to the base repository and the pass still looked successful. Read state, then end the pass before the first command that moves the branch when there is no finding to verify.

**A finding was fixed without being reproduced.** Claude read a review comment, changed the cited line, and pushed. The finding described a case the branch did not exhibit, so the change answered nothing and added a diff the maintainer had to review. Reproduce first, then fix what confirmed.

</failure_modes>

<success_criteria>

- The `<UPSTREAM_TARGET>` marker read for this pass carries `upstream-contribution`, established before any write.
- The pull request's state was read once, and `state`, `reviewDecision`, and each required check's conclusion appear verbatim.
- A `state` of `CLOSED` or `MERGED`, a head repository other than the resolved `head`, and a pass with no finding to verify each returned what Step 3 read, left this checkout's branch where it was, and wrote nothing; every criterion below covers a pass that continued.
- The pull request's `author.login` was compared against the authenticated login before the branch moved, and one the operator did not open was authorized in that turn.
- The review-thread read kept each comment's author and reply parent, and the findings it selected exclude every reply this flow posted on an earlier pass.
- Every confirmed finding is fixed as a defect class, and the Step 7 comment carries one disposition per finding Step 5 verified — what changed for a confirmed one, the evidence for an unconfirmed one — so re-reading the posted comment against the review accounts for every finding.
- The base repository's declared checks ran on the revised branch and reported success.
- `origin` was confirmed to be the resolved head and the working tree was clean before the head branch was reset to the fetched tip.
- A revision reached the head branch by appending, never by force-push, and the pull request's `headRefOid` equals the commit that was pushed; a pass that changed nothing committed and pushed nothing.
- A pass carrying findings posted one comment, after a prose review, stating what changed and standing as the re-request; a pass with no finding to answer posted none.
- The pass returned without polling, watching, or sleeping.

</success_criteria>
