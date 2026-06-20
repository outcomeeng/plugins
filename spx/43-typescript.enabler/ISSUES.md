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

## Skill-delegation `Skill` allowed-tools gap — PR2 (OPEN)

The marketplace-wide `require_skill` → `Skill` sweep closed spec-tree/python/rust in PR #279; typescript
is held for its own PR because two of its skills also carry pre-existing skill-auditor REJECTs that must
be remediated in the same change (touched-file debt — once a SKILL.md is edited, its auditor must-fixes
are in scope). A skill whose body invokes another skill needs `Skill` in `allowed-tools`, or the
delegation requires per-call approval; the cross-plugin context and detection heuristic are in
`spx/43-develop.enabler/ISSUES.md` §2.

**The 6 skills needing `Skill` appended to `allowed-tools`** (each carries `{!% require_skill … %!}`
and/or an `Invoke /<skill>` prerequisite):

- **Clean, frontmatter-only** (`audit-*` stay read-only — append `Skill`, never `Write`/`Edit`):
  `code-typescript`, `test-typescript`, `audit-typescript-architecture`, `audit-typescript-tests`.
- **`architect-typescript` — append `Skill` AND remediate its pre-existing REJECTs:**
  1. Product-path portability: the body cites `spx/CLAUDE.md` and `spx/{NN}-{slug}.adr.md` directly,
     which do not exist in a consumer that installs the typescript plugin without spec-tree. Reword to a
     conditional ("If this repository uses the spec-tree methodology, read its spec-tree root guide and
     the relevant ancestor ADRs/PDRs …"). NOTE `architect-python`/`architect-rust` carry the same
     `spx/CLAUDE.md` references but their PR #279 audits did not flag them — if the auditor flags those
     too, that is a separate cross-language portability pass, not this PR.
  2. Missing `<objective>` tag: `architect-python` and `architect-rust` have one; `architect-typescript`
     does not (skill-auditor REJECT). Add a TypeScript-accurate `<objective>` after the `require_skill`
     directive (no reviewer-gate claim unless the body actually dispatches one). An earlier session
     drafted this objective in a now-stale git stash — re-author from scratch.
- **`audit-typescript` — do NOT add `Skill` to enable its quick_start `/test` invocation; that
  invocation is the defect** (see the `audit-typescript` Spot Defects entry above). Fixes:
  1. Change quick_start step 1 "invoke `/test` … `/test-typescript`" to "Read `/test` … `/test-typescript`"
     to match the read-only sibling pattern — `audit-python`/`audit-rust` carry NO `Skill` and say "Read".
  2. Move the `spx/local/typescript.md` overlay check out of `<objective>` into a dedicated
     `<repo_local_overlay>` tag (siblings use that tag), removing the quick_start duplication.
  3. Fix the broken `${CLAUDE_SKILL_DIR}/rules/` reference (Spot Defects line 77) — the skill ships
     `references/` only.
  4. Verify whether `audit-typescript`'s body carries a `{!% require_skill … %!}` macro: if YES it needs
     `Skill` regardless (append it); if its only delegation was the quick_start `/test`, the Read-rewrite
     resolves it and NO `Skill` is added — matching audit-python/audit-rust.

**Procedure:** edit src → `just build-skills` → gate EVERY changed SKILL.md with `develop:skill-auditor`
(CI/changes-reviewer do not load skill standards; only the auditor catches voice/structure/portability)
→ fix every must-fix on touched files → `just bump` (typescript patch) → `/merge`. Marketplace-wide
classes the auditor will also flag are out of scope and tracked in `spx/43-develop.enabler/ISSUES.md` §2
(the bare `…/audit/scripts/verdict.py` verdict-path citation; `<quick_start>` on validators; reference
markdown-heading style — see also "Legacy XML Structure Cleanup" above).

Surfaced by PR #279 (the spec-tree/python/rust Skill-gap sweep).
