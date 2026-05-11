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

## Verdict-Format Drift Between PDR and Auditing Skills

`spx/15-audit-verdict-format.pdr.md` flipped to JSON in commit `dd03033`. The current auditing skills (`/auditing-tests`, `/auditing-typescript-tests`, `/auditing-typescript`, `/auditing-typescript-architecture`, etc.) still emit markdown verdict tables. The PDR also overreached during the flip by prohibiting markdown fences and mandating that the assistant response IS the verdict — wrong for the audit-skill case, where the verdict is delivered into a PR comment and the markdown carrier is the only durable cross-CI-run surface.

Resolution lives in [`spx/21-spec-tree.enabler/65-auditing.enabler/PLAN.md`](../21-spec-tree.enabler/65-auditing.enabler/PLAN.md) under `## PLAN: verdict-format carrier alignment and orchestrator/dispatched coherence`:

1. Refine the PDR — drop the two overreaching clauses, add an embedded-delivery Compliance section describing the carrier+payload model.
2. Update every audit skill's verdict-emit section to wrap a delimited JSON block (`<!-- AUDIT_VERDICT_JSON_BEGIN -->` / `<!-- AUDIT_VERDICT_JSON_END -->`) inside the existing markdown verdict surface.

## `auditing-typescript` Spot Defects (PR #10 Follow-up)

Three small fixes against `plugins/typescript/skills/auditing-typescript/SKILL.md`, deferred from PR #10 because they belong with the broader audit-skill alignment work rather than with the eval-harness branch.

- Line 25: typo "Typecsript" → "TypeScript".
- Line 77: broken reference `${CLAUDE_SKILL_DIR}/rules/` — the directory does not exist; the skill ships `references/` only. Either correct the path to `references/` or create `rules/` if a separate location is intended.
- Line 33: `quick_start` invokes `/testing` and `/testing-typescript`; these are test-evidence skills, but `auditing-typescript` explicitly delegates test concerns to `auditing-typescript-tests` elsewhere. Remove the test-skill invocations from `quick_start`.

These three edits land in one focused commit alongside (or just after) the audit-skill carrier+payload alignment work in the follow-up PR.
