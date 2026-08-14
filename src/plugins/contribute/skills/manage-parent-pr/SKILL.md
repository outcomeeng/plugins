---
name: manage-parent-pr
description: >-
  ALWAYS invoke this skill when continuing an open pull request against a repository the operator does not control — answering review, publishing a revision, or reporting its current state.
  NEVER comment on or push to such a pull request without this skill.
argument-hint: "[pull request number or URL]"
allowed-tools: Read, Skill,{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}},{!% endif %!} Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_target.py":*), Bash(git remote get-url origin), Bash(gh repo view:*), Bash(git status --porcelain), Bash(gh pr view:*), Bash(gh pr list:*), Bash(gh pr comment:*), Bash(gh api repos/*/pulls/*/comments:*), Bash(git fetch:*), Bash(git switch:*), Bash(git rev-list:*), Bash(git branch --show-current), Bash(git add:*), Bash(git commit:*), Bash(git push origin HEAD:refs/heads/*), Bash(printf:*)
---

<objective>
Every valid review finding answered in the head branch, and — when any finding needed a disposition — one comment on the open pull request stating what changed.
</objective>

<workflow>

**Step 1 — Load the standards and resolve the pull request.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

`$ARGUMENTS` is a pull-request number or URL. A bare number is the number; a URL's trailing path segment is the number. Both the URL check and the empty-input lookup need the resolved base, so Step 2 settles them.

**Step 2 — Resolve the target, then the pull request.** Run the resolver named in `/contribution-standards` `<resolution>`. A classification other than `parent-contribution` means this pull request does not belong to this flow; stop and report the classification and `detail` verbatim.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_target.py"
```

With `base` resolved, settle the number. A URL's `owner/name` segments must equal that `base`; a mismatch stops the flow rather than being reconciled. When `$ARGUMENTS` is empty, look the pull request up for the current branch and stop when none exists:

```bash
gh pr list --repo "<base>" --head "$(git branch --show-current)" --json number,headRefName,headRepository,headRepositoryOwner
```

`--head` filters by branch name only — `gh` does not accept `<owner>:<branch>` there — so two forks carrying the same branch name both match. Select the entry whose `headRepositoryOwner` and `headRepository` equal the resolved `head`, and stop when none does rather than taking the first.

**Step 3 — Read current state once.** Substitute the resolved values literally per `/contribution-standards` `<resolution>`:

```bash
gh pr view "<number>" --repo "<base>" --json state,isDraft,reviewDecision,mergeStateStatus,statusCheckRollup,comments,reviews,headRefName,headRepository,headRepositoryOwner,url
```

Read review threads through the API when line-anchored comments matter, because `gh pr view` carries the PR-level conversation and not the comments tied to a file and line:

```bash
gh api repos/"<base>"/pulls/"<number>"/comments --paginate --jq '.[] | {path, line, body}'
```

Read the state one time — a maintainer answers on their own schedule, and `/contribution-standards` forbids polling, watching, and sleeping on the artifact.

Report `state`, `reviewDecision`, and each required check's conclusion verbatim. `reviewDecision` stays `CHANGES_REQUESTED` until the maintainer looks again; nothing on the contributor's side clears it, and that is not a defect to work around.

**STOP when `state` is `CLOSED` or `MERGED`.** Report that outcome and return. This gate precedes every later step, because a management pass on a finished pull request would otherwise fix findings, push, and post a reply to a thread nobody is going to act on.

**STOP when `headRepositoryOwner`/`headRepository` do not equal the resolved `head`.** A number or URL names a pull request from any fork, and Step 5 pushes this checkout's `HEAD`; without this check a fix reaches an unrelated fork's branch while the reply claims this pull request was revised.

When they do match, check out `headRefName` before editing, so the branch being fixed is the branch the pull request carries. That fetch reads through `origin`, so verify `origin` first per `/contribution-standards` `<resolution>` "Verify `origin` before pushing or fetching through it" — a remote name is a local label, and an `origin` pointing elsewhere fetches a same-named branch from an unrelated repository:

```bash
gh repo view "$(git remote get-url origin)" --json nameWithOwner --jq '.nameWithOwner'
```

**STOP when that does not equal the resolved `head`.**

Two conditions must hold before the branch moves. The checkout must carry no uncommitted work, because the reset below takes those edits onto the pull request's branch, where Step 4 reproduces findings against them and Step 5 can commit one that overlaps a fixed path:

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

`-C` is required. Plain `git switch` selects an existing local branch without moving it, so a branch left behind from an earlier pass verifies Step 4's findings against stale code and Step 5's push is rejected as non-fast-forward. An invocation already sitting on that branch still runs this, because Step 5 pushes `HEAD`.

**Step 4 — GATE: Verify each finding before fixing it.** Reproduce the finding against the branch and report which findings confirmed. A finding the branch does not exhibit is answered with the evidence rather than with a change.

**Step 5 — Fix, commit, verify, append.** Apply every confirmed finding as a defect class: fix the cited site and every parallel instance the same rule reaches. Re-run the base repository's declared checks per `/contribution-standards`. Editing those files and running those checks are both discovered work rather than commands this skill can name, so they proceed per `/contribution-standards` `<capability_scope>`.

**When no finding produced a change, skip to Step 6.** A pass where every finding failed reproduction, and a pass invoked only to report the pull request's state, both reach this step with nothing to commit. `git commit` with no staged change exits non-zero, which would strand the evidence Step 6 owes the maintainer for the findings that did not reproduce. There is nothing to push either — the pull request already carries what it carried.

Commit the fixes before pushing. A push transfers commits, so an uncommitted fix leaves the pull request exactly as the maintainer left it while Step 6 posts a reply announcing a revision that is not there:

```bash
git add <fixed-paths>
git commit -m "<message in the base repository's commit style>"
git push origin HEAD:refs/heads/"$(git branch --show-current)"
```

`git commit` takes its message on the command line. Bare `git commit` opens an editor, and no step here runs on a terminal that can answer one.

Confirm the pull request carries the pushed commit before continuing to Step 6. `git commit` reported the new commit and `git push` reports the ref update it performed; `Everything up-to-date` means it moved nothing. Then read what the pull request itself now points at:

```bash
gh pr view "<number>" --repo "<base>" --json headRefOid --jq '.headRefOid'
```

Stop when it does not equal the commit just pushed. Step 6 would otherwise announce a revision the pull request does not carry.

The push updates the open pull request in place and needs no fresh authorization, because it revises the artifact the operator already authorized. NEVER force-push a branch a reviewer has already read.

**Step 6 — GATE: Review the reply, then post it.** A reply answers a review. An invocation that reports the pull request's current state, and the immediate handoff `/open-parent-pr` performs on a pull request nobody has reviewed yet, both reach this step with no finding to give a disposition to — they return after Step 7 without commenting, because a comment saying nothing notifies every watcher of a repository the operator does not control.

With findings to answer, draft the comment per `<reply_shape>` and review it per `/contribution-standards` `<invariants>` "Outward-facing text is permanent" — the prose plugin's `prose-auditor` agent where installed, `<outward_text>` unassisted where not.

```bash
printf '%s\n' '<line>' '<line>' | gh pr comment "<number>" --repo "<base>" --body-file -
```

That comment is the re-request. Requesting a reviewer is a maintainer-side action; `gh pr edit --add-reviewer` fails on a base the operator does not control, and the failure is the expected path.

**Step 7 — Return.** Report the pull-request URL, the state read in Step 3, what changed, and what the maintainer has been asked to look at — or, on a pass with no finding to answer, that nothing needed a reply. Do not wait for the response.

</workflow>

<reply_shape>

A reply answers the review. Structure it by finding:

- Open with what was confirmed and, when a fix was pushed, what was pushed, in one line. A pass that changed nothing says what it verified, and claims no revision.
- One section per finding, naming the finding and what changed. Quote the evidence rather than describing it.
- A finding that did not reproduce gets the evidence that shows it did not, not an argument.
- Close with what the maintainer is being asked to look at.

Cut every sentence about the contribution's own process — attempts made, time taken, lessons learned. Never characterize the maintainer's review as right or wrong; report what changed.

</reply_shape>

<constraints>

- MUST read the pull request's state exactly once per invocation and return without waiting.
- MUST verify a finding against the branch before changing code for it.
- MUST confirm `origin` resolves to the resolved head before the Step 3 fetch, not only before the Step 5 push. The fetch reads through `origin` too, and the reset that follows it moves the branch to whatever that fetch returned.
- MUST require a clean working tree before the Step 3 reset, and commit nothing the operator left in progress.
- NEVER commit or push when no confirmed finding produced a change; Step 6 still owes the maintainer the evidence for what did not reproduce.
- NEVER post a comment when the pass had no finding to answer at all — a state-only invocation, or a handoff on a pull request nobody has reviewed yet, returns what it read and writes nothing.
- MUST name the base repository with `--repo` on every `gh` write.
- NEVER force-push the head branch. The `Bash(git push origin HEAD:refs/heads/*)` grant matches by prefix, so it admits `--force` and `--force-with-lease` too; this constraint is the whole containment for those flags.
- NEVER pass `--force` or `--discard-changes` to `git switch`. The `Bash(git switch:*)` grant matches by prefix and admits both, and either one drops uncommitted work in the invocation checkout. `-C` moves the branch pointer and is required by Step 3; neither of those flags is.
- NEVER run the `-C` reset before the commit count proves the local branch carries nothing the fetched tip lacks. `-C` moves the branch to `FETCH_HEAD`, so a local commit the pull request has not seen is lost without that check.
- NEVER stage by wildcard. The `Bash(git add:*)` grant matches by prefix, so it admits `-A` and `.`, either of which sweeps unrelated work in the invocation checkout into a commit destined for someone else's repository. Name the fixed paths.
- NEVER pass `--no-verify` to `git commit`. The `Bash(git commit:*)` grant matches by prefix and admits it. Hooks run from this checkout's own configuration, which conforming to the base repository's conventions is what installs, so skipping them drops part of the verification `/contribution-standards` requires. No hook being configured right now is not a reason to pass the flag.
- NEVER write through `gh api` — the `Bash(gh api repos/*/pulls/*/comments:*)` grant exists to read review threads, and matching by prefix it also admits `-X DELETE` and `-X PATCH` against a maintainer's comment. Read only.
- NEVER pass `--edit-last` or `--delete-last` to `gh pr comment`. The `Bash(gh pr comment:*)` grant matches by prefix and admits both, and either one rewrites or removes a comment a reviewer may already have read. `/contribution-standards` `<invariants>` "Iterate by appending" is the rule; this constraint is its containment here.
- NEVER call `gh pr edit --add-reviewer`, `gh pr review`, or any maintainer-side action against a base the operator does not control.
- NEVER treat `reviewDecision: CHANGES_REQUESTED` as a state the contributor can clear.

</constraints>

<failure_modes>

**A structural permission failure was retried.** Claude ran `gh pr edit --add-reviewer` after pushing fixes, read `does not have the correct permissions to execute RequestReviewsByLogin`, and retried it. The call fails on every base the operator does not control. Post the comment stating what changed and stop.

**A gate was described before it existed.** Step 3 told the pass that `origin` had been "confirmed above" and fetched the pull request's head branch through it. The confirmation sat in Step 5, two steps later — so the fetch, and the reset that moved the branch to whatever it returned, both ran on an unverified remote label. Place a gate before the command it protects, and state it there rather than asserting elsewhere that it already happened.

**A finding was fixed without being reproduced.** Claude read a review comment, changed the cited line, and pushed. The finding described a case the branch did not exhibit, so the change answered nothing and added a diff the maintainer had to review. Reproduce first, then fix what confirmed.

</failure_modes>

<success_criteria>

- The resolver returned `parent-contribution` before any write.
- The pull request's state was read once, and `state`, `reviewDecision`, and each required check's conclusion appear verbatim.
- Every confirmed finding is fixed as a defect class, and the Step 6 comment carries one disposition per finding Step 4 read — what changed for a confirmed one, the evidence for an unconfirmed one — so re-reading the posted comment against the review accounts for every finding.
- The base repository's declared checks ran on the revised branch and reported success.
- `origin` was confirmed to be the resolved head and the working tree was clean before the head branch was reset to the fetched tip.
- A revision reached the head branch by appending, never by force-push, and the pull request's `headRefOid` equals the commit that was pushed; a pass that changed nothing committed and pushed nothing.
- A pass carrying findings posted one comment, after a prose review, stating what changed and standing as the re-request; a pass with no finding to answer posted none.
- The pass returned without polling, watching, or sleeping.

</success_criteria>
