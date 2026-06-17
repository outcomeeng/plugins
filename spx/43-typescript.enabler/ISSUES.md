# TypeScript Skill Issues

## Legacy XML Structure Cleanup

Observed during the TypeScript test-data policy cleanup.

Several TypeScript `SKILL.md` files still mix XML sections with markdown headings inside the skill body. The skill authoring standard requires pure XML structure in `SKILL.md`, with markdown headings reserved for generated report templates or reference content where appropriate.

Known examples:

- `test-typescript/SKILL.md` uses markdown headings inside `<write_mode_workflow>`, `<literal_reuse_remediation>`, and `<fix_mode_workflow>`.
- `code-typescript/SKILL.md` uses markdown headings inside `<mandatory_code_patterns>` and discovery sections.
- `typescript-architecture-standards/SKILL.md` uses markdown headings inside architecture-standard sections.
- Some TypeScript reference files still use the older markdown-heading style. If the cleanup expands to references, make the format decision explicitly instead of migrating one file at a time by accident.

Revisit condition: run a focused TypeScript skill-structure cleanup after the test-data policy and level-document rename changes are reviewed.

## Methodology Restatement Inside TypeScript Standards Skills

The TypeScript standards skills (`typescript-standards`, `typescript-architecture-standards`, `typescript-test-standards`) currently restate Spec Tree fundamentals that belong to the methodology layer rather than to TypeScript:

- `typescript-architecture-standards/SKILL.md` includes `<adr_sections>` and `<atemporal_voice>` sections that duplicate `spx/21-spec-tree.enabler/spec-tree.md` and `plugins/spec-tree/skills/understand/references/durable-map.md`.
- `<anti_patterns>` in the same skill mixes methodology-level prohibitions (no Status field, no Testing Strategy section) with TypeScript-specific anti-patterns.

The TypeScript specs under `spx/43-typescript.enabler/25-typescript-standards.enabler/` cover only TypeScript-specific concerns. The skill content remains broader so that downstream agents can be evaluated for both Spec Tree adherence and TypeScript-plugin conformance.

Resolution path: factor the Spec Tree fundamentals into a marketplace-wide PDR (or extend an existing one) so the language-standards skills can reference it instead of restating it. Until then, evaluations of these skills must check both layers.

## `audit-typescript` Spot Defects

Three small fixes against `plugins/typescript/skills/audit-typescript/SKILL.md`, to land with the audit-skill alignment work rather than with the eval-harness slice.

- Line 77: broken reference `${CLAUDE_SKILL_DIR}/rules/` — the directory does not exist; the skill ships `references/` only. Either correct the path to `references/` or create `rules/` if a separate location is intended.
- Line 33: `quick_start` invokes `/test` and `/test-typescript`; these are test-evidence skills, but `audit-typescript` explicitly delegates test concerns to `audit-typescript-tests` elsewhere. Remove the test-skill invocations from `quick_start`.
