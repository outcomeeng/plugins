<!-- Prompt template for the review-readiness eval.
     Generated from dist/claude/spec-tree/skills/open-pr/SKILL.md section verification_readiness_decision.
     The harness substitutes case input JSON before sending the prompt. -->

Use the producer section below as the authority for `/open-pr` `VERIFICATION_READINESS` behavior. Classify whether `/open-pr` may open a pull request ready for review at the opening mutation point.

Producer section:

```text
<step name="verification_readiness_decision">

**Step 3 — GATE: Evaluate `VERIFICATION_READINESS`.** Per /merging-standards `<authority_gates>`, the PR opens ready only when `VERIFICATION_READINESS` holds — all predicates below.

*(a) Deterministic verification.* Run the project's local deterministic verification per /merging-standards `<local_deterministic_scope>` — validation and testing for the touched scope, escalating only when the overlay or risk evidence requires a wider local run. Capture verbose stdout/stderr in a temporary log path and inspect only the exit status, summary, and failing sections. It must report success; fix failures and re-run until green.

*(b) Evidence-auditor predicates.* Dispatch every evidence auditor /merging-standards `<authority_gates>` requires for the diff: `test-evidence-auditor` for changed `[test]` assertions, linked tests, or imported test-infrastructure artifacts; `eval-evidence-auditor` for changed `[eval]` assertions, eval artifacts, or producer artifacts for eval-backed assertions. Handle rejected, failing, or unknown verdicts per /merging-standards `<auditor_verdicts>`, re-running deterministic verification and the relevant auditor until the evidence predicate is clean.

*(c) Local review to convergence.* Run the `changes-reviewer` agent on the working diff — it runs in an isolated context, so the verdict is not biased by everything the operator's main context has been doing. Invoke it per /merging-standards `<local_review_invocation>`: let it resolve its own scope — the worktree it runs in and the working diff — with no interpretive scope, no severity pre-filter, and no instruction on what to emphasize; the reviewer reads the repository's own instructions and the shared taxonomy itself. The reviewer emits findings only (no decision/verdict); process its findings by **validity and phase** per /merging-standards `<review_classification>` — this is the before-open phase:

- **Validate each finding** against its cited rule, the product-local / language / spec-tree governance, and the PDR/ADR decisions. Drop any finding the citation does not support.
- **Apply every valid finding that belongs.** Treat each valid finding as defect-class evidence: sweep the touched node(s) for parallel instances with the same rule, source contract, evidence pattern, lifecycle step, or generated-source relationship. Fix the cited site and every in-scope parallel instance, commit via /commit-changes, re-invoke the reviewer, and repeat. When a valid finding's fix is too large to belong in this changeset, **split it out** — the work leaves the diff, recorded in the owning node's `ISSUES.md` or `PLAN.md` — instead of applying it here.
- **Converged** when the working diff carries no unapplied valid finding that belongs. Severity never decides; validity and the before-open phase do.

The iteration accumulates commits on the branch — the eventual push at Step 4 sends them all. After every iteration that commits, re-run /merging-standards `<branch_hygiene>`, re-run local deterministic verification, re-run required evidence-auditor predicates for touched evidence surfaces, and re-run the local review — all `VERIFICATION_READINESS` predicates must hold together on the exact tree the push publishes, so loop until a single tree passes all predicates (the joint fixpoint of /manage-pr Step 6: a verification-driven fix is a diff the review has not seen, an evidence-audit fix changes the evidence surface, and a review-driven fix is a tree verification has not covered). `VERIFICATION_READINESS` holds only when (a), (b), and (c) hold; only then proceed. The before-open pass is the strictest point in the lifecycle: every valid finding that belongs is applied here and only split-out work survives to the CI review, which on the open PR must show no unresolved valid `BLOCKING` or `DEBT` finding.

</step>
```

Case input:

```json
{input_json}
```

Return exactly one JSON object with these fields:

- `open_decision`: `"OPEN_READY"` or `"WITHHOLD"`.
- `blocking_predicate`: `"deterministic-verification"`, `"evidence-auditor"`, `"local-review"`, or `"none"`.
- `ready_for_review`: `true` or `false`.

Do not include markdown, prose, commentary, caveats, or questions.
