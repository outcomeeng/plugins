# Issues: Auditing Enabler

## 1. Audit-skill `<success_criteria>` restate workflow steps instead of verdict-soundness properties

The `<success_criteria>` blocks in `audit-tests`, `audit-python-tests`, `audit-typescript-tests`,
and `audit-rust-tests` list workflow steps ("Gate 1 complete: every assertion evaluated",
"Gate 2 complete", "Verdict issued") rather than the verdict-soundness properties the auditor
skeleton (`develop:skill-standards` `references/auditor-skeleton.md` `<success_criteria_shape>`)
requires: every applicable rule judged with none skipped, overall determination stated, each finding
falsifiable, the same input yields the same verdict.

## 2. Language test-audit `<verdict_format>` delegate the schema to `/audit-tests`

`audit-typescript-tests` (and the sibling language skills) state `<verdict_format>` as
"Follow `<verdict_format>` in `/audit-tests`" plus language-specific finding IDs, rather than
carrying the row/field schema inline. This is intentional composition — the base `audit-tests`
carries the canonical schema and the language skills add IDs — but the skill auditor flags it
against the standalone-auditor skeleton rule.

## Why tracked, not fixed here

Both are pre-existing patterns across the whole audit-skill family, independent of the
no-deterministic-verification change that surfaced them. Fixing them is a separate skill-quality
refactor of the audit-skill `<success_criteria>` convention and the composed-skill verdict-format
contract — touching skills this change does not otherwise edit — not part of removing deterministic
verification from the test-evidence audits.
