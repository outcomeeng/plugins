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

## Seam-subtraction reduction (grounded by the ancestor delegation change)

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` is now the single language-neutral superset of the seam rules — the exact union of the three languages' rules, with `[eval]` evidence on predicate-ownership and oracle-independence — and requires a language test-standard spec node to cite the ancestor and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` and declare only its language delta, never restating or weakening the seam rules. Rust and Python were reduced to that delta-only form in the same changeset that built the superset; TypeScript is the first-affected lower spec still pending, grounded here per the decision→spec-alignment rule.

Pending: reduce `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/typescript-tests.md` and its decomposed test-standards children to cite `.../test-verification.md` and `.../15-test-infrastructure.pdr.md` and keep only the TypeScript delta — the `expect`/matcher assertion API, `const`/`let`/destructuring bindings, `fast-check` generators, the `@testing/` path-mapped test-infrastructure home, and Vitest runner specifics — removing the restated seam rules. Sequenced immediately after the ancestor change lands, on branch `spec/ts-seam-concept-parity`; fold the `#474` source-testability narrowing in on retarget.
