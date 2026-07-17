# PLAN — TypeScript test standards follow-ups

## Why

The TypeScript test-standard skill teaches several concerns that still need dedicated child nodes, and one shared methodology reference still uses the legacy Markdown-heading structure.

## Steps

1. Convert `src/plugins/spec-tree/skills/test/references/methodology.md` from Markdown headings to semantic XML sections as a focused reference-structure cleanup.
2. Use `/decompose` and `/author` to add TypeScript-specific child nodes for file naming, level tooling, property-based testing, and Playwright request context.
3. Move marketplace-wide methodology restatements from TypeScript-specific standards into shared Spec Tree guidance or cite the canonical source directly.
4. Gate with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check`, and `typescript:audit-typescript-tests`.
