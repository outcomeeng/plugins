<readiness_and_review>

<authority_gates>

The delivery lifecycle runs `VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE` with four gates, evaluated in order: `VERIFICATION_READINESS`, `MERGE_READINESS`, `DEPLOYMENT_READINESS`, and `RELEASE_READINESS`. A **gate** is a named authorization over one lifecycle step, decided from defined predicates; a **predicate** is a condition a gate reads — predicates are never themselves gates. GitHub-PR publication evaluates `VERIFICATION_READINESS` before pushing; open-PR management evaluates `MERGE_READINESS` for the current head, then continues through declared `DEPLOYMENT_READINESS` and `RELEASE_READINESS` phases after merge.

**`VERIFICATION_READINESS`** authorizes publishing the verified changeset to the selected transport. For the GitHub-PR transport, it authorizes opening the PR. It holds when all predicates hold:

- **deterministic verification passes** — the project's local validation and testing commands for the touched scope per `<local_deterministic_scope>` report success. A failing touched-scope test means this predicate does not hold, including a TDD-red opener authored intentionally ahead of an implementation slice. The remedy is either land the implementation in the same PR so the test passes, or add the owning node to the project's spec-tree EXCLUDE mechanism (for example `spx/EXCLUDE`) so the test runner skips the node until implementation arrives. See `references/excluded-nodes.md` in `/understand`. Per-line suppression (`# noqa`, `# type: ignore`, `@pytest.mark.skipif`, `@pytest.mark.xfail`, equivalents in other languages) does not satisfy this predicate because those suppressions are scattered and invisible to the spec-tree status surface; and
- **required evidence audits have passed** — when the diff creates or modifies `[test]` assertions, linked test files, or test-infrastructure artifacts imported by linked tests, dispatch `test-evidence-auditor`; when the diff creates or modifies `[eval]` assertions, eval artifacts (`eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`), or producer artifacts for eval-backed assertions, dispatch `eval-evidence-auditor`. Run the applicable evidence auditors after deterministic verification passes and before `changes-reviewer`. Handle rejected, failing, or unknown evidence-auditor verdicts per `<auditor_verdicts>`; and
- **the local review has converged** — `changes-reviewer`, invoked at parity per `<local_review_invocation>` and iterated to convergence, leaves no valid finding unaddressed: each is fixed in the diff, or split out of the changeset and captured in the owning node's `ISSUES.md` / `PLAN.md`. An unbacked finding is dropped.
- **the terminal full deterministic gate has passed when required** — `just check-full` ran after every applicable evidence audit and agentic review converged, against the current clean committed head, with no subsequent change and no concurrent heavy command.

The moment `VERIFICATION_READINESS` holds, a peer PR is created `ready_for_review` and has no draft phase or gated promotion; opening ready fires every CI review at once (reviewers that wait for ready, such as Codex, alongside the CI review). A stacked PR is the sole exception: it opens draft only while its exact base PR remains unmerged, then reconstruction onto the default branch removes the stack dependency and runs `gh pr ready` exactly once. No additional draft gate or promotion exists. A declared `PREVIEW` action then runs before `MERGE_READINESS`; absent preview declaration means `PREVIEW` is a no-op and never blocks merge.

All `VERIFICATION_READINESS` predicates are re-established before every push, not only the opening push. A follow-up push that changes the branch's own content — a fix for a CI finding — re-runs local deterministic verification per `<local_deterministic_scope>`, re-runs any evidence-auditor predicate whose touched evidence surface changed, and re-runs the local review per `<local_review_invocation>` on the new diff before it is pushed. A follow-up push that **only** rebased onto an advanced base re-establishes the predicates scoped by the `<base_sync>` preservation proof — reusing the local review and evidence-auditor verdicts when the branch diff is unchanged and the base movement does not touch the governed evidence surface, and running a narrower local validation/testing lane when the proof and the project overlay permit — rather than always re-running every predicate in full. Either way, the author-side evidence audits and review precede the push that fires CI, so a follow-up diff never reaches CI without author-side agentic verification first.

**`MERGE_READINESS`** authorizes merge. It holds when all predicates hold, every one decidable from observable PR state:

- a clean current-head CI review exists — the review-kind output for the current head, read from the surfaces in `<review_inspection>`, complete and valid, that reports **no unresolved `BLOCKING` or `DEBT` finding** — stated directly per the reviewer's no-`BLOCKING`-or-`DEBT` convention, or with **every** such finding individually assessed and dropped as unbacked; a `DEBT` finding the author tracks out of scope with a recorded reason is not unresolved (validity per `<review_classification>`; a valid in-scope `BLOCKING`/`DEBT` finding is unresolved work Claude fixes before merge). When multiple reviewers or review surfaces comment on the same head, the review predicate reads the union of current-head findings: a no-findings review from one reviewer never cancels a valid finding from another reviewer, and a required-check success never cancels a valid finding posted as a PR comment or review-thread comment. The absence of a current-head review is never clean — it is `WAIT_FOR_REVIEW`;
- every other required check on `statusCheckRollup` is **terminal-green** (defined below);
- `<branch_hygiene>` passes, including the upstream-safety check;
- PR state is `OPEN`, `isDraft` is false, the inspected head SHA matches the branch head fetched from origin, and the branch is rebased onto current `origin/<base>` or is a fast-forward descendant.

`MERGE_READINESS` carries no time-based settle: a clean review arriving two minutes after open makes the gate hold two minutes after open.

**Mutation-point guard.** Immediately before any `gh pr merge` command, re-read live PR state and recompute `MERGE_READINESS`; never rely on earlier inspection, conversation memory, or a prior `gh pr view` result. The guard reads PR state, `statusCheckRollup`, PR-level comments, formal reviews, review-thread comments, the fetched remote branch head, and the fetched base branch. It produces `MERGE_READY:<head-sha>` only when the freshly inspected head SHA, fetched remote branch head, and inspected status-check SHA match and every `MERGE_READINESS` predicate above still holds for that same head.

The guard withholds the merge command and emits the existing action token when any predicate fails:

- `WAIT_FOR_REVIEW` when current-head review output is absent, or the review-kind check is missing or non-terminal.
- `WAIT_FOR_CHECKS` when a non-review required check is queued, in progress, pending, expected, or otherwise non-terminal.
- `MENTION_REVIEW_NEEDED:<trigger-phrase>` when the review-kind check is skipped because the PR modifies the reviewer's own workflow file.
- `MERGE_BLOCKED:review-check-skipped` when the review-kind check is skipped for any other cause.
- `MERGE_BLOCKED:review-check-failed` when the review-kind check is terminal but failed, cancelled, timed out, action-required, or neutral.
- `MERGE_BLOCKED:<reason>` when a non-review required check is absent or terminal-but-not-success, the head SHA does not match the fetched remote branch head or status-check head, the PR is closed/draft, the branch is not based on current `origin/<base>`, or any other hard PR-state predicate fails.

Review-kind check outcomes map before non-review required-check outcomes. Missing or non-terminal emits `WAIT_FOR_REVIEW`; success permits inspection of the review surfaces but does not satisfy the review predicate alone; a self-modifying workflow skip emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`; any other skip emits `MERGE_BLOCKED:review-check-skipped`; failed, cancelled, timed-out, action-required, or neutral emits `MERGE_BLOCKED:review-check-failed`.

`mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, and a successful `gh pr merge` response are GitHub transport behavior, not repository policy authority. Claude never runs `gh pr merge` as a probe for mergeability; the command is legal only after the mutation-point guard has produced `MERGE_READY:<head-sha>`.

**`DEPLOYMENT_READINESS`** authorizes declared environment mutation after merge. It holds when every project- or transport-declared deployment predicate authorizes the mutation. When no deploy action is declared, `DEPLOY` is a no-op phase and never blocks later phases.

**`RELEASE_READINESS`** authorizes declared consumer-visible publication or refresh after deployment. It holds when every project- or transport-declared release predicate authorizes the publication or refresh. When no release action is declared, `RELEASE` is a no-op phase and never blocks close.

When a declared deploy action exists but its authorization predicate is unsatisfied, the delivery decision is `DEPLOYMENT_READINESS = WITHHOLD` with action token `AWAIT_DEPLOYMENT_AUTHORIZATION`; when a declared release action exists but its authorization predicate is unsatisfied, the delivery decision is `RELEASE_READINESS = WITHHOLD` with action token `AWAIT_RELEASE_AUTHORIZATION`. The transport preserves the branch-state closeout record, stops before the unauthorized action, and does not continue until the operator supplies the project-declared authorization and the managing flow re-inspects state.
Claude NEVER asks the operator to choose between auto-merge, hold-at-green, or pause. The merge is a mechanical consequence of `MERGE_READINESS` plus the mutation-point guard returning `MERGE_READY:<head-sha>`, not a decision to surface; the only operator-facing pauses the lifecycle carries are the explicit `<action_tokens>` an unresolved condition emits.

**terminal-green.** A required check in `statusCheckRollup` is a check run (`status` reaches `COMPLETED`, then a `conclusion`) or a status context (`state`). It is **terminal-green** only when terminal — `status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}` — AND successful — `conclusion == SUCCESS`, or `state == SUCCESS`. A check that is non-terminal (`QUEUED` / `IN_PROGRESS` / `PENDING` / `EXPECTED`), terminal-but-not-success (`FAILURE` / `CANCELLED` / `TIMED_OUT` / `SKIPPED` / `NEUTRAL` / `ACTION_REQUIRED` / `ERROR`), or absent from the rollup is not terminal-green and blocks `MERGE_READINESS`.

**Acting on findings (validity and phase, never severity).** Claude acts on each finding by **validity** — whether it holds against its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions; read those fresh and drop a finding they do not support — and by **phase**: before open (`VERIFICATION_READINESS`) apply every valid finding that belongs and split out of the changeset only a fix too large to belong — a separate, larger concern (its own node or feature), never a bounded fix such as a rename propagation, a cross-reference update, or a mechanical change — the split work leaves the diff and is captured in `ISSUES.md` / `PLAN.md`; on the open PR (`MERGE_READINESS`) fix every valid finding whose fix belongs in the changeset and re-push, with no deferral of in-scope work — a bounded fix is in-scope work the changeset carries, never deferred — while a `DEBT` finding the author judges a separate, larger concern is recorded in `ISSUES.md` / `PLAN.md` with a reason naming why it is large and tracked, not a merge blocker. Severity is the reviewer's reporting label; validity and scope (never the label) decide whether and how Claude acts on a finding, and the reviewer never decides whether the change merges.

**Same-class sweep.** A valid review or audit finding is evidence of a defect class, not only the cited line. Before the next push, inspect the touched node(s) — the files they govern — for parallel instances of the same defect: same rule, same source contract, same evidence pattern, same lifecycle step, or same generated-source relationship. Fix every in-scope parallel instance in the same bounded changeset. If the sweep proves the cited instance isolated, record that conclusion in the review/audit handling summary. A one-line patch that only satisfies the cited example is incomplete until this sweep is done.

**Reviewer disagreement and repeated rounds.** A clean review, passing required check, approved audit, or "no findings" comment is evidence about that reviewer or verifier's scope only; it does not invalidate a separate current-head finding that is backed by its cited rule and governance. Repeated valid findings in the same lifecycle area — each exposing a deeper variant of the same source contract, state transition, crash path, idempotency boundary, artifact lifecycle, or other defect class — mean the defect class is still open. Widen the same-class sweep, repair the underlying contract, and re-run the author-side review before the next push. Never convert that pattern into a "stuck gate" stop, operator call, or merge allowance. A path being foundational, not yet consumed by production code, behind a deferred downstream slice, or covered by other clean gates does not change finding disposition: if the changed diff carries the failure mode and the finding is valid in scope, fix it in the changeset or remove/split the capability so the diff no longer carries it.

**Reviewer-skipped-by-design (self-modifying-PR exception).** When the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate), no current-head review exists for `MERGE_READINESS`. Post one PR-level comment containing exactly `<trigger-phrase> review` (e.g., `@spec-tree review`) to fire the mention reviewer (which has no identical-content gate), emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run `<pr_check_wait>`, and on the next management pass treat that reviewer's posted findings as the current-head review. This applies to that skip cause only — not path-filter, branch-filter, or manual skips.

**Follow-up pushes.** A peer PR is ready from open; a follow-up push — fixing a valid CI finding, or a `<base_sync>` rebase — pushes to the ready PR and re-fires CI with no draft toggle. A stacked PR stays draft while its base is unmerged. The sole transition exception occurs after that base merges: post-merge reconstruction retargets and cleans the PR body, then runs `gh pr ready` exactly once before restarting inspection as a peer. Every later follow-up push uses the ready-peer path with no draft toggle.

</authority_gates>

<pr_check_wait>

Waiting for PR checks or the current-head CI review uses exactly one foreground command:

```bash
gh pr checks <pr-number> --watch --fail-fast --interval 30
```

After that command exits, immediately run the full managing inspection again before acting: PR state, check rollup, PR-level comments, formal reviews, and review-thread comments. This is the only PR-check wait path in the GitHub-PR lifecycle, applies to both Claude Code and Codex, and never runs in the background.

Forbidden waits: shell `sleep`, `gh run watch`, background keep-alives, and `until`/`while` polling. Never wrap `gh pr checks --watch` in a loop or background it. The Bash tool does not reliably reap detached subprocess trees across turns; fork-bomb-class accumulation results when those patterns are repeated.

</pr_check_wait>
<review_inspection>

Inspect all three review surfaces. Automated reviewers (and humans) may post as **formal reviews** OR as **PR-level issue comments** OR as **review-thread comments on specific lines** — checking only one or two surfaces misses feedback.

```bash
# Formal reviews + PR-level issue comments
gh pr view <pr-number> --json reviews,comments \
  --jq '{reviews: [.reviews[] | {author: .author.login, state, submittedAt}],
         comments: [.comments[] | {author: .author.login, createdAt, excerpt: .body[0:160]}]}'

# Review-thread comments tied to specific lines
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments --paginate \
  --jq '.[] | {id, node_id, author: .user.login, path, line, createdAt: .created_at, excerpt: .body[0:160]}'
```

**NEVER drop `comments` from the `gh pr view --json` argument list.** The `comments` field carries PR-level issue comments — a distinct surface from `reviews` (formal review submissions) and from `gh api repos/<owner>/<repo>/pulls/<n>/comments` (review-thread comments tied to specific lines). Dropping `comments` to "trim the JSON" silently loses that third surface; a valid `BLOCKING` or `DEBT` finding posted there is invisible to the inspection, and `MERGE_READINESS` evaluates against a partial view.

Completeness is checked per invocation. Every `gh pr view --json` invocation that participates in a management pass or re-inspection MUST include both `reviews` and `comments` in its field list, even when the same pass also runs another broader `gh pr view` command. Classify a pass by scanning each field list independently: if any participating field list omits `comments`, the PR-level issue-comment surface is missing for that pass and the inspection is incomplete; if any participating field list omits `reviews`, the formal-review surface is missing for that pass and the inspection is incomplete. A pass with one complete `reviews,comments,...` list followed by a later `reviews,...` list missing `comments` is incomplete with missing surface `comments-field`; the earlier complete call never repairs the later narrower call. Whatever field list the management pass constructs — it may add `statusCheckRollup`, `headRefOid`, `baseRefName`, `mergeable`, `mergeStateStatus`, or others for the merge-state predicates — `reviews` and `comments` remain mandatory. Construct the field list explicitly per pass; do not omit fields from an abbreviated re-creation between turns.

Compare timestamps against the most recent push. Entries after that push are re-reviews of the latest state — read them in full.

</review_inspection>
<review_classification>

Every review finding — whether produced by a reviewer (outgoing feedback) or triaged by an author (incoming feedback) — carries two dimensions: **severity** (one of two) and **category** (one of six). The taxonomy is shared so output and triage use the same vocabulary; nothing has to be translated between them.

This skill is the canonical consumer-facing taxonomy. Repositories may add local review instructions, but the default severity and category vocabulary below is complete here.

**Severity** (one of two — the reviewer's reporting label for the finding's merge-safety nature):

| Severity   | Use when                                                                                                 |
| ---------- | -------------------------------------------------------------------------------------------------------- |
| `BLOCKING` | Merge-safety defect: if deployed, the changeset would create a deterministic issue or pose a risk.       |
| `DEBT`     | Real defect that does not jeopardize merge safety: a problem the change carries, but not merge-blocking. |

Severity is the validity judgment the reviewer makes. **Disposition** — whether each `DEBT` finding is fixed in this PR or tracked out of scope — is the author's call, not the reviewer's; the reviewer carries no scope axis. A fix is **in scope** when it is bounded — a rename propagation, a cross-reference update, a mechanical change, or a fix that merely touches another file — and is fixed in the changeset; a finding is tracked out of scope only when its fix is a separate, larger concern (its own node or feature), with a recorded reason naming why it is large. Boundedness is never grounds to defer: a rename, a cross-reference, or a mechanical change is never tracked out of scope.

**A defect the changeset's own edits introduced is always in-scope and is never split out.** A claim an edit made stale, dead code a change orphaned, a cross-reference a rename broke, a spec a consolidation falsified — fixing the consequences of this change is part of this change, however many files the fix touches. "A separate, larger concern" means a node or capability that exists independently of this changeset; it is never a label applied to self-caused bounded work to end a review-convergence loop. If the only thing making a finding feel large is that fixing it would reopen the loop, it is in-scope — converge the loop, do not relabel the work to escape it.

**Handling is by validity and phase, never by severity.** Severity classifies the finding's nature for the reader; it is not a routing key. The consumer of a review validates each finding against its cited rule and the governing decisions, drops any the citation does not support, and acts on the rest by phase per `<authority_gates>`: before open (`VERIFICATION_READINESS`), apply every valid finding that belongs and split out of the changeset any whose fix is too large to belong; on the open PR (`MERGE_READINESS`), fix every valid in-scope finding the CI review surfaces, with no deferral of in-scope work — a bounded fix (a rename, a cross-reference, a mechanical change, a fix that merely touches another file) is in-scope work the changeset carries, never deferred — while a `DEBT` finding whose fix the author judges a separate, larger concern is recorded in `ISSUES.md` / `PLAN.md` with a reason naming why it is large and does not block the merge. A `BLOCKING` label does not force an action the citation does not support, and a `DEBT` label does not exempt a finding whose fix actually belongs in the changeset — validity, phase, and scope decide, and the reviewer never decides whether the change merges.

**Same-class sweep before disposition.** Treat a valid review or audit finding as evidence of a defect class. Before fixing only the cited site, inspect the touched node(s) for parallel instances with the same rule, source contract, evidence pattern, lifecycle step, or generated-source relationship. Fix all in-scope parallel instances in the same changeset, or record in the handling summary that the sweep found the cited instance isolated. Do not run another external review round after a micro-edit that only addresses one example while the defect class remains unswept.

**Cross-reviewer union and convergence.** Build one finding ledger from all current-head review surfaces and reviewers, then classify each item once. A no-findings review from the designated CI reviewer, a clean local review, a passing deterministic check, or an approved audit never cancels a valid finding from another reviewer. Multiple review rounds that keep surfacing valid variants in the same area are not reviewer noise and not an operator decision point; they prove the prior fix or sweep was too narrow. Treat the next valid variant as the same defect class until the underlying lifecycle contract is repaired and a new review round finds no valid in-scope variant. "Not wired into production yet" and "deferred next slice" are not dispositions for code in the diff — if the changed diff carries the defect and the finding is valid in scope, fix it in the changeset before merge.

**Category** (one of six), grouped by three axes:

*What the code does vs. what it is supposed to do*

- `consistency` — disagreement across layers (decisions / PDR / ADR <-> spec <-> tests <-> implementation). Surface the disagreement; do not judge which side is right.
- `security` — confidentiality, integrity, availability.
- `performance` — unbounded loops, hot-path allocations, O(n²) traversals where O(n) suffices, synchronous I/O on async paths, and similar pessimisations that change the changeset's runtime characteristics under realistic load.

*How we know it does what it is supposed to do*

- `evidence` — inadequate coverage of declared assertions by tests or evals; unmaintainable tests (literals, magic numbers, test-owned constants, duplication); evals that no longer exercise the assertions they claim to.

*How it does what it is supposed to do*

- `standards` — adherence to CLAUDE.md and the rules declared in standards skills (naming conventions, command tokens, file structure, language idioms).
- `architecture` — violation of structural principles declared by ADRs or PDRs (layer boundaries, separation of concerns, dependency directions, module-shape rules). A finding is an architecture one when the structure itself is at odds with a governance principle, even if every layer is internally consistent.

**Finding labels.** Both `BLOCKING` and `DEBT` require an action in this PR and use `Reference:` + `Evidence:` + `Required:`.

**No findings: say so directly.** When the changeset has no `BLOCKING` or `DEBT` findings, post a one-line comment saying so. NEVER invent lower-priority findings to prove the review happened.

**Findings only — never open questions, never commentary.** A reviewer with a question frames it as a finding (e.g., "Evidence: cannot verify X from the changeset; if assumption Y holds, this breaks Z because …") rather than asking a question that waits for an answer. Questions add CI roundtrips a single-pass review cannot recover from. Praise, observations, and commentary that do not constitute findings are noise — omit them.

**Forbidden taxonomies.** Severity-rank labels MUST NOT replace the two severities — no `P0` / `P1` / `P2` / `P3`, no `critical` / `high` / `medium` / `low`, no `minor` / `nit` headings. A third scope-shaped severity (`FOLLOW-UP`) MUST NOT reappear — scope is the author's disposition, not a reviewer severity. Risk words may appear inside rationale only when they add concrete evidence, never as a finding's primary label. Legacy class labels `NEEDS-ANSWER` and `NOTE` are forbidden — open questions are reframed as findings; commentary is omitted.

Comment format examples:

```text
### BLOCKING [consistency]: path/to/file:42
Reference: <quote the standard from CLAUDE.md, skills, governance from decisions (PDR/ADR), or assertion from specs>
Evidence: <quote the diff or behavior and explain the disagreement between layers>
Required: <concrete change>
```

```text
### DEBT [standards]: path/to/file:97
Reference: <quote the standard from CLAUDE.md, skills, governance from decisions (PDR/ADR), or assertion from specs>
Evidence: <quote the diff or behavior and explain how it violates the standard>
Required: <concrete change>
```

</review_classification>

<auditor_verdicts>

Local auditor agents — `test-evidence-auditor`, `eval-evidence-auditor`, `adr-auditor`, `pdr-auditor`, `spec-auditor`, and `implementation-auditor` — emit structured findings for the slice they inspect. Language-specific audit concerns are composed through the installed `audit-{lang}-{code|tests|architecture}` skills, not through language-specific auditor agents.

**Verdict handling.** A `REJECTED` overall verdict, an `UNKNOWN` overall verdict, a `FAIL` row, an `UNKNOWN` row, or a `REJECT` finding is in-slice unresolved work, identical in handling to a valid `BLOCKING` or `DEBT` finding in `<review_classification>`: fix the bug or resolve the audit uncertainty, re-run the auditor, repeat until clean. `APPROVED` means the auditor found nothing in scope. "Capture in `ISSUES.md`" is NOT an option for rejected or unknown in-slice audit work on a slice currently under review — `ISSUES.md` is for items outside the slice (a known gap in an unrelated module, a tracking note for future enablement), never for in-slice bugs or audit uncertainty the auditor surfaced.

**Why auditor verdicts are authoritative.** Auditor agents invoke the same audit skills the operator would invoke directly; each verdict is the audit skill's structured output for its specific concern, not a separate discretionary decision. CI green and reviewer-bot approval do not erase an auditor REJECT because audit and review inspect different concerns: test evidence, PDR quality, architectural fitness, or language-specific code quality.

**Loop semantics.** When an invoked workflow surfaces auditor verdicts while preparing or repairing a PR, handle every `REJECTED` or `UNKNOWN` overall verdict, `FAIL` or `UNKNOWN` row, and `REJECT` finding as in-slice work under `<review_classification>`: fix it or resolve the audit uncertainty, re-run the auditor, and repeat until no rejected or unknown in-slice audit work remains. `APPROVED` means the auditor found nothing in its scope. Auditor findings do not add a fourth PR-lifecycle gate and do not change the `MERGE_READINESS` predicate set in `<authority_gates>`.

</auditor_verdicts>

</readiness_and_review>
