---
name: manage-pr
description: >-
  ALWAYS invoke this skill when managing, waiting on, or continuing an open pull request lifecycle after a PR exists.
argument-hint: "[pr-number|url|branch] [--return-closeout]"
allowed-tools: Read, Glob, Grep, Edit, Write, Agent, Skill, Bash(spx worktree status:*), Bash(spx diagnose:*), Bash(gh auth status:*), Bash(gh repo view:*), Bash(gh pr view:*), Bash(gh pr edit:*), Bash(gh pr checks:*), Bash(gh pr comment:*), Bash(gh pr merge:*), Bash(gh run view:*), Bash(gh api repos/*/pulls/*/comments:*), Bash(gh api repos/*/actions/jobs/*:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_review_thread.py":*), Bash(git fetch:*), Bash(git branch:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git rev-parse:*), Bash(git merge-base:*), Bash(git push:*), Bash(git switch:*), Bash(git ls-remote:*), Bash(git cherry:*), Bash(git worktree list:*), Bash(printf:*)
---

<objective>
The pull request merged into the base branch on origin with one stable closeout-ready result, or a terminal action token naming the gate condition that withholds the merge.
</objective>

<input>

`$ARGUMENTS` accepts one optional PR pointer and the optional exact marker `--return-closeout`. Remove the marker before pointer resolution. Treat the remaining complete trimmed value as a PR number, PR URL, or branch name and pass that same value to every pointer-bearing inspection command; when it is empty, resolve the PR from the current branch with bare `gh pr view`. Reject duplicate markers, unknown flags, or more than one pointer.

The marker binds post-merge ownership. Present means the caller owns broader-goal continuation and session closure, so Step 9 returns closeout-ready evidence. Absent means `/manage-pr` owns direct-invocation closure and invokes `/handoff` when its remaining-work disposition is complete.

</input>

<step name="pr_wait_and_reentry_policy">

`/manage-pr` is the re-entry point for an open pull request. When the user asks to manage, wait on, or continue a PR lifecycle, invoke `/manage-pr <pr-number|url|branch>` and inspect live GitHub and repository state before acting. When no pointer is provided, resolve the PR from the current branch with bare `gh pr view`.

Action tokens are pass-local observations derived from the current live inspection. `WAIT_FOR_REVIEW`, `WAIT_FOR_CHECKS`, `FIX_FINDING:<item>`, `MENTION_REVIEW_NEEDED:<trigger-phrase>`, `MERGE_BLOCKED:<reason>`, `AWAIT_DEPLOYMENT_AUTHORIZATION`, and `AWAIT_RELEASE_AUTHORIZATION` never store PR state and never authorize a later wait, fix, deploy, release, or closeout without a fresh `/manage-pr` inspection pass. The mutation guard verdict `MERGE_READY:<head-sha>` is also pass-local and never authorizes a later merge without a fresh `/manage-pr` inspection pass for the same inspected head. After compaction or when the foundation is absent, restart from Step 0. After foreground wait completion, a push, a review arrival, an operator reply, or any new user turn, discard prior token and guard-verdict authority and return to Step 1 for the PR pointer.

When PR checks or current-head review output are not terminal, `/manage-pr` runs exactly one foreground wait command, `gh pr checks <pr-number> --watch --fail-fast --interval 30`, then discards the pre-wait token authority and re-inspects PR state, check rollup, PR-level comments, formal reviews, review-thread comments, and base drift before deciding the next action. Runtime heartbeats, runtime timers, background waits, shell polling, background `sleep`, and `gh run watch` are invalid wait mechanisms for GitHub PR checks.

GitHub and the local repository are authoritative for PR state. Conversation memory and prior tokens are only routing hints that name why `/manage-pr` is being re-entered.

</step>

<step name="pr_identity_fields">

Every PR-state `gh pr view --json` command that participates in a management pass or re-inspection reads the formal-review and PR-level-comment surfaces in the same snapshot as check and PR state:

```bash
gh pr view <pr-number-or-url-or-branch> --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,reviews,comments
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,reviews,comments
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments --paginate
```

The `reviews` field carries formal review submissions. The `comments` field carries PR-level issue comments. The review-thread comments surface is the separate `gh api repos/<owner>/<repo>/pulls/<pr-number>/comments --paginate` call.

</step>

<step name="the_managing_flow">

Walk these steps on each management pass. Routine steps — inspect, classify, rebase, re-review, push, and foreground PR-check wait — run directly. The only pauses are the autonomous merge after `MERGE_READINESS` holds and the mutation-point guard returns `MERGE_READY:<head-sha>`, plus the action-token emissions when a gate withholds.

**Step 0 — Load references.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke /understand first. Then invoke /merging-standards (shared vocabulary) and /commit-changes (commit format for any follow-up commits) via the Skill tool. Follow /merging-standards `<reference_index>` and directly read its `merge-policy.md` reference before Step 1; invoking the compact loader alone does not load the tagged policy sections used below.

**Step 1 — Identify the PR.** When `$ARGUMENTS` is non-empty, resolve the PR from that pointer before inspecting state. Use the `<pr_identity_fields>` command field set. Use bare `gh pr view` only when `$ARGUMENTS` is empty and the current branch is the intended PR branch.

```bash
gh pr view <pr-number-or-url-or-branch> --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,reviews,comments
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,reviews,comments
```

**Step 2 — Inspect three surfaces and check base drift.** Run /merging-standards `<review_inspection>` queries. Compare timestamps against the most recent push; entries after that push are re-reviews of the latest state. In the same checkpoint, fetch `origin/<base>` and determine whether the branch is behind it — review state and base drift are read together so the rebase can proceed during the wait for reviews, not only after they land.

**Step 3 — Classify every finding.** Apply the two-severity / five-category taxonomy from /merging-standards `<review_classification>`. Convert any severity-rank labels (`P0`, `critical`, `nit`), the removed `FOLLOW-UP` severity, or legacy class labels (`NEEDS-ANSWER`, `NOTE`) on incoming feedback to one of the two severities before queuing — reframe open questions as findings and omit commentary that does not constitute a finding. Remap a legacy `standards` category by the defect's effect: use `consistency`, `security`, `performance`, `evidence`, or `architecture` under the current definitions rather than preserving the removed category.

**Step 4 — Run the safety preflight, then sync to base.** Immediately after the read-only inspection and classification in Steps 1–3, run `spx worktree status` from the assigned root and require a fresh passing /merging-standards `<occupancy_preflight>`. Then run every overlay-declared preflight check per `<overlay_safety_checks>`. Run these preflights on every management pass, including when the branch is already current, so they precede any rebase, finding repair, commit, push, or merge. Re-run `<occupancy_preflight>` immediately before any checkout or worktree transition. A failed check stops before mutation with its output preserved. `<merge_cleanup>` repeats the overlay preflight immediately before the merge command because the earlier follow-up work may have changed the inspected environment.

If Step 2 found the branch behind `origin/<base>`, invoke /merging-standards `<base_sync>` now — independent of whether a review has landed and independent of whether any landed review carries findings. A branch behind base is superseded before it can merge, so rebasing immediately aims CI and reviewers at the head that will actually merge and surfaces a nasty rebase early. `/sync-base` owns authorized dirty-tree checkpointing and retry. When its final result is `dirty_tree`, stop this management pass at that unresolved ownership boundary, preserve the exact reported paths, and resume the same PR pointer only after `/sync-base` reaches a clean result; never surface it as a rebase conflict or duplicate the commit/retry protocol here. Otherwise consume its clean result, structured `conflict` report, or hard failure. Step 6 re-establishes `VERIFICATION_READINESS` against the rebased tree — scoped by the `/sync-base` `preservation` proof per `<base_sync>`, so an unrelated base movement does not force a full re-run — and pushes it with `--force-with-lease`.

**Step 5 — Drive the queue.** Process every current-head finding by validity and phase per /merging-standards `<review_classification>`, never by severity. First build one current-head finding ledger from all inspected surfaces and reviewers, classify each item once as valid in-scope, unbacked, or separate/larger. A no-findings review from one reviewer, a clean required check, or an approved audit does not cancel a valid current-head finding from another reviewer or surface. Validate each finding against its cited rule and the governing decisions; drop any the citation does not support. For every valid finding, perform the same-class sweep required by /merging-standards `<review_classification>` across the touched node(s) before editing. This is the PR-open phase: **fix every valid in-scope finding and every in-scope parallel instance** the sweep surfaces (fix them, commit via /commit-changes) — there is no deferral of in-scope work on the open PR. Validity and scope (never the severity label) decide. A bounded fix — a rename propagation, a cross-reference update, a mechanical change, or a fix that merely touches another file — is in-scope work the changeset carries and is fixed here, never deferred. Repeated valid findings in the same lifecycle area after earlier fixes mean the same-class sweep or underlying contract is still incomplete; widen the repair and re-review rather than calling the gate stuck. A valid `DEBT` finding whose fix the author judges a separate, larger concern — its own node or feature, outside this PR's diff — is recorded in the owning node's `ISSUES.md` or `PLAN.md` via the Edit or Write tool (those are committed coordination artifacts) with a reason naming why it is large and does not block the merge; a valid in-scope finding about the shipped diff is fixed, not recorded.

**Step 6 — Re-establish `VERIFICATION_READINESS`, then push follow-ups deliberately.** A Step 5 fix or a Step 4 rebase changed the diff, so before any push re-establish all `VERIFICATION_READINESS` predicates **on the exact tree the push would publish**. All predicates must hold *together* on that final tree — they iterate to a joint fixpoint, not a one-time linear pass:

1. **Deterministic verification.** Run the project's local deterministic verification per /merging-standards `<local_deterministic_scope>` — validation and testing for the touched scope, escalating only when the overlay or risk evidence requires a wider local run. Redirect verbose command output to a temporary log path and inspect only the exit status, summary, and failing sections. One scoping exception: when this push follows **only** a base-sync rebase with no Step 5 content fix, scope this command to the lane the `/sync-base` `preservation` proof and the project overlay select per `<base_sync>`.
2. **Evidence-auditor predicates.** Dispatch every evidence auditor /merging-standards `<authority_gates>` requires for the diff after deterministic verification passes and before local review: `test-evidence-auditor` for changed `[test]` assertions, linked tests, or imported test-infrastructure artifacts; `eval-evidence-auditor` for changed `[eval]` assertions, eval artifacts, or producer artifacts for eval-backed assertions. Handle rejected, failing, or unknown verdicts per /merging-standards `<auditor_verdicts>`, committing fixes via /commit-changes and re-running deterministic verification plus the relevant auditor before local review.
3. **Local review at parity.** Run the local review to convergence per /merging-standards `<local_review_invocation>` — the `changes-reviewer` agent, which resolves its own scope (the worktree it runs in and the diff), adding no interpretive scope, no severity pre-filter, and no instruction on what to emphasize. This re-applies to the new diff the same author-side gate /open-pr ran before the opening push; act on its findings by validity and phase per /merging-standards `<review_classification>`, committing fixes via /commit-changes. The local review before this push parallels the CI review that fires after it — same class of gate, opposite sides of the push. One reuse exception: when this push follows **only** a base-sync rebase with no content change — no Step 5 fix and no fix from sub-step 1 or sub-step 2 above — reuse the converged verdict if the `/sync-base` `preservation` proof and the overlay's governance-surface list permit it per `<base_sync>`. Any content fix, in Step 5, sub-step 1, or sub-step 2, re-runs the review on the new diff.

**Any fix in any sub-step mutates the tree, so loop:** a deterministic-verification fix is a new diff the evidence auditors and local review have not seen, an evidence-audit fix changes the evidence surface, and a review-driven fix is a new tree deterministic verification and evidence auditors have not covered. Re-run all applicable predicates after every commit until a single tree passes deterministic verification, every required evidence-auditor predicate is clean, and the local review carries no unaddressed valid finding — that converged tree is what Step 6 pushes. Never push a tree on which the later-fixed predicate was established before the last commit.

Then re-run /merging-standards `<branch_hygiene>` before the push — hygiene applies on every push, not only at creation. Push via /merging-standards `<push_semantics>`; a pass that rebased in Step 4 pushes with the `--force-with-lease` form. The PR is ready throughout — a follow-up push goes to the ready PR and re-fires CI; there is no draft toggle.

<step name="pr_check_wait">

**Step 7 — PR-check wait command.** Step 8 invokes this step when it emits `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, or `MENTION_REVIEW_NEEDED:<trigger-phrase>`. `/manage-pr` owns PR check and review waits. Run the exact foreground wait command from /merging-standards `<pr_check_wait>`, then discard the pre-wait token authority and return to Step 1:

```bash
gh pr checks <pr-number> --watch --fail-fast --interval 30
```

The command exits when all PR checks finish, and `--fail-fast` exits when any check fails. Do not schedule runtime heartbeats or timers for PR checks. Do not act from the pre-wait gate tuple; Step 1 and Step 2 re-read PR state, check rollup, PR-level comments, formal reviews, review-thread comments, and base drift before the next action.

When Step 8 emits `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, or `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run Step 7 and immediately return to Step 1 in the same turn. Do not merge or emit a final token from pre-watch state. The post-watch pass must re-read PR state, check rollup, PR-level comments, formal reviews, and review-thread comments before deciding the next action.

</step>

**Step 8 — Evaluate the merge gate and act.** Apply /merging-standards `<authority_gates>`: `MERGE_READINESS`. Declared `DEPLOYMENT_READINESS` and `RELEASE_READINESS` phases are handled after merge in Step 9.

Start every Step 8 pass with the live gate tuple in prose: PR number, head SHA, current-head review state, required-check state, and the next autonomous action token or merge action. Before each mutation in this step — posting the reviewer trigger comment, merging, deleting branches through the merge cleanup sequence, or resolving review threads — name the exact target, intended command class, gate predicate that permits it, and the next inspection or lifecycle phase.

<step name="merge_readiness_decision_table">

Classify `MERGE_READINESS` in this order. The first matching rule wins; once a rule matches, ignore every later predicate even when a later predicate also fails.

1. Missing or non-terminal review-kind check -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-nonterminal"`, `guard_verdict: "WAIT_FOR_REVIEW"`, `merge_command_allowed: false`, `autonomous_action: "wait"`, `pr_comment_body: null`.
2. Current-head CI review exists with a valid `BLOCKING` or in-scope `DEBT` finding -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-valid-finding"`, `guard_verdict: "FIX_FINDING:<id>"`, `merge_command_allowed: false`, `autonomous_action: "fix-finding"`, `pr_comment_body: null`.
3. Review-kind check skipped because the PR modifies the reviewer's own workflow file and current-head CI review is absent -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-skipped-self-modifying-workflow"`, `guard_verdict: "MENTION_REVIEW_NEEDED:<trigger-phrase>"`, `merge_command_allowed: false`, `autonomous_action: "post-review-trigger-comment"`, `pr_comment_body: "<trigger-phrase> review"`.
4. Review-kind check skipped for any other reason -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-check-skipped"`, `guard_verdict: "MERGE_BLOCKED:review-check-skipped"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
5. Review-kind check failed, cancelled, timed out, requires action, or is neutral -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-check-failed"`, `guard_verdict: "MERGE_BLOCKED:review-check-failed"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
6. Current-head CI review absent after the review-kind check guard -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-absent"`, `guard_verdict: "WAIT_FOR_REVIEW"`, `merge_command_allowed: false`, `autonomous_action: "wait"`, `pr_comment_body: null`.
7. Non-review required check non-terminal -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "check-not-terminal-green"`, `guard_verdict: "WAIT_FOR_CHECKS"`, `merge_command_allowed: false`, `autonomous_action: "wait"`, `pr_comment_body: null`.
8. Non-review required check terminal-but-not-success or absent -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "check-failed-or-absent"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
9. Branch hygiene or PR-state predicate failed -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "branch-hygiene"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
10. Head SHA, fetched branch head, or status-check head mismatch -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "head-mismatch"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
11. Otherwise -> `merge_readiness: "HOLD"`, `blocking_predicate: "none"`, `guard_verdict: "MERGE_READY:<head-sha>"`, `merge_command_allowed: true`, `autonomous_action: "merge"`, `pr_comment_body: null`.

Ignore host mergeability. `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, and a successful `gh pr merge` response never authorize the merge command.

</step>

When evaluating the review predicate, read the current-head CI review from the three surfaces Step 2 inspects (per /merging-standards `<review_inspection>`) — the review-kind findings posted after the latest push. The predicate is clean only when such a review exists, is complete and valid, and reports no unresolved `BLOCKING` or `DEBT` finding across the current-head finding ledger — stated directly, or with every such finding individually dropped as unbacked (a `DEBT` finding the author tracks out of scope with a recorded reason is not unresolved). A no-findings review from one reviewer does not make the predicate clean while another current-head reviewer or review surface carries a valid unresolved finding; Step 5 owns that fix queue. The mere absence of a current-head review is `WAIT_FOR_REVIEW`, never a clean read. To tell a not-yet-run review from a deliberately failed or skipped one, read the review-kind check's conclusion on Step 1's `statusCheckRollup` — identify it by role (the check that runs the changeset review), not by a fixed name — and confirm with `gh pr checks <pr-number>`. If the conclusion is `failure`, `cancelled`, `timed_out`, `action_required`, or `neutral`, emit `MERGE_BLOCKED:review-check-failed`; review infrastructure failed, so no clean current-head review exists. If the conclusion is `skipped`, retrieve the cause with `gh run view <run-id> --json conclusion,jobs` (run ID in `detailsUrl`) or `gh api repos/<owner>/<repo>/actions/jobs/<job-id> --jq '.steps[]'` — a skip caused by the PR modifying the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate) triggers the reviewer-skipped-by-design exception below.

If the conclusion is `skipped` **because the PR modifies the reviewer's own workflow file** (GitHub Actions' identical-workflow-content gate) and no current-head review has been posted, apply the reviewer-skipped-by-design exception from /merging-standards `<authority_gates>`. For any other skip cause (path filter, branch filter, manual skip), emit `MERGE_BLOCKED:review-check-skipped` and do not post the trigger-phrase comment — the exception is scoped to the self-modifying-PR case only.

Reviewer-skipped-by-design exception steps:

1. Resolve the trigger phrase per /merging-standards `<repo_local_overlay>` (the Mention-reviewer trigger phrase topic; default `@spec-tree` when the overlay is silent).
2. Post one PR-level comment with body exactly `<trigger-phrase> review` via `gh pr comment <pr-number>`.
3. Emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run Step 7, and re-inspect. The mention-triggered reviewer's posted findings become the current-head review the next management pass reads.

Otherwise, evaluate `MERGE_READINESS` from observable PR state:

- A clean current-head CI review exists — present, complete and valid, and reporting no unresolved `BLOCKING` or `DEBT` finding across the union of current-head review surfaces and reviewers — stated directly, or with every such finding individually dropped as unbacked, a `DEBT` finding the author tracks out of scope with a recorded reason not unresolved (a valid in-scope `BLOCKING`/`DEBT` finding is fixed in Step 5 — if one remains this pass, emit `FIX_FINDING:<item>`); the absence of a current-head review is `WAIT_FOR_REVIEW`, never clean.
- Every other required check is terminal-green per /merging-standards `<authority_gates>`. The review-kind check's absent, non-terminal, skipped, and failed states are handled before this point from the check conclusion itself. If no current-head review has landed after that guard, emit `WAIT_FOR_REVIEW`; else if a non-review required check is non-terminal, emit `WAIT_FOR_CHECKS`; if a non-review required check is terminal-but-not-success or absent, or a PR-state predicate (`OPEN`, `isDraft` false, head SHA matches, rebased onto base) fails, emit `MERGE_BLOCKED:<reason>`.

For `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, or `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run Step 7 and immediately return to Step 1 in the same turn. Do not merge or emit a final token from pre-watch state. The post-watch pass must re-read PR state, check rollup, PR-level comments, formal reviews, and review-thread comments before deciding the next action.

When `MERGE_READINESS` appears to hold, run the mutation-point guard from /merging-standards `<authority_gates>` immediately before the merge command. The guard re-reads live PR state and returns either `MERGE_READY:<head-sha>` or one existing action token. Do not run `gh pr merge` unless the guard returns `MERGE_READY:<head-sha>` for the head SHA just inspected.

<step name="merge_command_selection">

Directly read /merging-standards `merge-cleanup.md` from its `<reference_index>` immediately before selecting or running the merge command.

Select the merge command only after the mutation-point guard returns `MERGE_READY:<head-sha>`:

- Use the overlay's declared merge command when one exists.
- Use the universal default from /merging-standards `<merge_cleanup>` when the overlay is silent: selected merge flag `--rebase`, explicit delete-branch flag `--delete-branch=false`, and worktree-safe manual branch deletion.
- Never select merge commit (`--merge`) or squash (`--squash`) from the gate alone; those flags require an overlay declaration.

</step>

Run the mutation-point guard inspection per /merging-standards `<authority_gates>` and continue only after it returns `MERGE_READY:<head-sha>`. Enter the single-source /merging-standards `<merge_cleanup>` sequence; its first action runs every overlay-declared preflight check immediately before the merge command, and its post-detach boundary runs every overlay-declared post-cleanup check before branch deletion. Do not transcribe a second copy of those commands here. All cleanup stays in the assigned worktree per /merging-standards `<assigned_cwd_worktree_discipline>`.

If the project declares deploy or release phases, continue through Step 9 with the branch-state closeout record and the declared phase results.

If `MERGE_READINESS` does not hold, directly read /merging-standards `action-tokens.md` from its `<reference_index>`, then emit exactly one token from `<action_tokens>`. The token is valid only for this pass. For `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, or `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run Step 7 and re-inspect. For `MERGE_BLOCKED:<reason>`, stop at the concrete blocker the token names; when the operator replies, restart this workflow for the PR pointer before acting. A base-sync conflict is handled earlier in Step 4 as a structured stop report, not an action token.

**Step 9 — Build the closeout result and apply explicit ownership.** Once the PR is merged, build the branch-state closeout record from /merging-standards `<branch_state_closeout>` and run its safe cleanup policy before deploy or release routing so every later token carries the cleanup state. If a declared deploy action exists and its authorization predicate is unsatisfied, emit `AWAIT_DEPLOYMENT_AUTHORIZATION` with the branch-state closeout record, run no deploy action, run no release action, and wait for operator authorization before re-entering Step 1. If a declared release action exists after deploy completion or a deploy no-op and its authorization predicate is unsatisfied, emit `AWAIT_RELEASE_AUTHORIZATION` with the branch-state closeout record, run no release action, and wait for operator authorization before re-entering Step 1. When declared deploy and release phases are complete or no-op, build one closeout-ready result containing the PR URL, full merged head SHA, merge commit when available, cleanup state, branch-state closeout record with **Remaining Branches** groups, deploy result, release result, and remaining-work disposition. When `--return-closeout` is present, return that result so the caller applies broader-goal continuation and session closure. When the marker is absent and the disposition names remaining in-scope work, return the result for direct continuation. When the marker is absent and the disposition says no in-scope work remains, invoke `/handoff` plain with the branch-state closeout record and return the handoff closeout. The parsed marker, never inferred caller identity, decides closeout ownership.

**Exit when:** the PR is closed, Step 9 has returned a continuation result, Step 9 has returned `/handoff` closeout, or Step 9 has emitted `AWAIT_DEPLOYMENT_AUTHORIZATION` or `AWAIT_RELEASE_AUTHORIZATION` with branch-state closeout evidence. Otherwise return to Step 1 after Step 7 or after the operator resolves a token boundary.

</step>

<script_testing>

`scripts/resolve_review_thread.py` has mapping evidence in this plugin's source test suite. The covered behavior is the review-thread resolution workflow this skill invokes.

Tested inputs and expected outputs:

- Direct thread node ID: `--host ghe.example.com PRRT_thread0002` resolves that thread by calling `gh api graphql --silent` with `id=PRRT_thread0002`.
- Review-comment discovery: `--host ghe.example.com --repo outcomeeng/plugins --pr 405 --review-comment-id 12345` discovers the owning review-thread node before resolving it.
- Thread pagination: a first review-thread page whose `pageInfo.hasNextPage` is true and `endCursor` is present leads to a follow-up `threadsAfter=<cursor>` query, then resolves the discovered thread.
- Comment pagination: a thread comments page whose `pageInfo.hasNextPage` is true and `endCursor` is present leads to a follow-up `commentsAfter=<cursor>` query before resolving the owning thread.
- Malformed resolver CLI inputs: generated thread IDs, repositories, PR numbers, comment IDs, hosts, and mixed direct/discovery modes outside the helper's source-owned validators return exit code `2`, print a validation message, and make no GitHub mutation call.
- Missing review comment: complete review-thread pagination without a matching comment returns exit code `2` with `review comment was not found after complete review-thread pagination`.
- Malformed GitHub payloads: null repository, null pull request, null paginated thread node, missing comment pagination metadata, and missing pagination cursor responses return exit code `2` with the exact failing response shape named.
- Cleanup: the helper creates no temporary files and owns no persistent state; tests assert only subprocess calls, stdout/stderr payload handling, and exit codes.

</script_testing>

<commands_reference>

For pre-flight, branch topology, push semantics, base sync, the authority gates, the PR-check wait requirement, review inspection, review classification, and the action token table, see /merging-standards. For commit selection, message format, and atomic-commit rules, see /commit-changes. Managing-flow-specific commands:

```bash
# PR identity
gh pr view <pr-number-or-url-or-branch> --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,reviews,comments
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision,reviews,comments

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

# Programmatic runner form for the PR-level comment.
# Keep each pipeline as one physical shell line; each printf argument is one body line.
printf '%s\n' '### BLOCKING [consistency]: path/to/file:42' 'Reference: ...' 'Evidence: ...' 'Required: ...' | gh pr comment <pr-number> --body-file -

# Reply within an existing review thread (line-level comment)
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments \
  --method POST \
  --field in_reply_to=<review-comment-id> \
  --field body="Acknowledged — fix in next push."

# Mark a review thread resolved
python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_review_thread.py" --host <host> <review-thread-node-id>
python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_review_thread.py" --host <host> --repo <owner>/<repo> --pr <pr-number> --review-comment-id <review-comment-id>

# Merge + branch deletion: see /merging-standards <merge_cleanup> for the single-source
# rebase-merge-then-worktree-safe-deletion sequence (the merge command, the worktree detach,
# and the local + remote branch deletion). Run it only after the mutation-point guard returns
# MERGE_READY:<head-sha> per /merging-standards <authority_gates>; cleanup stays in the assigned
# worktree per /merging-standards <assigned_cwd_worktree_discipline>. Not transcribed here.
```

</commands_reference>

<shell_scope>

The narrow Bash grants in frontmatter authorize approval-free execution. Run required consumer-declared commands from the product's root guide or active merge specialization through normal harness per-call approval when they fall outside those grants, then continue the governed step without a separate lifecycle confirmation. When the harness exposes no approval path, emit `MERGE_BLOCKED:project-command-approval-unavailable`, naming the command and declaring surface; never skip the command, widen `allowed-tools` during execution, or add repository-specific grants to this portable skill.

</shell_scope>

<failure_modes>

**Merged into a void — an absent review read as clean.** Claude evaluated the `MERGE_READINESS` review predicate as "no valid finding" and merged a PR whose current-head CI review had not landed at all: zero findings was indistinguishable from zero review. The predicate requires a clean review to *exist* — a conforming current-head review that reports no unresolved `BLOCKING` or `DEBT` finding (stated directly, or with every such finding individually dropped as unbacked; a `DEBT` finding the author tracks out of scope with a recorded reason is not unresolved). A PR with no current-head review emits `WAIT_FOR_REVIEW` and never merges (Step 8; /merging-standards `<authority_gates>`).

**Pushed a tree only one predicate had seen.** Claude re-ran deterministic verification after a review-driven fix, re-ran an evidence auditor after a verification-driven fix, or re-ran the local review after an evidence-audit fix, but did not run every applicable predicate on the final tree — each fix is a new diff the other predicates have not covered, so the pushed tree was never jointly gated. Step 6 iterates all predicates to a joint fixpoint: after every commit, re-run deterministic verification, required evidence-auditor predicates, and local review until one tree passes them all, then push only that tree.

**Wait-token-only without the foreground wait.** Claude emitted `WAIT_FOR_CHECKS` or `WAIT_FOR_REVIEW` and ended the turn, leaving the operator to re-check the PR manually while current-head checks were still running. Step 8 runs `gh pr checks <pr-number> --watch --fail-fast --interval 30` when the PR is blocked by check completion, then restarts full inspection from Step 1 before acting.

**Used GitHub mergeability as authority.** Claude merged while current-head PR review/check automation was still running because GitHub reported the PR as mergeable and accepted `gh pr merge`. Host mergeability is not the repository policy gate; it ignores the stricter requirement that current-head review output exists and all required checks are terminal-green. Run the mutation-point guard immediately before merge; if any current-head review/check predicate is absent or non-terminal, emit the wait token and refresh tracking.

</failure_modes>

<success_criteria>

The managing flow satisfies its contract when, at minimum:

- /merging-standards and /commit-changes are loaded before any inspection or push, `merge-policy.md` is read directly from /merging-standards `<reference_index>` before any tagged policy section is used, and every management pass gets a fresh `spx worktree status` proof through `<occupancy_preflight>` before checkout-sensitive mutation.
- Each pass inspects all three surfaces from /merging-standards `<review_inspection>`.
- Each pass checks base drift in the same checkpoint as review inspection; a branch behind `origin/<base>` is rebased per /merging-standards `<base_sync>` before the queue is driven, regardless of whether a review has landed or carries findings.
- Every finding is labeled with one of `BLOCKING` / `DEBT` — never `FOLLOW-UP`, never a severity rank, never a legacy class label — and acted on by validity and phase, never by severity.
- The work queue fixes every valid in-scope finding the open-PR review surfaces — no deferral of in-scope work; a `DEBT` finding the author judges out of scope is recorded in `ISSUES.md` / `PLAN.md` with a recorded reason and tracked, not a merge blocker.
- Every follow-up push re-establishes `VERIFICATION_READINESS` on the diff it would publish — local deterministic verification passes per /merging-standards `<local_deterministic_scope>` (or, for a push that only rebased onto an advanced base, the preservation-proof-scoped lane per /merging-standards `<base_sync>`), every required evidence-auditor predicate has passed, and the local `changes-reviewer` review (invoked at parity per /merging-standards `<local_review_invocation>`, with no scope narrowing) has converged with no valid finding unaddressed — re-runs /merging-standards `<branch_hygiene>`, and goes to the ready PR with no draft toggle.
- Pending PR checks or current-head CI review use exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30` per /merging-standards `<pr_check_wait>`.
- Action tokens are treated as pass-local observations only; after compaction, wait completion, push, review arrival, operator reply, or a new user turn, `/manage-pr` re-enters from the PR pointer and re-inspects live GitHub and repository state before waiting, merging, or closing.
- Merge fires autonomously only when `MERGE_READINESS` holds and the mutation-point guard has just produced `MERGE_READY:<head-sha>`: a clean current-head CI review exists (present, complete and valid, reporting no unresolved `BLOCKING` or `DEBT` finding — stated directly or with every such finding individually refuted as unbacked, a `DEBT` finding the author tracks out of scope with a recorded reason not unresolved — its absence is never clean), every other required check is terminal-green, branch hygiene and PR-state hold, and the inspected head SHA matches the fetched remote branch head and status-check head.
- After merge and declared deploy or release handling, the closeout-ready result carries the PR URL, full merged head SHA, merge commit when available, cleanup state, branch-state record with **Remaining Branches**, deploy and release results, and remaining-work disposition. The branch-state closeout record from /merging-standards `<branch_state_closeout>` has been built and safe cleanup has run. `--return-closeout` returns ownership to the caller; without it, remaining in-scope work returns for direct continuation and a complete disposition invokes `/handoff` plain.
- A current-head CI review skipped **because the PR modifies the reviewer's own workflow file** (`conclusion: skipped`, GitHub Actions' identical-workflow-content gate) triggers the reviewer-skipped-by-design exception from /merging-standards `<authority_gates>`: post `<trigger-phrase> review` as a PR-level comment and emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`. For any other skip cause, emit `MERGE_BLOCKED:review-check-skipped` — the exception is scoped to the self-modifying-PR case only.
- The foreground PR-check wait inspects the terminal check result, then re-runs the full Step 1/Step 2 inspection before deciding the next action.
- `gh pr merge` is never run as a probe for mergeability; `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, and command acceptance are not merge predicates.
- Each pass that does not fire an autonomous action emits exactly one token from /merging-standards `<action_tokens>`, except a base-sync conflict, which stops with `/sync-base`'s structured conflict report and active rebase state.
- No `<self_reference>` violation per /merging-standards.

</success_criteria>
