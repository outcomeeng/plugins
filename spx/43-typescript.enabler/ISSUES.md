# TypeScript Skill Issues

## Legacy XML Structure Cleanup

Observed during the TypeScript test-data policy cleanup.

Several TypeScript `SKILL.md` files still mix XML sections with markdown headings inside the skill body. The skill authoring standard requires pure XML structure in `SKILL.md`, with markdown headings reserved for generated report templates or reference content where appropriate.

Known examples:

- `testing-typescript/SKILL.md` uses markdown headings inside `<write_mode_workflow>`, `<literal_reuse_remediation>`, and `<fix_mode_workflow>`.
- `coding-typescript/SKILL.md` uses markdown headings inside `<mandatory_code_patterns>` and discovery sections.
- `standardizing-typescript-architecture/SKILL.md` uses markdown headings inside architecture-standard sections.
- Some TypeScript reference files still use the older markdown-heading style. If the cleanup expands to references, make the format decision explicitly instead of migrating one file at a time by accident.

Revisit condition: run a focused TypeScript skill-structure cleanup after the test-data policy and level-document rename changes are reviewed.

## Methodology Restatement Inside TypeScript Standardizing Skills

The standardizing TypeScript skills (`standardizing-typescript`, `standardizing-typescript-architecture`, `standardizing-typescript-tests`) currently restate Spec Tree fundamentals that belong to the methodology layer rather than to TypeScript:

- `standardizing-typescript-architecture/SKILL.md` includes `<adr_sections>` and `<atemporal_voice>` sections that duplicate `spx/21-spec-tree.enabler/spec-tree.md` and `plugins/spec-tree/skills/understanding/references/durable-map.md`.
- `<anti_patterns>` in the same skill mixes methodology-level prohibitions (no Status field, no Testing Strategy section) with TypeScript-specific anti-patterns.

The TypeScript specs under `spx/43-typescript.enabler/25-typescript-standards.enabler/` cover only TypeScript-specific concerns. The skill content remains broader so that downstream agents can be evaluated for both Spec Tree adherence and TypeScript-plugin conformance.

Resolution path: factor the Spec Tree fundamentals into a marketplace-wide PDR (or extend an existing one) so the standardizing-language skills can reference it instead of restating it. Until then, evaluations of these skills must check both layers.

## `auditing-typescript` Spot Defects

Three small fixes against `plugins/typescript/skills/auditing-typescript/SKILL.md`, to land with the audit-skill alignment work rather than with the eval-harness slice.

- Line 25: typo "Typecsript" → "TypeScript".
- Line 77: broken reference `${CLAUDE_SKILL_DIR}/rules/` — the directory does not exist; the skill ships `references/` only. Either correct the path to `references/` or create `rules/` if a separate location is intended.
- Line 33: `quick_start` invokes `/testing` and `/testing-typescript`; these are test-evidence skills, but `auditing-typescript` explicitly delegates test concerns to `auditing-typescript-tests` elsewhere. Remove the test-skill invocations from `quick_start`.
