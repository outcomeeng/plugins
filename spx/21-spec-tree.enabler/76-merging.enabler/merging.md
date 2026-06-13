# Merging

PROVIDES the transport-neutral merging policy — the three authority gates and the finding-disposition rule — and the `/merge` transport dispatcher
SO THAT every product that installs the spec-tree plugin
CAN drive a changeset from review-ready to merge under one policy, routed to the project's selected transport (a GitHub pull request or a direct push to trunk), per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given a production-relevant change (per the project's recognition mechanism) that the operator has not approved, when `MERGE_READINESS` otherwise holds, then the merging flow withholds the merge and emits an explicit-approval action token; given a non-production-relevant change or operator approval, then it executes the merge ([eval](evals/production-readiness/eval.toml))
- Given a required check's `statusCheckRollup` status and conclusion, when the gate classifies it, then it is terminal-green only when terminal (`status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}`) and successful (`conclusion == SUCCESS` or `state == SUCCESS`); a `SKIPPED`, `NEUTRAL`, `FAILURE`, `CANCELLED`, `TIMED_OUT`, still-running, or absent required check is not terminal-green and withholds `MERGE_READINESS` ([eval](evals/terminal-green/eval.toml))
- Given an auditor verdict surfaces while the merging flow drives review feedback, when the overall verdict is `REJECTED` or `UNKNOWN`, a row status is `FAIL` or `UNKNOWN`, or a finding verdict is `REJECT`, then the flow treats the cited issue or audit uncertainty as in-slice unresolved work to fix or resolve before merge rather than deferred `ISSUES.md` / `PLAN.md` work ([eval](evals/auditor-verdict-handling/eval.toml))

### Conformance

- The `/merge` dispatcher conforms to portable-skill packaging — a `SKILL.md` under `plugins/spec-tree/skills/merge/`, user-invocable, shipped as a skill rather than a command, so it activates on both runtimes, per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_merge.conformance.l1.py))
- The `/merge` dispatcher classifies the changeset through the canonical `changeset_scope` primitives (`detect_base_ref` for the base ref, `branch_scope` for the committed diff) via a co-located `scripts/classify_changeset.py`, never re-deriving the base ref or diff range inline in the skill body, per `spx/21-spec-tree.enabler/17-auditing.adr.md` ([test](tests/test_classify_changeset.scenario.l1.py))

### Compliance

- ALWAYS: `/merge` reads the changeset and the `spx/local/merging.md` transport selector, selects exactly one transport per the precedence (overlay-declared, else coordination-note-only → direct-push, else GitHub-PR), and presents a proposal before any direct-push mutation ([audit])
- ALWAYS: `/merge` delegates the GitHub-PR transport to `/github-pr` (which owns the commit → open → manage → close protocols) and drives the direct-push transport through `/committing-changes` and the `changes-reviewer` review, never reimplementing a transport's internal protocol inline ([audit])

- ALWAYS: the merging skills expose exactly three gates — `REVIEW_READINESS`, `MERGE_READINESS`, `PRODUCTION_READINESS` — named with the single word "gate"; every condition a gate reads is a predicate, never a gate, per `spx/15-merging.pdr.md` ([review])
- ALWAYS: the merging policy — the three gates and the finding-disposition rule — is transport-neutral, and `/merge` selects the transport from `spx/local/merging.md`: a coordination-note-only changeset routes to the direct-push transport, an overlay-declared transport is honored, else the GitHub-PR transport is the default; `/merge` then delegates to that transport's skills, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: each transport binds the gate predicates — which review attests `MERGE_READINESS`, which checks are required, how `REVIEW_READINESS` publishes the changeset — without adding, removing, or reordering a gate or changing the disposition rule, per `spx/15-merging.pdr.md` ([review])
- ALWAYS: `MERGE_READINESS` and `PRODUCTION_READINESS` are decidable from observable state — an independent reader reaches the same verdict — and carry no time-based settle, per `spx/15-merging.pdr.md` ([review])
- ALWAYS: the agent acts on each review finding by validity, phase, and scope — at `REVIEW_READINESS` applying every valid finding that belongs and splitting out only a fix too large to belong, at `MERGE_READINESS` fixing every valid in-scope finding and re-publishing — and a bounded fix (a rename propagation, a cross-reference update, a mechanical change, or a fix that merely touches another file) is in scope and fixed in the changeset; a `DEBT` finding is deferred only when its fix is a genuinely separate, larger concern recorded in `ISSUES.md` / `PLAN.md` with a reason naming why it is large, per `spx/15-merging.pdr.md` ([review])
- NEVER: relabel a defect the changeset's own edits introduced — a stale claim, dead code, a broken cross-reference, a falsified spec — as a genuinely separate, larger concern to escape a review-convergence loop; a self-caused defect is in scope however many files its fix touches, and a genuinely separate concern is one that exists independently of this changeset, per `spx/15-merging.pdr.md` ([review])
- ALWAYS: an auditor verdict surfacing while the merging flow drives review feedback — an overall `REJECTED` or `UNKNOWN` verdict, a row `FAIL` or `UNKNOWN`, or a finding `REJECT` — is in-slice unresolved work the flow fixes or resolves before merge, never deferred `ISSUES.md` / `PLAN.md` work, per `spx/15-audit-verdict-format.pdr.md` and `spx/15-merging.pdr.md` ([review])
- ALWAYS: the merging skills re-establish both `REVIEW_READINESS` predicates before every push — opening and follow-up — running deterministic verification and the local `changes-reviewer` review on the diff that push would publish, per `spx/15-merging.pdr.md` ([review])
- ALWAYS: the merging skills rebase a behind-base branch automatically from observable git state and never ask the operator whether to rebase — the only base-sync operator touch-point is a rebase conflict the agent cannot resolve autonomously, per `spx/15-merging.pdr.md` ([review])
- ALWAYS: the merging skills invoke the local `changes-reviewer` review at parity with the integration-time reviewer — passing only the repository/worktree and the diff range, never a caller-supplied interpretive scope, severity pre-filter, or emphasis steering — per `spx/15-merging.pdr.md` ([review])
- NEVER: gate any of the three gates on a review finding's severity label, or use a time-based settle as a `MERGE_READINESS` predicate — validity, phase, and scope decide; a `DEBT` finding the author tracks out of scope with a recorded reason is non-blocking because of scope, not its label, per `spx/15-merging.pdr.md` ([review])
- NEVER: treat an agent-inferred "the work looks done" as a gate, or satisfy a gate's review predicate by invoking a review skill in the working conversation rather than the `changes-reviewer` agent — a gate's predicates are observable or deterministically computed state, per `spx/15-merging.pdr.md` ([review])
