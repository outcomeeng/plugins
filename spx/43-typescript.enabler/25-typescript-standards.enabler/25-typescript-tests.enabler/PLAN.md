# PLAN — TypeScript test standards follow-ups

## Why

The TypeScript test-standard skill teaches several concerns that still need dedicated child nodes, and one shared methodology reference still uses the legacy Markdown-heading structure.

## Steps

1. Reduce `src/plugins/typescript/skills/typescript-test-standards/SKILL.md` below 500 lines by moving one compact topic into a cited reference.
2. Replace "test-owned code" with production-grade test infrastructure under `testing/`, path-mapped to `@testing/`.
3. Convert `src/plugins/spec-tree/skills/test/references/methodology.md` from Markdown headings to semantic XML sections as a focused reference-structure cleanup.
4. Use `/decompose` and `/author` to add TypeScript-specific child nodes for file naming, level tooling, property-based testing, and Playwright request context.
5. Move marketplace-wide methodology restatements from TypeScript-specific standards into shared Spec Tree guidance or cite the canonical source directly.
6. Gate with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check`, and `typescript:audit-typescript-tests`.

## Revisit condition

Resume during the next TypeScript test-standards maintenance changeset.
