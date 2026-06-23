---
name: manage-pr
description: >-
  Open-PR management protocol for review and check inspection, follow-up pushes, merge gates, and post-merge cleanup. Loaded by /manage-github-pr.
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, Skill
---

<objective>
The pull request merged into the base branch on origin, or a terminal action token naming the gate condition that withholds the merge.
</objective>

<the_managing_flow>

Walk these steps on each management pass. Routine steps — inspect, classify, rebase, re-review, push, and foreground PR-check wait — run directly. The only pauses are the autonomous merge (under `MERGE_READINESS ∧ PRODUCTION_READINESS`) and the action-token emissions when a gate withholds.

**Step 0 — Load references.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke /understand first. Then invoke /merging-standards (shared vocabulary) and /commit-changes (commit format for any follow-up commits) via the Skill tool.

**Step 1 — Identify the PR.**

```bash
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,comments
```

**Step 2 — Inspect three surfaces and check base drift.** Run /merging-standards `<review_inspection>` queries. Compare timestamps against the most recent push; entries after that push are re-reviews of the latest state. In the same checkpoint, fetch `origin/<base>` and determine whether the branch is behind it — review state and base drift are read together so the rebase can proceed during the wait for reviews, not only after they land.

**Step 3 — Classify every finding.** Apply the two-severity / six-category taxonomy from /merging-standards `<review_classification>`. Convert any severity-rank labels (`P0`, `critical`, `nit`), the removed `FOLLOW-UP` severity, or legacy class labels (`NEEDS-ANSWER`, `NOTE`) on incoming feedback to one of the two severities before queuing — reframe open questions as findings and omit commentary that does not constitute a finding.

**Step 4 — Sync to base.** If Step 2 found the branch behind `origin/<base>`, rebase per /merging-standards `<base_sync>` now — independent of whether a review has landed and independent of whether any landed review carries findings. A branch behind base is superseded before it can merge, so rebasing immediately aims CI and reviewers at the head that will actually merge and surfaces a nasty rebase early. An unresolvable conflict emits `SYNC_BASE` and ends the pass; a `dirty_tree` outcome is committed through `/commit-changes` then re-synced per `<base_sync>`, never surfaced as `SYNC_BASE`. Otherwise Step 6 re-establishes `REVIEW_READINESS` against the rebased tree — scoped by the `/sync-base` `preservation` proof per `<base_sync>`, so an unrelated base movement does not force a full re-run — and pushes it with `--force-with-lease`.

**Step 5 — Drive the queue.** Process every current-head finding by validity and phase per /merging-standards `<review_classification>`, never by severity. First build one current-head finding ledger from all inspected surfaces, classify each item once as valid in-scope, unbacked, or genuinely separate/larger. Validate each finding against its cited rule and the governing decisions; drop any the citation does not support. For every valid finding, perform the same-class sweep required by /merging-standards `<review_classification>` across the touched node(s) before editing. This is the PR-open phase: **fix every valid in-scope finding and every in-scope parallel instance** the sweep surfaces (fix them, commit via /commit-changes) — there is no deferral of in-scope work on the open PR. Validity and scope (never the severity label) decide. A bounded fix — a rename propagation, a cross-reference update, a mechanical change, or a fix that merely touches another file — is in-scope work the changeset carries and is fixed here, never deferred. A valid `DEBT` finding whose fix the author judges a genuinely separate, larger concern — its own node or feature, outside this PR's diff — is recorded in the owning node's `ISSUES.md` or `PLAN.md` via the Edit or Write tool (those are committed coordination artifacts) with a reason naming why it is large and does not block the merge; a valid in-scope finding about the shipped diff is fixed, not recorded.

**Step 6 — Re-establish `REVIEW_READINESS`, then push follow-ups deliberately.** A Step 5 fix or a Step 4 rebase changed the diff, so before any push re-establish both `REVIEW_READINESS` predicates **on the exact tree the push would publish**. Both predicates must hold *together* on that final tree — they iterate to a joint fixpoint, not a one-time linear pass:

1. **Deterministic verification.** Run the project's local deterministic verification per /merging-standards `<local_deterministic_scope>` — validation and testing for the touched scope, escalating only when the overlay or risk evidence requires a wider local run. Redirect verbose command output to a temporary log path and inspect only the exit status, summary, and failing sections. One scoping exception: when this push follows **only** a base-sync rebase with no Step 5 content fix, scope this command to the lane the `/sync-base` `preservation` proof and the project overlay select per `<base_sync>`.
2. **Local review at parity.** Run the local review to convergence per /merging-standards `<local_review_invocation>` — the `changes-reviewer` agent (or `/review-changes`), which resolves its own scope (the worktree it runs in and the diff), adding no interpretive scope, no severity pre-filter, and no instruction on what to emphasize. This re-applies to the new diff the same author-side gate /open-pr ran before the opening push; act on its findings by validity and phase per /merging-standards `<review_classification>`, committing fixes via /commit-changes. The local review before this push parallels the CI review that fires after it — same class of gate, opposite sides of the push. One reuse exception: when this push follows **only** a base-sync rebase with no content change — no Step 5 fix and no fix from sub-step 1 above — reuse the converged verdict if the `/sync-base` `preservation` proof and the overlay's governance-surface list permit it per `<base_sync>`. Any content fix, in Step 5 or in sub-step 1, re-runs the review on the new diff.

**Any fix in either sub-step mutates the tree, so loop:** a deterministic-verification fix is a new diff the local review has not seen, and a review-driven fix is a new tree deterministic verification has not covered. Re-run both predicates after every commit until a single tree passes deterministic verification *and* carries no unaddressed valid finding — that converged tree is what Step 6 pushes. Never push a tree on which the later-fixed predicate was established before the last commit.

Then re-run /merging-standards `<branch_hygiene>` before the push — hygiene applies on every push, not only at creation. Push via /merging-standards `<push_semantics>`; a pass that rebased in Step 4 pushes with the `--force-with-lease` form. The PR is ready throughout — a follow-up push goes to the ready PR and re-fires CI; there is no draft toggle.

**Step 7 — PR-check wait command.** Step 8 invokes this step when it emits `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, or `MENTION_REVIEW_NEEDED:<trigger-phrase>`. Run the exact foreground wait command from /merging-standards `<pr_check_wait>`, then return to Step 1:

```bash
gh pr checks <pr-number> --watch --fail-fast --interval 30
```

The command exits when all PR checks finish, and `--fail-fast` exits when any check fails. Do not schedule runtime heartbeats or timers for PR checks.

**Step 8 — Evaluate the merge gates and act.** Apply /merging-standards `<authority_gates>`: `MERGE_READINESS`, then `PRODUCTION_READINESS`.

When evaluating the review predicate, read the current-head CI review from the three surfaces Step 2 inspects (per /merging-standards `<review_inspection>`) — the review-kind findings posted after the latest push. The predicate is clean only when such a review exists, is complete and valid, and reports no unresolved `BLOCKING` or `DEBT` finding — stated directly, or with every such finding individually dropped as unbacked (a `DEBT` finding the author tracks out of scope with a recorded reason is not unresolved); the mere absence of a current-head review is `WAIT_FOR_REVIEW`, never a clean read. To tell a not-yet-run review from a deliberately skipped one, read the review-kind check's conclusion on Step 1's `statusCheckRollup` — identify it by role (the check that runs the changeset review), not by a fixed name — and confirm with `gh pr checks <pr-number>`. If that conclusion is `skipped`, retrieve the cause with `gh run view <run-id> --json conclusion,jobs` (run ID in `detailsUrl`) or `gh api repos/<owner>/<repo>/actions/jobs/<job-id> --jq '.steps[]'` — a skip caused by the PR modifying the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate) triggers the reviewer-skipped-by-design exception below.

If the conclusion is `skipped` **because the PR modifies the reviewer's own workflow file** (GitHub Actions' identical-workflow-content gate) and no current-head review has been posted, apply the reviewer-skipped-by-design exception from /merging-standards `<authority_gates>`. For any other skip cause (path filter, branch filter, manual skip), emit `WAIT_FOR_REVIEW` and do not post the trigger-phrase comment — the exception is scoped to the self-modifying-PR case only.

Reviewer-skipped-by-design exception steps:

1. Resolve the trigger phrase per /merging-standards `<repo_local_overlay>` (the Mention-reviewer trigger phrase topic; default `@spec-tree` when the overlay is silent).
2. Post one PR-level comment with body exactly `<trigger-phrase> review` via `gh pr comment <pr-number>`.
3. Emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run Step 7, and re-inspect. The mention-triggered reviewer's posted findings become the current-head review the next management pass reads.

Otherwise, evaluate `MERGE_READINESS` from observable PR state:

- A clean current-head CI review exists — present, complete and valid, and reporting no unresolved `BLOCKING` or `DEBT` finding — stated directly, or with every such finding individually dropped as unbacked, a `DEBT` finding the author tracks out of scope with a recorded reason not unresolved (a valid in-scope `BLOCKING`/`DEBT` finding is fixed in Step 5 — if one remains this pass, emit `FIX_FINDING:<item>`); the absence of a current-head review is `WAIT_FOR_REVIEW`, never clean.
- Every other required check is terminal-green per /merging-standards `<authority_gates>`. If no current-head review has landed yet, emit `WAIT_FOR_REVIEW`; else if a required check is non-terminal, emit `WAIT_FOR_CHECKS`; if a required check is terminal-but-not-success or absent, or a PR-state predicate (`OPEN`, `isDraft` false, head SHA matches, rebased onto base) fails, emit `MERGE_BLOCKED:<reason>`.

For `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, or `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run Step 7 and immediately return to Step 1 in the same turn. Do not merge or emit a final token from pre-watch state. The post-watch pass must re-read PR state, check rollup, PR-level comments, formal reviews, and review-thread comments before deciding the next action.

When `MERGE_READINESS` appears to hold, evaluate `PRODUCTION_READINESS`. If `PRODUCTION_READINESS` also holds, run the mutation-point guard from /merging-standards `<authority_gates>` immediately before the merge command. The guard re-reads live PR state and returns either `MERGE_READY:<head-sha>` or one existing action token. Do not run `gh pr merge` unless the guard returns `MERGE_READY:<head-sha>` for the head SHA just inspected.

- **Not production-relevant (per the overlay's recognition mechanism, or no mechanism declared), or operator-approved** -> merge using the project's merge command only after the mutation-point guard returns `MERGE_READY:<head-sha>`. Claude follows the overlay's declared command if any. When the overlay is silent on the merge command, the universal default is rebase merge followed by the worktree-safe manual branch deletion in /merging-standards `<merge_cleanup>` — `gh pr merge <pr-number> --rebase --delete-branch=false`, then detach this worktree onto the refreshed base tip and delete the local and remote branches separately. Claude never selects a merge commit or squash command from the gate alone; those require the overlay to opt in. An overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for always-single-worktree projects, where `gh`'s post-merge switch-to-base never collides.

  Overlay-silent default (per /merging-standards `<merge_cleanup>`):

  ```bash
  base=$(gh pr view <pr-number> --json baseRefName --jq '.baseRefName')
  branch=$(gh pr view <pr-number> --json headRefName --jq '.headRefName')
  git fetch origin "${base}" "${branch}"
  gh pr view <pr-number> --json number,state,isDraft,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus,statusCheckRollup,reviews,comments
  gh pr checks <pr-number>
  gh api repos/<owner>/<repo>/pulls/<pr-number>/comments
  # Continue only after the guard verdict is MERGE_READY:<head-sha>.
  # mergeable / mergeStateStatus / gh acceptance are not authority.
  # explicit --delete-branch=false — never rely on gh's default for the omitted flag
  # (varies by version/config, unknowable across consumers); =false skips gh's switch to
  # "${base}", which would fail when "${base}" is checked out in another worktree
  gh pr merge <pr-number> --rebase --delete-branch=false
  git fetch origin "${base}"
  git switch --detach "origin/${base}"   # step this worktree off the merged branch
  git branch -D "${branch}" 2>/dev/null || true   # delete the local branch (tolerate "not found")
  git ls-remote --exit-code --heads origin "${branch}" >/dev/null 2>&1 && git push origin --delete "${branch}"
  git status --porcelain
  ```

  Emit `POST_MERGE_VERIFY` if the project requires post-merge verification.
- **Production-relevant and not yet approved** -> emit `AWAIT_APPROVAL:<reason>` and wait for the operator's explicit approval. Claude has already done the full `MERGE_READINESS` work; only execution waits.

If `MERGE_READINESS` does not hold, emit exactly one token from /merging-standards `<action_tokens>`. For `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, or `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run Step 7 and re-inspect. For `AWAIT_APPROVAL`, `SYNC_BASE`, or `MERGE_BLOCKED:<reason>`, stop at the operator boundary or concrete blocker the token names.

**Exit when:** the PR is merged, closed, or the gate emits a terminal token (`POST_MERGE_VERIFY`). Otherwise return to Step 1 after Step 7 or after the operator resolves a token boundary.

</the_managing_flow>

<commands_reference>

For pre-flight, branch topology, push semantics, base sync, the authority gates, the PR-check wait requirement, review inspection, review classification, and the action token table, see /merging-standards. For commit selection, message format, and atomic-commit rules, see /commit-changes. Managing-flow-specific commands:

```bash
# PR identity
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,comments

# Checks snapshot
gh pr checks <pr-number>

# Required PR-check wait
gh pr checks <pr-number> --watch --fail-fast --interval 30

# Post a PR-level comment (top of the conversation), interactive harness form
gh pr comment <pr-number> --body-file - <<'EOF'
### BLOCKING [consistency]: path/to/file:42
Reference: ...
Evidence: ...
Required: ...
EOF

# Post a formal review comment (counts as a review), interactive harness form
gh pr review <pr-number> --comment --body-file - <<'EOF'
Summary of remaining items:
- 1 BLOCKING ...
- 2 DEBT ...
EOF

# Programmatic runner form for either payload-bearing gh command.
# Keep each pipeline as one physical shell line; each printf argument is one body line.
printf '%s\n' '### BLOCKING [consistency]: path/to/file:42' 'Reference: ...' 'Evidence: ...' 'Required: ...' | gh pr comment <pr-number> --body-file -
printf '%s\n' 'Summary of remaining items:' '- 1 BLOCKING ...' '- 2 DEBT ...' | gh pr review <pr-number> --comment --body-file -

# Reply within an existing review thread (line-level comment)
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments \
  --method POST \
  --field in_reply_to=<review-comment-id> \
  --field body="Acknowledged — fix in next push."

# Mark a review thread resolved
gh api graphql --silent \
  -f query='mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }' \
  -F id=<review-thread-node-id>

# Merge (only after MERGE_READINESS, PRODUCTION_READINESS, and the mutation-point guard hold;
# per /merging-standards <authority_gates> + <merge_cleanup>)
# Overlay-silent universal default: rebase merge, then worktree-safe manual branch deletion.
base=$(gh pr view <pr-number> --json baseRefName --jq '.baseRefName')
branch=$(gh pr view <pr-number> --json headRefName --jq '.headRefName')
git fetch origin "${base}" "${branch}"
gh pr view <pr-number> --json number,state,isDraft,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus,statusCheckRollup,reviews,comments
gh pr checks <pr-number>
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments
# Continue only after the guard verdict is MERGE_READY:<head-sha>.
gh pr merge <pr-number> --rebase --delete-branch=false   # explicit; see <merge_cleanup>
git fetch origin "${base}"
git switch --detach "origin/${base}"
git branch -D "${branch}" 2>/dev/null || true
git ls-remote --exit-code --heads origin "${branch}" >/dev/null 2>&1 && git push origin --delete "${branch}"
git status --porcelain
```

</commands_reference>

<failure_modes>

**Merged into a void — an absent review read as clean.** Claude evaluated the `MERGE_READINESS` review predicate as "no valid finding" and merged a PR whose current-head CI review had not landed at all: zero findings was indistinguishable from zero review. The predicate requires a clean review to *exist* — a conforming current-head review that reports no unresolved `BLOCKING` or `DEBT` finding (stated directly, or with every such finding individually dropped as unbacked; a `DEBT` finding the author tracks out of scope with a recorded reason is not unresolved). A PR with no current-head review emits `WAIT_FOR_REVIEW` and never merges (Step 8; /merging-standards `<authority_gates>`).

**Pushed a tree only one predicate had seen.** Claude re-ran deterministic verification after a review-driven fix, or re-ran the local review after a verification-driven fix, but not both on the final tree — each fix is a new diff the other predicate has not covered, so the pushed tree was never jointly gated. Step 6 iterates both predicates to a joint fixpoint: after every commit, re-run both until one tree passes verification *and* carries no unaddressed valid finding, then push only that tree.

**Wait-token-only without the foreground wait.** Claude emitted `WAIT_FOR_CHECKS` or `WAIT_FOR_REVIEW` and ended the turn, leaving the operator to re-check the PR manually while current-head checks were still running. Step 8 runs `gh pr checks <pr-number> --watch --fail-fast --interval 30` when the PR is blocked by check completion, then restarts full inspection from Step 1 before acting.

**Used GitHub mergeability as authority.** Claude merged while current-head PR review/check automation was still running because GitHub reported the PR as mergeable and accepted `gh pr merge`. Host mergeability is not the repository policy gate; it ignores the stricter requirement that current-head review output exists and all required checks are terminal-green. Run the mutation-point guard immediately before merge; if any current-head review/check predicate is absent or non-terminal, emit the wait token and refresh tracking.

</failure_modes>

<success_criteria>

The managing flow satisfies its contract when, at minimum:

- /merging-standards and /commit-changes are loaded before any inspection or push.
- Each pass inspects all three surfaces from /merging-standards `<review_inspection>`.
- Each pass checks base drift in the same checkpoint as review inspection; a branch behind `origin/<base>` is rebased per /merging-standards `<base_sync>` before the queue is driven, regardless of whether a review has landed or carries findings.
- Every finding is labeled with one of `BLOCKING` / `DEBT` — never `FOLLOW-UP`, never a severity rank, never a legacy class label — and acted on by validity and phase, never by severity.
- The work queue fixes every valid in-scope finding the open-PR review surfaces — no deferral of in-scope work; a `DEBT` finding the author judges out of scope is recorded in `ISSUES.md` / `PLAN.md` with a recorded reason and tracked, not a merge blocker.
- Every follow-up push re-establishes `REVIEW_READINESS` on the diff it would publish — local deterministic verification passes per /merging-standards `<local_deterministic_scope>` (or, for a push that only rebased onto an advanced base, the preservation-proof-scoped lane per /merging-standards `<base_sync>`), and the local `review-changes` review (invoked at parity per /merging-standards `<local_review_invocation>`, with no caller narrowing) has converged with no valid finding unaddressed — re-runs /merging-standards `<branch_hygiene>`, and goes to the ready PR with no draft toggle.
- Pending PR checks or current-head CI review use exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30` per /merging-standards `<pr_check_wait>`.
- Merge fires autonomously only when `MERGE_READINESS` and `PRODUCTION_READINESS` both hold and the mutation-point guard has just produced `MERGE_READY:<head-sha>`: a clean current-head CI review exists (present, complete and valid, reporting no unresolved `BLOCKING` or `DEBT` finding — stated directly or with every such finding individually refuted as unbacked, a `DEBT` finding the author tracks out of scope with a recorded reason not unresolved — its absence is never clean), every other required check is terminal-green, branch hygiene and PR-state hold, the inspected head SHA matches the fetched remote branch head and status-check head, and the change is non-production-relevant or operator-approved.
- A production-relevant, unapproved change emits `AWAIT_APPROVAL:<reason>` and waits; Claude does the full `MERGE_READINESS` work regardless.
- A current-head CI review skipped **because the PR modifies the reviewer's own workflow file** (`conclusion: skipped`, GitHub Actions' identical-workflow-content gate) triggers the reviewer-skipped-by-design exception from /merging-standards `<authority_gates>`: post `<trigger-phrase> review` as a PR-level comment and emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`. For any other skip cause, emit `WAIT_FOR_REVIEW` — the exception is scoped to the self-modifying-PR case only.
- The foreground PR-check wait inspects the terminal check result, then re-runs the full Step 1/Step 2 inspection before deciding the next action.
- `gh pr merge` is never run as a probe for mergeability; `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, and command acceptance are not merge predicates.
- Each pass that does not fire an autonomous action emits exactly one token from /merging-standards `<action_tokens>`.
- No `<self_reference>` violation per /merging-standards.

</success_criteria>
