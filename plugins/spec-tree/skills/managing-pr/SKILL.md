---
name: managing-pr
description: >-
  ALWAYS invoke this skill when managing an open pull request after PR creation — inspecting review and check state, classifying review feedback, posting findings, pushing follow-up commits, or deciding the next PR lifecycle action.
  NEVER use this skill to create a pull request; use opening-pr for PR creation.
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, Skill
---

<objective>

Drive the post-creation pull request loop without treating unstructured review prose as approval, merge authority, or completion. This skill owns the iteration phase: read review state on every relevant surface, classify each item by required receiver action, address BLOCKING and NEEDS-ANSWER items, push follow-up commits, and merge when the validated review/check gates prove no work remains. PR creation, branch hygiene, push semantics, draft lifecycle, heartbeat protocol, and three-surface review inspection are inherited from `/standardizing-merging`. Commits and the closure gate run via `/committing-changes`.

</objective>

<anti_patterns>

Patterns that break this skill's loop. Never:

- Use this skill to create the PR — use `/opening-pr`. The same applies to pushing commits to a branch that has no PR yet.
- Squash or close the PR through this skill — the iteration loop does not own lifecycle termination.
- Promote draft → ready without the four prerequisites in `/standardizing-merging` `<draft_lifecycle>` rule 3 — explicit human instruction, closure gate just run, gate passed, change asserted mergeable.
- Compose commits or commit messages here — use `/committing-changes`.
- Review someone else's PR with this skill — use `/reviewing-pr`.
- Skip the upstream-safety check before a follow-up push. A branch created with `git switch -c <branch> origin/main` sets upstream to `origin/main`; with `push.default=tracking`, a bare `git push` then routes feature-branch commits directly to `origin/main`. Re-run `/standardizing-merging` `<branch_hygiene>` on every push.
- Drive the work queue from severity ranks (`P0`, `P1`, `critical`, `nit`). The four-class receiver-action taxonomy is the only valid label set.
- Create a second heartbeat for the same PR — refresh the existing one per `/standardizing-merging` `<heartbeat>`.
- End the turn with vague handoff prose. Name one of the action tokens from `<workflow>` Step 8.
- Include self-reference in commits, comments, or PR text.

</anti_patterns>

<essential_principles>

- Advisory review comments are normal PR feedback. They are distinct from GitHub approval reviews, merge decisions, and reactions.
- Classify every review item by required receiver action: `BLOCKING`, `NEEDS-ANSWER`, `FOLLOW-UP`, or `NOTE`.
- Drive the work loop only from `BLOCKING` and `NEEDS-ANSWER` items. `FOLLOW-UP` items are tracked in the owning durable location when worth preserving. `NOTE` items create no work.
- A PR may merge only after at least one current-head human or bot review on an inspected surface uses the expected four-class format and leaves no `BLOCKING` or `NEEDS-ANSWER` work.
- Wait at least five minutes after the latest pushed commit before merge evaluation, so review automation has time to respond without shell polling.
- All required checks must be terminal-green before merge. Running, queued, pending, skipped-required, neutral-required, cancelled, timed-out, or failing checks block merge.
- Keep review scope tied to the PR diff plus immediate context needed to judge it.
- Use one-shot inspections per `/standardizing-merging` `<review_inspection>`; never watch CI, poll, or keep a shell process alive while waiting.
- When code changes are required, invoke the relevant coding/testing/spec/prose skill via the Skill tool before editing. This skill coordinates the PR loop; domain skills own implementation quality.

</essential_principles>

<classification>

The four-class receiver-action taxonomy (`BLOCKING` / `NEEDS-ANSWER` / `FOLLOW-UP` / `NOTE`) and the comment-format examples used to express each finding live in `/standardizing-merging` `<review_classification>`. This skill does not re-state them — the same vocabulary is used by reviewers (outgoing feedback) and authors (this skill, triaging incoming feedback) so nothing has to be translated between the two sides.

When triaging incoming review prose into the active PR loop:

- Drive the work queue from `BLOCKING` and `NEEDS-ANSWER` only.
- Track accepted `FOLLOW-UP` items in the owning durable location (`ISSUES.md` / `PLAN.md`).
- Drop `NOTE` items unless the reviewer is asking for an acknowledgment.

Severity-rank labels (`P0`, `critical`, `nit`, etc.) on incoming feedback are converted to one of the four classes before entering the queue — never carried through as the primary label.

</classification>

<merge_gate>

Automatic merge is allowed only when every condition below holds in the same one-shot inspection pass:

- PR state is `OPEN` and `isDraft` is false.
- The inspected head SHA matches the branch head fetched from origin.
- At least five minutes have elapsed since the latest pushed commit on the PR branch.
- At least one current-head review exists from a human or bot reviewer on an inspected surface and uses the expected four-class format: findings are labeled `BLOCKING`, `NEEDS-ANSWER`, `FOLLOW-UP`, or `NOTE`, or the review states in that vocabulary that no merge-blocking work remains.
- Current-head review state has no `BLOCKING` items, no `NEEDS-ANSWER` items, and no unresolved change-request review.
- All required checks in `statusCheckRollup` are complete and successful. Any queued, in-progress, pending, failing, cancelled, timed-out, missing, or ambiguous required check blocks merge.
- Branch hygiene passes, including the upstream-safety check.
- The PR branch has been rebased onto current `origin/<base>` or is already a fast-forward descendant of it.
- The repo-local overlay (`spx/local/merging.md` per `/standardizing-merging` `<repo_local_overlay>`) does not require explicit human merge instruction.

When the gate passes, merge immediately using the project's merge command. The default is rebase merge with remote-branch deletion; the repo-local overlay may specify a different command (e.g., merge commit, squash, or a two-step delete that avoids multi-worktree cleanup failures):

```bash
gh pr merge <pr-number> --rebase --delete-branch
git fetch origin <base>
git switch --detach "origin/<base>"
git status --porcelain
```

If the repo-local overlay requires explicit human merge instruction, do not run `gh pr merge`. End with `AWAIT_MERGE_INSTRUCTION`, surface the gate-pass summary, and wait for the user to authorize the merge.

When the five-minute review window has not elapsed, refresh the heartbeat and report `WAIT_FOR_REVIEW_WINDOW`.

</merge_gate>

<workflow>

**Step 0: Load references.** Invoke `/standardizing-merging` (cross-cutting merge-flow standards) via the Skill tool. Invoke `/committing-changes` via the Skill tool before any commit or push.

**Step 1: Identify the PR.** Resolve the current branch's PR:

```bash
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision
```

**Step 2: Inspect review state on all three surfaces.** Use `/standardizing-merging` `<review_inspection>` — never check only `reviews`. Run the formal-reviews + PR-level-comments query AND the review-thread-comments query, comparing timestamps against the most recent push.

**Step 3: Classify feedback.** Rewrite every actionable item into the four-class model from `/standardizing-merging` `<review_classification>`. Preserve the reviewer evidence: source comment, file path, line, and reason. Use the comment-format shape from `<review_classification>` for each item.

**Step 4: Resolve the action queue.**

- Address `BLOCKING` items first.
- Answer or investigate `NEEDS-ANSWER` items before coding speculative fixes.
- Track accepted `FOLLOW-UP` items in the owning node's `ISSUES.md` or `PLAN.md` when they are worth keeping. Edit those files directly with the `Edit` or `Write` tool — they are committed coordination artifacts, not spec assertions.

**Step 5: Validate focused changes.** Run the narrowest meaningful validation after each fix pass. Before pushing when the PR is approaching ready-for-review or merge consideration, run the project's local closure gate (named in `spx/local/merging.md` if defined) — that gate is the assertion required by `/standardizing-merging` `<draft_lifecycle>` rule 3 before any draft → ready promotion.

**Step 6: Commit and push deliberately.**

- Commit via `/committing-changes` — this skill does not re-implement staging, message format, atomic-commit rules, or version-bump policy.
- Before pushing, re-run the `/standardizing-merging` `<branch_hygiene>` checks. They apply on every push, not only at PR creation. The upstream-safety check in particular catches the `push.default=tracking` failure where feature-branch commits would publish to `origin/main`.
- Push using the explicit-destination-ref form from `/standardizing-merging` `<push_semantics>`.
- For post-ready follow-ups, default to `gh pr ready --undo <pr-number>` before pushing per `/standardizing-merging` `<draft_lifecycle>` rule 4 — unless the project's local rules permit keeping the PR ready when the closure gate has just re-passed.

**Step 7: Re-inspect after push and refresh the heartbeat.** Run the three-surface review inspection again. Refresh the existing PR heartbeat per `/standardizing-merging` `<heartbeat>` instead of creating a second one — one heartbeat per PR.

**Step 8: Merge or report the next repository-governed action.** Evaluate `<merge_gate>` before reporting. If the gate passes, merge using the command specified in `<merge_gate>` (the repo-local overlay's merge command if defined; otherwise the default `gh pr merge <pr-number> --rebase --delete-branch`), fetch the base branch, detach at `origin/<base>`, verify clean status, and end with `POST_MERGE_VERIFY` if the project requires post-merge verification. If the gate does not pass, end with one of these named tokens stated explicitly:

- `WAIT_FOR_CHECKS` — checks still running; heartbeat will re-fire
- `WAIT_FOR_REVIEW` — checks green, awaiting human or bot review
- `WAIT_FOR_REVIEW_WINDOW` — checks and review are present, but five minutes have not elapsed since the latest push
- `FIX_BLOCKING:<item>` — at least one BLOCKING item remains
- `ANSWER_NEEDED:<item>` — at least one NEEDS-ANSWER item remains
- `MARK_READY` — closure gate passed, four prerequisites hold, ready for explicit human promotion
- `MERGE_BLOCKED:<reason>` — merge gate failed for a concrete reason not covered by another token
- `AWAIT_MERGE_INSTRUCTION` — merge gate passed but the repo-local overlay requires explicit human authorization before `gh pr merge`
- `SYNC_BASE` — base branch has advanced; rebase needed before further action
- `POST_MERGE_VERIFY` — PR merged; run post-merge verification per the project's Git workflow

</workflow>

<commands_reference>

```bash
# PR identity
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision

# Three-surface review inspection — see /standardizing-merging <review_inspection>
gh pr view <pr-number> --json reviews,comments \
  --jq '{reviews: [.reviews[] | {author: .author.login, state, submittedAt}],
         comments: [.comments[] | {author: .author.login, createdAt, excerpt: .body[0:160]}]}'
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments \
  --jq '.[] | {author: .user.login, path, line, createdAt: .created_at, excerpt: .body[0:160]}'

# Checks (one-shot — NEVER --watch)
gh pr checks <pr-number>

# Merge only after <merge_gate> passes
gh pr merge <pr-number> --rebase --delete-branch

# Post a PR-level comment (top of the conversation)
gh pr comment <pr-number> --body-file - <<'EOF'
BLOCKING [correctness]: path/to/file.py:42
Evidence: ...
Required before merge: ...
EOF

# Post a formal review comment (counts as a review)
gh pr review <pr-number> --comment --body-file - <<'EOF'
Summary of remaining items:
- 1 BLOCKING ...
- 2 NEEDS-ANSWER ...
EOF

# Reply within an existing review thread (line-level comment)
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments \
  --method POST \
  --field in_reply_to=<review-comment-id> \
  --field body="Acknowledged — fix in next push."

# Mark a review thread as resolved (GraphQL)
gh api graphql --silent \
  -f query='mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }' \
  -F id=<review-thread-node-id>

# Draft / ready transitions — see /standardizing-merging <draft_lifecycle>
gh pr ready <pr-number>          # draft → ready (only with all 4 prerequisites)
gh pr ready --undo <pr-number>   # ready → draft (default before follow-up push)
```

For pre-flight, branch topology, push semantics, draft lifecycle, and heartbeat — see `/standardizing-merging`. For commit selection, message format, and atomic-commit rules — see `/committing-changes`.

</commands_reference>

<success_criteria>

- `/standardizing-merging` and `/committing-changes` are loaded before any inspection or push
- Current PR state has been inspected on all three surfaces (`reviews`, PR-level `comments`, review-thread comments via `gh api .../pulls/<n>/comments`)
- Review feedback is classified only as `BLOCKING`, `NEEDS-ANSWER`, `FOLLOW-UP`, or `NOTE`
- No `P0` / `P1` / `P2` / `P3`, `critical`, `high`, `medium`, `low`, `minor`, or `nit` heading drives the receiver action queue
- Every `BLOCKING` item has a fix plan, a fix commit, or an explicit blocker
- Every `NEEDS-ANSWER` item has an answer, an investigation result, or a direct question for the required human judgment
- Every retained `FOLLOW-UP` item is recorded in the owning durable location (`ISSUES.md` or `PLAN.md`) before the PR loop moves on
- Every push re-runs `/standardizing-merging` `<branch_hygiene>`, including the upstream-safety check
- Automatic merge happens only after `<merge_gate>` passes in the current inspection pass
- A wild or unstructured review never satisfies the required-review condition for merge
- The turn ends with one of the named action tokens from `<workflow>` Step 8 stated explicitly, never with vague handoff prose

</success_criteria>

<failure_modes>

Real failure patterns to avoid:

- **Treating advisory bot prose as approval.** Bot reviewers often post observations as PR-level issue comments with no `state: APPROVED`. The author reads "looks good overall" and ships — missing the BLOCKING item buried later in the same comment. Classify every actionable line, not just the conclusion.
- **Checking only `reviews` and missing comment-surface re-feedback.** After a follow-up push, bot reviewers often re-fire as PR-level issue comments rather than formal reviews. A `gh pr view --json reviews` query returns the prior approval and looks clean; the new comments-surface critique is invisible until merge time. The three-surface inspection in `/standardizing-merging` `<review_inspection>` is the antidote.
- **Skipping the upstream-safety check on follow-up pushes.** A branch created with `git switch -c <branch> origin/main` sets upstream to `origin/main`. With `push.default=tracking`, a bare `git push` then routes feature-branch commits directly to `origin/main`. Re-run `<branch_hygiene>` on every push.
- **Burning expensive CI on guesses.** Promoting draft → ready without the closure gate makes the ready flip a guess. CI then spends the team's budget validating an unverified assertion. The four prerequisites are not optional.
- **Waiting for permission after the merge gate passed.** A green, unblocked, reviewed PR was reported with an extra "what next" prompt, wasting a heartbeat cycle. Once `<merge_gate>` passes, merge immediately; the gate is the merge authority.

</failure_modes>
