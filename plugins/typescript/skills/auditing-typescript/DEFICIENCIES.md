# Deficiencies: auditing-typescript

Insights from the `auditing-typescript-tests` rewrite applied to this skill.

## D1: Phase 7 (Commit) doesn't belong in an audit

The skill includes Phase 7: "Report and Commit (APPROVED Only)". An audit agent should produce a verdict, not commit code. Committing is a side effect that couples the audit to the workflow. The calling context (e.g., `/coding` skill or the user) should decide what happens after APPROVED.

**Action:** Remove Phase 7. End at verdict + report.

## D2: Test verification section duplicates auditing-typescript-tests

The `<test_verification>` section (lines 77-119) does a shallow version of what `auditing-typescript-tests` now does comprehensively with the 4-property evidence model. Having both creates confusion about who owns the test audit.

**Action:** Replace `<test_verification>` with a single directive: "Test evidence quality is audited by `/auditing-typescript-tests`. This skill audits implementation code, not test code. If test files are in scope, delegate to `/auditing-typescript-tests`."

## D3: Hard 80% coverage conflicts with evidence model

Phase 2 has a hard "Coverage ≥80% = PASS, <80% = REJECTED" threshold. The evidence model in `auditing-tests` measures coverage as a **delta** (does this test increase coverage of assertion-relevant files?), not an absolute percentage. A codebase at 75% with all assertions covered has more evidentiary value than one at 85% where the coverage comes from trivial paths.

**Action:** Replace the absolute threshold with delta-based coverage reasoning, or defer coverage judgment to `/auditing-typescript-tests` entirely.

## D4: No failure modes section

The test audit skills include failure modes — concrete stories of how past auditors failed (distracted by code quality, accepted tautological tests, missed mocking). These are the most effective teaching tool for agents. This skill has none.

**Candidates for failure modes:**

- **Approved code that passed linters but had a design flaw** — reviewer trusted Phase 1 and skimmed Phase 3
- **Rejected code for a false positive** — reviewer flagged a dead parameter that was required by a Protocol interface contract
- **Missed a mocking violation hidden behind DI** — `vi.fn()` passed as a dep parameter looks like DI but is still a mock
- **Distracted by style while missing a logic bug** — reviewer spent time on naming while a branch condition was inverted

## D5: Phase 3 mixes comprehension with mechanical detection

Phase 3 ("Critical Code Comprehension") contains both:

- **Genuine comprehension** (3.1 predict/verify/investigate) — this is the core value
- **Pattern matching** (3.2 near-duplicate blocks, redundant operations, reimplemented stdlib) — these are closer to linting concerns

The `auditing-tests` rewrite explicitly separates evidence quality from code quality ("NO MECHANICAL DETECTION"). The same principle applies here: the auditor's value is in understanding design intent, not in finding duplicated code blocks that a tool could find.

**Action:** Split Phase 3 into comprehension (what the auditor does) and code quality patterns (what belongs in `/standardizing-typescript` or a linter rule). Keep 3.1 and 3.3 as the core. Move 3.2 patterns to a reference that the auditor checks only after comprehension is complete.

## D6: No structured verdict format per concern

The test audit skills produce a per-assertion table showing which property failed. This skill's output format (lines 393-446) is a flat report with no structured per-concern breakdown. An agent running this audit can't easily extract which specific concern caused the rejection.

**Action:** Add a structured verdict table, e.g.:

```text
| # | File        | Concern            | Verdict | Detail                  |
|---|-------------|--------------------|---------|-------------------------|
| 1 | config.ts   | Design: IO/logic   | REJECT  | Computation tangled     |
| 2 | parser.ts   | Design: SRP        | PASS    | Single responsibility   |
| 3 | —           | ADR compliance     | PASS    | All constraints met     |
```

## D7: `allowed-tools` includes Write and Edit

An audit skill should be read-only (except for running linters/tests via Bash). The current `allowed-tools: Read, Bash, Glob, Grep, Write, Edit` means the auditor can modify code. This conflicts with the audit agent model where the auditor produces a verdict, not changes.

**Action:** Remove `Write` and `Edit` from allowed-tools. The Phase 7 removal (D1) eliminates the need for write access.

## D8: No harness/import guidance for code under audit

The test audit skills now have detailed import classification tables (production imports, test harness imports, path aliases, barrel re-exports). The code audit skill has no equivalent guidance for how to evaluate import structure in the code under review — it just has a rejection trigger for "Deep relative import" without the nuanced classification.

**Action:** Add import evaluation guidance consistent with the coupling taxonomy in `auditing-typescript-tests`, so both skills use the same vocabulary.

## Priority order

1. **D1** (remove commit phase) — prerequisite for agent independence
2. **D7** (remove write tools) — prerequisite for agent independence
3. **D2** (remove test duplication) — eliminates confusion with test audit
4. **D4** (add failure modes) — highest impact on audit quality
5. **D5** (separate comprehension from detection) — clarifies the auditor's role
6. **D6** (structured verdict) — enables machine-readable output
7. **D3** (coverage model) — aligns with evidence model
8. **D8** (import guidance) — consistency with test audit
