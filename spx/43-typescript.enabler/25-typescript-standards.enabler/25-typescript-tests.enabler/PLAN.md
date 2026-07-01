# PLAN — TypeScript test standards follow-ups

## Why

`docs/cross-language-test-standards-drift-audit.md` records TypeScript test-standard follow-ups around skill size, test-infrastructure wording, and missing child nodes for the standards that the skill already teaches.

## Steps

1. Move one compact topic out of `typescript-test-standards/SKILL.md` into a reference file so the overview stays under the `/skill-standards` line-count target.
2. Audit remaining legacy wording against the PDR vocabulary for production-grade test infrastructure under `testing/`, path-mapped to `@testing/`.
3. Convert `src/plugins/spec-tree/skills/test/references/methodology.md` from Markdown headings to semantic XML sections as a focused reference-structure cleanup.
4. Use `/decompose` and `/author` to add TypeScript-specific child nodes for file naming, level tooling, property-based testing, and Playwright request context.
5. Move marketplace-wide methodology restatements from TypeScript-specific standards into shared Spec Tree guidance or cite the canonical source directly.
6. Gate with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check`, and `typescript:audit-typescript-tests`.

## Revisit condition

Pick this up after the `review-changes` vocabulary boundary is clarified, so TypeScript standards work is reviewed with the corrected distinction between review and audit.
