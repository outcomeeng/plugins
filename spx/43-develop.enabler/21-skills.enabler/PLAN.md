# Plan: objective-shape follow-ups

Both items follow the marketplace-wide objective reframe shipped in PRs #317
(refine `<objective_shape>` to a one-sentence output rule + `objective_bloat`
flag + common-shapes-by-family) and #319 (the brevity follow-up).

## 1. Make the skill-auditor deterministic on the code-auditor verdict form

`develop:skill-auditor` returns non-deterministic verdicts on the code-auditor
objective shape. In one audit batch the identical objective —
"A verdict on X implementation code — APPROVED, or REJECTED with each finding
naming the design flaw, the violated rule, and the evidence." — PASSED for
`audit-python` and FAILED for `audit-typescript` (`auditor_skeleton_violation`:
missing outcome shape / finding categories). The `<objective_shape>` rule and
`skill-standards` `references/auditor-skeleton.md` `<objective_examples>`
underspecify the **code/test auditor** verdict objective, distinct from the
artifact-auditor form #314 pinned for `audit-adr`/`audit-pdr`/`audit-specs`/
`audit-tests`.

Fix: pin the canonical code-auditor / test-auditor objective form in
`auditor-skeleton.md` (or the `<objective_shape>` family-shapes) — decide
explicitly whether the verdict objective must enumerate `APPROVED`/`REJECTED`
plus finding fields and categories, or whether the shorter
"A verdict on X — &lt;what it catches&gt;" form is acceptable — so `/audit-skills`
yields a stable verdict on these skills.

## 2. Audit the residual reframed objectives

A representative ~12-skill sample was run through `develop:skill-auditor` during
#319; the remainder were pattern-applied but not individually audited:
`rust-standards`, `rust-test-standards`, the three `*-architecture-standards`,
`architect-typescript`, `test-rust`, `create-subagents`, `interview`. Run the
auditor over each and fix any stragglers (expected to parallel forms that
already passed).
