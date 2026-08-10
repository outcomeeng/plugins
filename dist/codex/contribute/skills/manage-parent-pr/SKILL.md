---
name: manage-parent-pr
description: >-
  ALWAYS invoke this skill when continuing an open pull request against a repository the operator does not control — answering review, publishing a revision, or reporting its current state.
argument-hint: "[pull request number or URL]"
allowed-tools: Read, Skill, multi_agent_v1.spawn_agent, multi_agent_v1.wait_agent, multi_agent_v1.close_agent, Bash(python3 "${SKILL_DIR}/scripts/resolve_target.py":*), Bash(git remote get-url origin), Bash(gh pr view:*), Bash(gh pr list:*), Bash(gh pr diff:*), Bash(gh pr comment:*), Bash(gh api repos/*/pulls/*/comments:*), Bash(git fetch:*), Bash(git branch --show-current), Bash(git push origin HEAD:refs/heads/*), Bash(mktemp -d), Bash(printf:*)
---

<objective>
The open pull request's current state read once, every valid review finding answered in the head branch, and one comment stating what changed.
</objective>

<workflow>

**Step 1 — Load the standards and resolve the pull request.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

`$ARGUMENTS` is a pull-request number or URL. A bare number is the number; a URL's trailing path segment is the number. Both the URL check and the empty-input lookup need the resolved base, so Step 2 settles them.

**Step 2 — Resolve the target, then the pull request.** Run the resolver named in `/contribution-standards` `<resolution>`. A classification other than `parent-contribution` means this pull request does not belong to this flow; stop and report the classification and `detail` verbatim.

With `base` resolved, settle the number. A URL's `owner/name` segments must equal that `base`; a mismatch stops the flow rather than being reconciled. When `$ARGUMENTS` is empty, look the pull request up for the current branch and stop when none exists:

```bash
gh pr list --repo "<base>" --head "$(git branch --show-current)" --json number
```

**Step 3 — Read current state once.** Substitute the resolved values literally per `/contribution-standards` `<resolution>`:

```bash
gh pr view "<number>" --repo "<base>" --json state,isDraft,reviewDecision,mergeStateStatus,statusCheckRollup,comments,reviews,headRefName,url
```

Read review threads through the API when line-anchored comments matter. Read the state one time — a maintainer answers on their own schedule, and `/contribution-standards` forbids polling, watching, and sleeping on the artifact.

Report `state`, `reviewDecision`, and each required check's conclusion verbatim. `reviewDecision` stays `CHANGES_REQUESTED` until the maintainer looks again; nothing on the contributor's side clears it, and that is not a defect to work around.

**Step 4 — GATE: Verify each finding before fixing it.** Reproduce the finding against the branch and report which findings confirmed. A finding the branch does not exhibit is answered with the evidence rather than with a change.

**Step 5 — Fix, verify, append.** Confirm `origin` resolves to the resolved head per `/contribution-standards` `<resolution>` before the push. Apply every confirmed finding as a defect class: fix the cited site and every parallel instance the same rule reaches. Re-run the base repository's declared checks per `/contribution-standards`. Then append the revision:

```bash
git push origin HEAD:refs/heads/"$(git branch --show-current)"
```

The push updates the open pull request in place and needs no fresh authorization, because it revises the artifact the operator already authorized. NEVER force-push a branch a reviewer has already read.

**Step 6 — GATE: Review the reply, then post it.** Draft the comment per `<reply_shape>` and review it per `/contribution-standards` `<invariants>` "Outward-facing text is permanent" — the prose plugin's `prose-auditor` agent where installed, `<outward_text>` unassisted where not.

```bash
printf '%s\n' '<line>' '<line>' | gh pr comment "<number>" --repo "<base>" --body-file -
```

That comment is the re-request. Requesting a reviewer is a maintainer-side action; `gh pr edit --add-reviewer` fails on a base the operator does not control, and the failure is the expected path.

**Step 7 — Return.** Report the pull-request URL, the state read in Step 3, what changed, and what the maintainer has been asked to look at. Do not wait for the response.

When the maintainer has merged or closed the pull request, report that outcome and stop; a merged contribution needs no further pass.

</workflow>

<reply_shape>

A reply answers the review. Structure it by finding:

- Open with what was confirmed and what was pushed, in one line.
- One section per finding, naming the finding and what changed. Quote the evidence rather than describing it.
- A finding that did not reproduce gets the evidence that shows it did not, not an argument.
- Close with what the maintainer is being asked to look at.

Cut every sentence about the contribution's own process — attempts made, time taken, lessons learned. Never characterize the maintainer's review as right or wrong; report what changed.

</reply_shape>

<constraints>

- MUST read the pull request's state exactly once per invocation and return without waiting.
- MUST verify a finding against the branch before changing code for it.
- MUST name the base repository with `--repo` on every `gh` write.
- NEVER force-push the head branch. The `Bash(git push origin HEAD:refs/heads/*)` grant matches by prefix, so it admits `--force` and `--force-with-lease` too; this constraint is the whole containment for those flags.
- NEVER write through `gh api` — the `Bash(gh api repos/*/pulls/*/comments:*)` grant exists to read review threads, and matching by prefix it also admits `-X DELETE` and `-X PATCH` against a maintainer's comment. Read only.
- NEVER call `gh pr edit --add-reviewer`, `gh pr review`, or any maintainer-side action against a base the operator does not control.
- NEVER treat `reviewDecision: CHANGES_REQUESTED` as a state the contributor can clear.

</constraints>

<failure_modes>

**A structural permission failure was retried.** Claude ran `gh pr edit --add-reviewer` after pushing fixes, read `does not have the correct permissions to execute RequestReviewsByLogin`, and retried it. The call fails on every base the operator does not control. Post the comment stating what changed and stop.

**A finding was fixed without being reproduced.** Claude read a review comment, changed the cited line, and pushed. The finding described a case the branch did not exhibit, so the change answered nothing and added a diff the maintainer had to review. Reproduce first, then fix what confirmed.

</failure_modes>

<success_criteria>

- The resolver returned `parent-contribution` before any write.
- The pull request's state was read once, and `state`, `reviewDecision`, and each required check's conclusion appear verbatim.
- Every confirmed finding is fixed as a defect class; every unconfirmed finding is answered with evidence.
- The base repository's declared checks ran on the revised branch and reported success.
- The revision reached the head branch by appending, never by force-push.
- One comment states what changed, after a prose review, and stands as the re-request.
- The pass returned without polling, watching, or sleeping.

</success_criteria>
