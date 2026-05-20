---
name: managing-pr
description: >-
  ALWAYS invoke this skill when managing an open pull request after PR creation — inspecting review and check state, classifying review feedback, posting findings, pushing follow-up commits, or deciding the next PR lifecycle action.
  NEVER use this skill to create a pull request; use opening-pr for PR creation.
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, Skill
---

<objective>
The managing flow. Loop body that runs per heartbeat fire: inspect → classify → sync to base → drive queue → push follow-ups → refresh heartbeat → evaluate PR authority gate → act. Authority for promotion and merge is the PR authority gate from /standardizing-merging `<pr_authority_gate>`. Every step is a routine workflow operation that runs without operator confirmation; the only authority-gated waits are the action tokens from /standardizing-merging `<action_tokens>`, emitted when the gate fails a predicate or the overlay declares human-required authority.
</objective>

<the_managing_flow>

Walk these steps on every heartbeat fire. Routine steps — inspect, classify, rebase, push, refresh heartbeat — run directly. The only pauses are the autonomous action runs (promotion or merge under gate-green-autonomous authority) and the action-token emissions when the gate or overlay requires waiting.

**Step 0 — Load references.** Invoke /standardizing-merging (shared vocabulary) and /committing-changes (commit format for any follow-up commits) via the Skill tool.

**Step 1 — Identify the PR.**

```bash
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision
```

**Step 2 — Inspect three surfaces and check base drift.** Run /standardizing-merging `<review_inspection>` queries. Compare timestamps against the most recent push; entries after that push are re-reviews of the latest state. In the same checkpoint, fetch `origin/<base>` and determine whether the branch is behind it — review state and base drift are read together so the rebase can proceed during the wait for reviews, not only after they land.

**Step 3 — Classify every finding.** Apply the three-severity / six-category taxonomy from /standardizing-merging `<review_classification>`. Convert any severity-rank labels (`P0`, `critical`, `nit`) or legacy class labels (`NEEDS-ANSWER`, `NOTE`) on incoming feedback to one of the three severities before queuing — reframe open questions as findings and omit commentary that does not constitute a finding.

**Step 4 — Sync to base.** If Step 2 found the branch behind `origin/<base>`, rebase per /standardizing-merging `<base_sync>` now — independent of whether a review has landed and independent of whether any landed review carries findings. A branch behind base is superseded before it can merge, so rebasing immediately aims CI and reviewers at the head that will actually merge and surfaces a nasty rebase early. An unresolvable conflict emits `SYNC_BASE` and ends the pass; otherwise Step 6 runs the closure gate against the rebased tree and pushes it with `--force-with-lease`.

**Step 5 — Drive the queue.** Address `BLOCKING` first, then `DEBT` — both require fix-in-this-PR. Record accepted `FOLLOW-UP` items in the owning node's `ISSUES.md` or `PLAN.md` (edit those files directly via the Edit or Write tool — they are committed coordination artifacts, not spec assertions).

**Step 6 — Push follow-ups deliberately.** Validate via the narrowest meaningful check after each fix. Before any push that approaches ready or merge, and before any push that follows a Step 4 rebase, run the project's local closure gate (named in `spx/local/merging.md` if defined) — a rebased branch carries a freshly integrated tree no prior gate run covered. Commit via /committing-changes. Re-run /standardizing-merging `<branch_hygiene>` before every push — hygiene applies on every push, not only at creation. Push via /standardizing-merging `<push_semantics>`; a pass that rebased in Step 4 pushes with the `--force-with-lease` form. For post-ready follow-ups, default to `gh pr ready --undo <pr-number>` before pushing per /standardizing-merging `<pr_authority_gate>` post-ready follow-up rule, unless `spx/local/merging.md` permits keeping the PR ready when the closure gate has just re-passed.

**Step 7 — Refresh the heartbeat.** Per /standardizing-merging `<heartbeat>`, refresh the existing heartbeat. One heartbeat per PR.

**Step 8 — Evaluate the PR authority gate and act.** Apply /standardizing-merging `<pr_authority_gate>` at the moment that fits the PR's current state.

When evaluating the review predicate, locate the `spec-tree-review / spec-tree-review` check in Step 1's `statusCheckRollup` and read its conclusion. Confirm with `gh pr checks <pr-number>` for the human-readable status. If the check is missing from the rollup or its conclusion is ambiguous, fetch the underlying job with `gh run view <run-id> --json conclusion,jobs` (the run ID is in `detailsUrl`). If the conclusion is `skipped`, retrieve the skip cause from `gh api repos/<owner>/<repo>/actions/jobs/<job-id> --jq '.steps[]'` (or read the job's annotations) — GitHub Actions records "PR head differs from main" as the cause for the identical-workflow-content gate.

If the conclusion is `skipped` **with cause "PR head differs from main"** and no current-head three-severity review has been posted, apply the reviewer-skipped-by-design exception from /standardizing-merging `<pr_authority_gate>`. For any other skip cause (path filter, branch filter, manual skip), emit `WAIT_FOR_REVIEW` and do not post the trigger-phrase comment — the exception is scoped to the self-modifying-PR case only.

Reviewer-skipped-by-design exception steps:

1. Resolve the trigger phrase from `spx/local/merging.md`'s **Mention-reviewer trigger phrase** topic (defaulting to `@claude` per /standardizing-merging `<repo_local_overlay>` when the overlay is silent).
2. Post one PR-level comment with body exactly `<trigger-phrase> review` via `gh pr comment <pr-number>`.
3. Emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, refresh the heartbeat, and exit Step 8. The mention-triggered reviewer's posted findings become the current-head three-severity review the next heartbeat reads.

Otherwise, branch on PR state:

- **PR is draft (`isDraft = true`):** evaluate the gate's promotion-time predicates. If every predicate holds, consult the overlay's draft-promotion-authority topic:
  - **Gate-green-autonomous (default):** run `gh pr ready <pr-number>`, refresh the heartbeat, and emit `WAIT_FOR_CHECKS` while ready-state CI fires.
  - **Overlay-requires-human:** emit `MARK_READY` and wait for the operator's explicit promotion instruction.

- **PR is ready (`isDraft = false`):** evaluate the gate's merge-time predicates (including the merge-only predicates: head SHA matches branch head, branch rebased onto current `origin/<base>`). If every predicate holds, consult the overlay's merge-authority topic:
  - **Gate-green-autonomous (default):** merge using the project's merge command. The default is rebase merge with remote-branch deletion; the overlay may specify a different command (merge commit, squash, or a two-step delete that avoids multi-worktree cleanup failures):

    ```bash
    gh pr merge <pr-number> --rebase --delete-branch
    git fetch origin <base>
    git switch --detach "origin/<base>"
    git status --porcelain
    ```

    Emit `POST_MERGE_VERIFY` if the project requires post-merge verification.
  - **Overlay-requires-human:** emit `AWAIT_MERGE_INSTRUCTION` and wait for the operator's explicit merge instruction.

If the gate at either moment does not pass, emit exactly one token from /standardizing-merging `<action_tokens>` and rely on the heartbeat to re-fire.

**Exit when:** the PR is merged, closed, or the gate emits a terminal token (`POST_MERGE_VERIFY`). Stop the heartbeat. Otherwise the next heartbeat fire re-enters Step 1.

</the_managing_flow>

<commands_reference>

For pre-flight, branch topology, push semantics, base sync, the PR authority gate, the heartbeat, review inspection, review classification, and the action token table, see /standardizing-merging. For commit selection, message format, and atomic-commit rules, see /committing-changes. Managing-flow-specific commands:

```bash
# PR identity
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision

# Checks (one-shot — NEVER --watch per /standardizing-merging <heartbeat>)
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

# Draft / ready transitions (per /standardizing-merging <pr_authority_gate>)
gh pr ready <pr-number>          # autonomous fire under gate-green-autonomous promotion
gh pr ready --undo <pr-number>   # ready → draft before a follow-up push
```

</commands_reference>

<success_criteria>

The managing flow satisfies its contract when, at minimum:

- /standardizing-merging and /committing-changes are loaded before any inspection or push.
- Each pass inspects all three surfaces from /standardizing-merging `<review_inspection>`.
- Each pass checks base drift in the same checkpoint as review inspection; a branch behind `origin/<base>` is rebased per /standardizing-merging `<base_sync>` before the queue is driven, regardless of whether a review has landed or carries findings.
- Every finding is labeled with one of `BLOCKING` / `DEBT` / `FOLLOW-UP` — never a severity rank, never a legacy four-class label.
- The work queue is driven from `BLOCKING` and `DEBT` only — both require fix-in-this-PR.
- Every follow-up push re-runs /standardizing-merging `<branch_hygiene>`.
- Promotion fires autonomously under gate-green-autonomous draft-promotion authority; under overlay-requires-human, `MARK_READY` is emitted instead.
- Merge fires autonomously under gate-green-autonomous merge authority; under overlay-requires-human, `AWAIT_MERGE_INSTRUCTION` is emitted instead.
- Production-class PRs trigger `PRODUCTION_HOLD:<reason>` for both actions regardless of overlay.
- A skipped auto-review job (`spec-tree-review / spec-tree-review: conclusion: skipped`) **with cause "PR head differs from main"** triggers the reviewer-skipped-by-design exception from /standardizing-merging `<pr_authority_gate>`: post `<trigger-phrase> review` as a PR-level comment and emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`. For any other skip cause (path filter, branch filter, manual skip), emit `WAIT_FOR_REVIEW` — the exception is scoped to the self-modifying-PR case only.
- Each pass that does not fire an autonomous action emits exactly one token from /standardizing-merging `<action_tokens>`.
- No `<self_reference>` violation per /standardizing-merging.

</success_criteria>
