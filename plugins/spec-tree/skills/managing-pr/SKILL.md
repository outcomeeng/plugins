---
name: managing-pr
description: >-
  ALWAYS invoke this skill when managing an open pull request after PR creation — inspecting review and check state, classifying review feedback, posting findings, pushing follow-up commits, or deciding the next PR lifecycle action.
  NEVER use this skill to create a pull request; use opening-pr for PR creation.
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, Skill
---

<objective>

Drive the post-creation pull request loop without treating advisory review prose as approval, merge authority, or completion. This skill owns the iteration phase: read review state on every relevant surface, classify each item by required receiver action, address BLOCKING and NEEDS-ANSWER items, push follow-up commits, and report the next repository-governed action. PR creation, branch hygiene, push semantics, draft lifecycle, heartbeat protocol, and three-surface review inspection are inherited from `/standardizing-merging`. Commits and the closure gate run via `/committing-changes`.

</objective>

<scope>

This skill does NOT:

- Create the PR (use `/opening-pr`)
- Push commits to a branch with no PR (use `/opening-pr`)
- Merge, squash, or close the PR
- Promote draft → ready without the four prerequisites in `/standardizing-merging` `<draft_lifecycle>`
- Stage or compose commit messages (use `/committing-changes`)
- Watch CI runs, poll in-shell, or `sleep` to wait (use `/standardizing-merging` `<heartbeat>`)
- Review someone else's PR with the goal of producing review prose for them (use `/reviewing-pr`)

</scope>

<essential_principles>

- Advisory review comments are normal PR feedback. They are distinct from GitHub approval reviews, merge decisions, and reactions.
- Classify every review item by required receiver action: `BLOCKING`, `NEEDS-ANSWER`, `FOLLOW-UP`, or `NOTE`.
- Drive the work loop only from `BLOCKING` and `NEEDS-ANSWER` items. `FOLLOW-UP` items are tracked in the owning durable location when worth preserving. `NOTE` items create no work.
- Keep review scope tied to the PR diff plus immediate context needed to judge it.
- Use one-shot inspections per `/standardizing-merging` `<review_inspection>`; never watch CI, poll, or keep a shell process alive while waiting.
- When code changes are required, invoke the relevant coding/testing/spec/prose skill via the Skill tool before editing. This skill coordinates the PR loop; domain skills own implementation quality.

</essential_principles>

<classification>

| Class          | Receiver action             | Use when                                                                                                                                                         |
| -------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BLOCKING`     | Fix in this PR before merge | The PR introduces a correctness bug, security risk, data-loss risk, production-safety risk, broken required validation, secret exposure, or direct policy break. |
| `NEEDS-ANSWER` | Answer before merge         | A required fact is missing from the diff or PR context, and the answer can clear the concern or convert it to `BLOCKING`.                                        |
| `FOLLOW-UP`    | Track outside this PR       | The concern is valid, but fixing it would widen the PR or does not affect merge safety for this change.                                                          |
| `NOTE`         | No action expected          | Context, praise, explanation, or an observation that does not create work.                                                                                       |

Severity-rank labels (`P0` / `P1` / `P2` / `P3`, `critical`, `high`, `medium`, `low`, `minor`, `nit`) MUST NOT drive the receiver action queue. Receiver action is the only ordering signal.

</classification>

<workflow>

**Step 0: Load references.** Invoke `/standardizing-merging` (cross-cutting merge-flow standards) via the Skill tool. Invoke `/committing-changes` via the Skill tool before any commit or push.

**Step 1: Identify the PR.** Resolve the current branch's PR:

```bash
gh pr view --json number,url,headRefName,baseRefName,state,isDraft,mergeStateStatus,statusCheckRollup,reviewDecision
```

**Step 2: Inspect review state on all three surfaces.** Use `/standardizing-merging` `<review_inspection>` — never check only `reviews`. Run the formal-reviews + PR-level-comments query AND the review-thread-comments query, comparing timestamps against the most recent push.

**Step 3: Classify feedback.** Rewrite every actionable item into the four-class model. Preserve the reviewer evidence: source comment, file path, line, and reason. Use `<comment_format>` below for each item.

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

**Step 8: Report the next repository-governed action.** End the turn with one of these named tokens stated explicitly:

- `WAIT_FOR_CHECKS` — checks still running; heartbeat will re-fire
- `WAIT_FOR_REVIEW` — checks green, awaiting human or bot review
- `FIX_BLOCKING:<item>` — at least one BLOCKING item remains
- `ANSWER_NEEDED:<item>` — at least one NEEDS-ANSWER item remains
- `MARK_READY` — closure gate passed, four prerequisites hold, ready for explicit human promotion
- `MERGE_AUTHORIZED` — user has explicitly authorized merge
- `SYNC_BASE` — base branch has advanced; rebase needed before further action
- `POST_MERGE_VERIFY` — PR merged; run post-merge verification per the project's Git workflow

A turn that ends with "looks good, let me know if you need anything" does NOT satisfy this success criterion.

</workflow>

<comment_format>

Use this shape when posting or summarizing review findings:

```text
BLOCKING [correctness]: path/to/file.py:42
Evidence: The changed branch now raises on an empty profile list because ...
Required before merge: Preserve the previous no-op behavior or add evidence that the new failure is intended.
```

```text
NEEDS-ANSWER [scope]: path/to/file.py:108
Evidence: The new helper duplicates logic in <other-module>, but the diff does not say why it cannot reuse it.
Question: Is the duplication intentional (e.g., the modules will diverge soon)? If not, reuse and drop the duplicate.
```

```text
FOLLOW-UP [test-evidence]: spx/.../tests/test_x.py
Evidence: The test covers the happy path but not rollback.
Track under: spx/.../ISSUES.md.
```

```text
NOTE [praise]: path/to/file.py:200
The new error path is clearer than what was there. No action.
```

</comment_format>

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
- The turn ends with one of the named action tokens from `<workflow>` Step 8 stated explicitly — never "looks good, let me know if you need anything"

</success_criteria>

<critical_rules>

1. **NEVER use this skill to create a PR** — use `/opening-pr`.
2. **NEVER promote draft → ready without the four prerequisites in `/standardizing-merging` `<draft_lifecycle>` rule 3** — explicit human instruction, closure gate just run, gate passed, change asserted mergeable.
3. **NEVER inspect only `reviews` after a push** — always check `reviews` AND PR-level `comments` AND review-thread comments via `gh api .../pulls/<n>/comments`.
4. **NEVER watch CI, poll in-shell, or `sleep` to wait** — use `/standardizing-merging` `<heartbeat>`.
5. **NEVER skip the upstream-safety check before a follow-up push** — `push.default=tracking` will publish feature-branch commits to `origin/main` if upstream is set wrong.
6. **NEVER drive the queue from severity ranks** — `BLOCKING` / `NEEDS-ANSWER` / `FOLLOW-UP` / `NOTE` is the only valid taxonomy.
7. **NEVER end the turn with vague handoff prose** — name one of the action tokens from `<workflow>` Step 8.
8. **NEVER create a second heartbeat for the same PR** — refresh the existing one per `/standardizing-merging` `<heartbeat>`.
9. **NEVER include self-reference** in commits, comments, or PR text — no "Claude", "AI", "agent", "Co-Authored-By: Claude".

</critical_rules>

<failure_modes>

Real failure patterns to avoid:

- **Treating advisory bot prose as approval.** Bot reviewers (e.g., automated review agents) often post observations as PR-level issue comments with no `state: APPROVED`. The author reads "looks good overall" and ships — missing the BLOCKING item buried later in the same comment. Classify every actionable line, not just the conclusion.
- **Checking only `reviews` and missing comment-surface re-feedback.** After a follow-up push, bot reviewers often re-fire as PR-level issue comments rather than formal reviews. A `gh pr view --json reviews` query returns the prior approval and looks clean; the new comments-surface critique is invisible until merge time. The three-surface inspection in `/standardizing-merging` `<review_inspection>` is the antidote.
- **Skipping the upstream-safety check on follow-up pushes.** A branch created with `git switch -c <branch> origin/main` sets upstream to `origin/main`. With `push.default=tracking`, a bare `git push` then routes feature-branch commits directly to `origin/main`. Re-run `<branch_hygiene>` on every push.
- **Burning expensive CI on guesses.** Promoting draft → ready without the closure gate makes the ready flip a guess. CI then spends the team's budget validating an unverified assertion. The four prerequisites are not optional.

</failure_modes>
