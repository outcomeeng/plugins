# PLAN — TypeScript test standards follow-ups

## Why

`docs/cross-language-test-standards-drift-audit.md` records TypeScript test-standard follow-ups around skill size, test-infrastructure wording, and missing child nodes for the standards that the skill already teaches.

## Steps

1. Move one compact topic out of `typescript-test-standards/SKILL.md` into a reference file so the overview stays under the `/skill-standards` line-count target.
2. Replace "test-owned code" wording with the PDR vocabulary for production-grade test infrastructure under `testing/`, path-mapped to `@testing/`.
3. Use `/decomposing` and `/authoring` to add TypeScript-specific child nodes for file naming, level tooling, property-based testing, and Playwright request context.
4. Move marketplace-wide methodology restatements from TypeScript-specific standards into shared Spec Tree guidance or cite the canonical source directly.
5. Gate with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check`, and `typescript:audit-typescript-tests`.

## Revisit condition

Pick this up after the `reviewing-changes` vocabulary boundary is clarified, so TypeScript standards work is reviewed with the corrected distinction between reviewing and auditing.
