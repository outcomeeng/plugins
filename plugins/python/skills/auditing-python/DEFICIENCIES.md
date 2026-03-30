# Deficiencies: auditing-python

Insights from the `auditing-python-tests` rewrite applied to this skill. Nearly identical to `auditing-typescript` deficiencies — the two skills are structural mirrors.

## D1: Phase 7 (Commit) doesn't belong in an audit

The skill includes Phase 7: "Report and Commit (APPROVED Only)". An audit agent should produce a verdict, not commit code. Committing is a side effect that couples the audit to the workflow.

**Action:** Remove Phase 7. End at verdict + report.

## D2: Test verification section duplicates auditing-python-tests

The `<test_verification>` section (lines 77-114) does a shallow version of what `auditing-python-tests` now does with the 4-property evidence model (coupling, falsifiability, alignment, coverage). Having both creates confusion about who owns the test audit.

**Action:** Replace `<test_verification>` with a delegation directive: "Test evidence quality is audited by `/auditing-python-tests`. This skill audits implementation code, not test code."

## D3: Hard 80% coverage conflicts with evidence model

Phase 2 has a hard "Coverage ≥80% = PASS, <80% = REJECTED" threshold. The evidence model measures coverage as a **delta**, not an absolute. A module at 75% with all spec assertions covered has more value than one at 85% where coverage comes from trivial paths.

**Action:** Replace absolute threshold with delta-based reasoning, or defer coverage judgment to `/auditing-python-tests`.

## D4: No failure modes section

The test audit skills include concrete stories of how auditors failed. This skill has none.

**Candidates for failure modes:**

- **Approved code that passed ruff+mypy but had a design flaw** — reviewer trusted Phase 1 and skimmed Phase 3
- **Rejected code for a false positive** — reviewer flagged a dead parameter required by a Protocol contract
- **Missed mocking hidden behind DI** — `lambda cmd: (0, "", "")` passed as a dep looks like DI but is a stub without exception justification
- **Confused `sys.path` manipulation with a real import** — reviewer missed that a test fixture inserted a fake module into sys.path

## D5: Phase 3 mixes comprehension with mechanical detection

Phase 3.2 contains pattern-matching concerns (near-duplicate blocks, redundant operations, reimplemented stdlib) that are closer to linting than comprehension. The `auditing-tests` rewrite separates evidence quality from code quality ("NO MECHANICAL DETECTION").

**Action:** Keep 3.1 (predict/verify/investigate) and 3.3 (design questions) as the core. Move 3.2 patterns to a reference appendix or to `/standardizing-python`.

## D6: No structured verdict format per concern

The output format is a flat report. An agent can't easily extract which concern caused the rejection.

**Action:** Add a structured per-concern verdict table matching the pattern from `auditing-python-tests`.

## D7: `allowed-tools` includes Write and Edit

An audit agent should be read-only. `Write` and `Edit` in allowed-tools means the auditor can modify code, which violates audit independence.

**Action:** Remove `Write` and `Edit`. The Phase 7 removal (D1) eliminates the need.

## D8: No import/harness classification guidance

The test audit skill has detailed import classification (production via `product.*`, test harness via `product_testing.*`, `TYPE_CHECKING` blocks, `__init__.py` re-exports). The code audit skill has a rejection trigger for "Deep relative import" and "sys.path manipulation" but no nuanced classification.

**Action:** Add import evaluation guidance consistent with `auditing-python-tests` coupling taxonomy.

## D9: Python-specific — `src.*` examples should use `product.*`

If the code audit skill contains examples, they should use `product.*` / `product_testing.*` to match the convention established in `auditing-python-tests`.

**Action:** Verify and update any examples when rewriting.

## Priority order

1. **D1** (remove commit phase) — prerequisite for agent independence
2. **D7** (remove write tools) — prerequisite for agent independence
3. **D2** (remove test duplication) — eliminates confusion with test audit
4. **D4** (add failure modes) — highest impact on audit quality
5. **D5** (separate comprehension from detection) — clarifies the auditor's role
6. **D6** (structured verdict) — enables machine-readable output
7. **D3** (coverage model) — aligns with evidence model
8. **D8** (import guidance) — consistency with test audit
9. **D9** (example naming) — convention alignment
