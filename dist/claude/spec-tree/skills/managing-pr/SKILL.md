---
name: managing-pr
description: >-
  ALWAYS invoke this skill when managing an open pull request after PR creation — inspecting review and check state, classifying review feedback, posting findings, pushing follow-up commits, or deciding the next PR lifecycle action.
  NEVER use this skill to create a pull request; use opening-pr for PR creation.
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, Skill
---

<objective>
The managing flow. Loop body that runs per heartbeat fire: inspect → classify → sync to base → drive queue → re-review and push follow-ups → refresh heartbeat → evaluate the merge gates → act. Authority for merge comes from the `MERGE_READINESS` and `PRODUCTION_READINESS` gates in /standardizing-merging `<authority_gates>`; the PR is already `ready_for_review` (opened ready once `REVIEW_READINESS` held), so there is no draft-to-ready transition in this loop. Every step is a routine workflow operation that runs without operator confirmation; the only authority-gated wait is `AWAIT_APPROVAL`, emitted when `MERGE_READINESS` holds but the change is production-relevant and unapproved.
</objective>

<the_managing_flow>

Walk these steps on every heartbeat fire. Routine steps — inspect, classify, rebase, re-review, push, refresh heartbeat — run directly. The only pauses are the autonomous merge (under `MERGE_READINESS ∧ PRODUCTION_READINESS`) and the action-token emissions when a gate withholds.

**Step 0 — Load references.** Invoke /standardizing-merging (shared vocabulary), /committing-changes (commit format for any follow-up commits), and /tracking-tasks (runtime tracking rules) via the Skill tool.

**Step 1 — Identify the PR.**

```bash
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision
```

**Step 2 — Inspect three surfaces and check base drift.** Run /standardizing-merging `<review_inspection>` queries. Compare timestamps against the most recent push; entries after that push are re-reviews of the latest state. In the same checkpoint, fetch `origin/<base>` and determine whether the branch is behind it — review state and base drift are read together so the rebase can proceed during the wait for reviews, not only after they land.

**Step 3 — Classify every finding.** Apply the three-severity / six-category taxonomy from /standardizing-merging `<review_classification>`. Convert any severity-rank labels (`P0`, `critical`, `nit`) or legacy class labels (`NEEDS-ANSWER`, `NOTE`) on incoming feedback to one of the three severities before queuing — reframe open questions as findings and omit commentary that does not constitute a finding.

**Step 4 — Sync to base.** If Step 2 found the branch behind `origin/<base>`, rebase per /standardizing-merging `<base_sync>` now — independent of whether a review has landed and independent of whether any landed review carries findings. A branch behind base is superseded before it can merge, so rebasing immediately aims CI and reviewers at the head that will actually merge and surfaces a nasty rebase early. An unresolvable conflict emits `SYNC_BASE` and ends the pass; otherwise Step 6 re-establishes `REVIEW_READINESS` (deterministic verification and the local review) against the rebased tree and pushes it with `--force-with-lease`.

**Step 5 — Drive the queue.** Process every finding by validity and phase per /standardizing-merging `<review_classification>`, never by severity. Validate each finding against its cited rule and the governing decisions; drop any the citation does not support. This is the PR-open phase: **fix every valid finding** the review surfaces (fix it, commit via /committing-changes) — there is no deferral on the open PR, because deferral is a before-open split and the PR already opened. Severity is the reviewer's reporting label; a finding's label never decides whether the agent fixes it. (A finding genuinely about work outside this PR's diff is recorded in the owning node's `ISSUES.md` or `PLAN.md` via the Edit or Write tool — those are committed coordination artifacts — but a valid finding about the shipped diff is fixed, not recorded.)

**Step 6 — Re-establish `REVIEW_READINESS`, then push follow-ups deliberately.** A Step 5 fix or a Step 4 rebase changed the diff, so before any push re-establish both `REVIEW_READINESS` predicates **on the exact tree the push would publish**. Both predicates must hold *together* on that final tree — they iterate to a joint fixpoint, not a one-time linear pass:

1. **Deterministic verification.** Run the project's full deterministic-verification command (named in `spx/local/merging.md` if defined) — a rebased branch carries a freshly integrated tree no prior run covered. Fix any failure.
2. **Local review at parity.** Run the local review to convergence per /standardizing-merging `<local_review_invocation>` — the `changes-reviewer` agent (or `/review-changes`), passing only the repository/worktree and the diff range, with no interpretive scope, no severity pre-filter, and no instruction on what to emphasize. This re-applies to the new diff the same author-side gate /opening-pr ran before the opening push; act on its findings by validity and phase per /standardizing-merging `<review_classification>`, committing fixes via /committing-changes. The local review before this push parallels the CI review that fires after it — same class of gate, opposite sides of the push.

**Any fix in either sub-step mutates the tree, so loop:** a deterministic-verification fix is a new diff the local review has not seen, and a review-driven fix is a new tree deterministic verification has not covered. Re-run both predicates after every commit until a single tree passes deterministic verification *and* carries no unaddressed valid finding — that converged tree is what Step 6 pushes. Never push a tree on which the later-fixed predicate was established before the last commit.

Then re-run /standardizing-merging `<branch_hygiene>` before the push — hygiene applies on every push, not only at creation. Push via /standardizing-merging `<push_semantics>`; a pass that rebased in Step 4 pushes with the `--force-with-lease` form. The PR is ready throughout — a follow-up push goes to the ready PR and re-fires CI; there is no draft toggle.

**Step 7 — Refresh the heartbeat.** Per /standardizing-merging `<heartbeat>` and /tracking-tasks, refresh the existing heartbeat. One heartbeat per PR.

**Step 8 — Evaluate the merge gates and act.** Apply /standardizing-merging `<authority_gates>`: `MERGE_READINESS`, then `PRODUCTION_READINESS`.

When evaluating the review predicate, locate the `spec-tree-review / spec-tree-review` check in Step 1's `statusCheckRollup` and read its conclusion. Confirm with `gh pr checks <pr-number>` for the human-readable status. If the check is missing from the rollup or its conclusion is ambiguous, fetch the underlying job with `gh run view <run-id> --json conclusion,jobs` (the run ID is in `detailsUrl`). If the conclusion is `skipped`, retrieve the skip cause from `gh api repos/<owner>/<repo>/actions/jobs/<job-id> --jq '.steps[]'` (or read the job's annotations) — GitHub Actions records "PR head differs from main" as the cause for the identical-workflow-content gate.

If the conclusion is `skipped` **with cause "PR head differs from main"** and no current-head review has been posted, apply the reviewer-skipped-by-design exception from /standardizing-merging `<authority_gates>`. For any other skip cause (path filter, branch filter, manual skip), emit `WAIT_FOR_REVIEW` and do not post the trigger-phrase comment — the exception is scoped to the self-modifying-PR case only.

Reviewer-skipped-by-design exception steps:

1. Resolve the trigger phrase from `spx/local/merging.md`'s **Mention-reviewer trigger phrase** topic (defaulting to `@spec-tree` per /standardizing-merging `<repo_local_overlay>` when the overlay is silent).
2. Post one PR-level comment with body exactly `<trigger-phrase> review` via `gh pr comment <pr-number>`.
3. Emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, refresh the heartbeat through /tracking-tasks, and exit Step 8. The mention-triggered reviewer's posted findings become the current-head review the next heartbeat reads.

Otherwise, evaluate `MERGE_READINESS` from observable PR state:

- The current-head CI `spec-tree-review` reports no valid finding (an unbacked finding is dropped; a valid finding is fixed in Step 5 — if one remains this pass, emit `FIX_FINDING:<item>`).
- Every other required check is terminal-green per /standardizing-merging `<authority_gates>`. If a required check is non-terminal, emit `WAIT_FOR_CHECKS`; if no current-head review has landed yet, emit `WAIT_FOR_REVIEW`; if a required check is terminal-but-not-success or absent, or a PR-state predicate (`OPEN`, `isDraft` false, head SHA matches, rebased onto base) fails, emit `MERGE_BLOCKED:<reason>`.

When `MERGE_READINESS` holds, evaluate `PRODUCTION_READINESS`:

- **Not production-relevant (per the overlay's recognition mechanism, or no mechanism declared), or operator-approved** → merge using the project's merge command. The agent follows the overlay's declared command if any. When the overlay is silent on the merge command, the universal default is rebase merge with remote-branch deletion — `gh pr merge <pr-number> --rebase --delete-branch` — per the Merge command topic in /standardizing-merging. The agent never selects a merge commit or squash command from the gate alone; those require the overlay to opt in. The overlay also decides whether `--delete-branch` runs inline or as a separate `git push origin --delete <branch>` to avoid multi-worktree cleanup failures.

  Overlay-silent default:

  ```bash
  gh pr merge <pr-number> --rebase --delete-branch
  git fetch origin <base>
  git switch --detach "origin/<base>"
  git status --porcelain
  ```

  Emit `POST_MERGE_VERIFY` if the project requires post-merge verification.
- **Production-relevant and not yet approved** → emit `AWAIT_APPROVAL:<reason>` and wait for the operator's explicit approval. The agent has already done the full `MERGE_READINESS` work; only execution waits.

If `MERGE_READINESS` does not hold, emit exactly one token from /standardizing-merging `<action_tokens>` and rely on the /tracking-tasks heartbeat to re-fire.

**Exit when:** the PR is merged, closed, or the gate emits a terminal token (`POST_MERGE_VERIFY`). Stop the heartbeat through /tracking-tasks. Otherwise the next heartbeat fire re-enters Step 1.

</the_managing_flow>

<commands_reference>

For pre-flight, branch topology, push semantics, base sync, the authority gates, the PR-level heartbeat requirement, review inspection, review classification, and the action token table, see /standardizing-merging. For heartbeat payload and lifecycle rules, see /tracking-tasks. For commit selection, message format, and atomic-commit rules, see /committing-changes. Managing-flow-specific commands:

```bash
# PR identity
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision

# Checks (one-shot — NEVER --watch per /standardizing-merging <heartbeat> and /tracking-tasks)
gh pr checks <pr-number>

# Post a PR-level comment (top of the conversation)
gh pr comment <pr-number> --body-file - <<'EOF'
### BLOCKING [consistency]: path/to/file.py:42
Reference: ...
Evidence: ...
Required: ...
EOF

# Post a formal review comment (counts as a review)
gh pr review <pr-number> --comment --body-file - <<'EOF'
Summary of remaining items:
- 1 BLOCKING ...
- 2 DEBT ...
EOF

# Reply within an existing review thread (line-level comment)
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments \
  --method POST \
  --field in_reply_to=<review-comment-id> \
  --field body="Acknowledged — fix in next push."

# Mark a review thread resolved
gh api graphql --silent \
  -f query='mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }' \
  -F id=<review-thread-node-id>

# Merge (when MERGE_READINESS and PRODUCTION_READINESS hold; per /standardizing-merging <authority_gates> + Merge command)
gh pr merge <pr-number> --rebase --delete-branch
```

</commands_reference>

<success_criteria>

The managing flow satisfies its contract when, at minimum:

- /standardizing-merging, /committing-changes, and /tracking-tasks are loaded before any inspection, push, or heartbeat mutation.
- Each pass inspects all three surfaces from /standardizing-merging `<review_inspection>`.
- Each pass checks base drift in the same checkpoint as review inspection; a branch behind `origin/<base>` is rebased per /standardizing-merging `<base_sync>` before the queue is driven, regardless of whether a review has landed or carries findings.
- Every finding is labeled with one of `BLOCKING` / `DEBT` / `FOLLOW-UP` — never a severity rank, never a legacy four-class label — and acted on by validity and phase, never by severity.
- The work queue fixes every valid finding the open-PR review surfaces — there is no deferral on the open PR; deferral is a before-open split handled by /opening-pr.
- Every follow-up push re-establishes `REVIEW_READINESS` on the diff it would publish — the project's full deterministic-verification command passes, and the local `reviewing-changes` review (invoked at parity per /standardizing-merging `<local_review_invocation>`, with no caller narrowing) has converged with no valid finding unaddressed — re-runs /standardizing-merging `<branch_hygiene>`, and goes to the ready PR with no draft toggle.
- Merge fires autonomously when `MERGE_READINESS` and `PRODUCTION_READINESS` both hold: the current-head CI `spec-tree-review` has no valid finding, every other required check is terminal-green, branch hygiene and PR-state hold, and the change is non-production-relevant or operator-approved.
- A production-relevant, unapproved change emits `AWAIT_APPROVAL:<reason>` and waits; the agent does the full `MERGE_READINESS` work regardless.
- A skipped auto-review job (`spec-tree-review / spec-tree-review: conclusion: skipped`) **with cause "PR head differs from main"** triggers the reviewer-skipped-by-design exception from /standardizing-merging `<authority_gates>`: post `<trigger-phrase> review` as a PR-level comment and emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`. For any other skip cause, emit `WAIT_FOR_REVIEW` — the exception is scoped to the self-modifying-PR case only.
- Each pass that does not fire an autonomous action emits exactly one token from /standardizing-merging `<action_tokens>`.
- No `<self_reference>` violation per /standardizing-merging.

</success_criteria>
