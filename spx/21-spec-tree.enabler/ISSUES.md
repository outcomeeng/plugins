# Issues: Spec Tree Enabler

Issues discovered during contradiction analysis of `spx/EXCLUDE`, sync-exclude, and the quality gate mechanism. Source: `methodology/skills/skill-structure.md` stale content + cross-file contradiction audit.

## 8. Multi-language test discovery missing from methodology (PARTIAL)

Multi-language discovery is documented in `excluded-nodes.md` and `sync-exclude.md` spec (mapping assertions for pytest/vitest). The `status.yaml` reference in `testing-foundation.md` was removed in commit `391e9e5`.

**Remaining:** upstream `outcomeeng/methodology` repo still needs the multi-language principle added to `spec-tree-reference.md`.

## 9. `committing-changes` references `just check`

`skill-structure.md` line 457: "Run product validation (e.g., `just check`)." Should reference `spx` validation as the spec-tree quality gate. `just check` is the product's own concern, separate from spec-tree.

## 10. Spec headers diverged from upstream methodology

Plugin uses `PROVIDES ... SO THAT ... CAN ...` and `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Upstream `outcomeeng/methodology/reference/spec-tree-reference.md` uses `## Enables...` and `## We believe that...`. Plugin leads; upstream needs to catch up.

## 11. Upstream methodology still references `spx-lock.yaml`

`outcomeeng/methodology/reference/spec-tree-reference.md` lines 86-108 describe a lock-file model (`spx-lock.yaml`, blob hashes, "Needs work / Stale / Valid" states) that the plugin replaced with the EXCLUDE + derived-state model. The upstream needs to be rewritten to match.

## 13. `.evidence.md` artifact type unrecognized by methodology

`spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.evidence.md` introduces a `.evidence.md` artifact suffix as supporting material for `21-compact-continuity.pdr.md`. The file's own Status section documents the gap: `/spec-tree:contextualizing` globs only `*.adr.md`, `*.pdr.md`, `PLAN.md`, and `ISSUES.md`, so `.evidence.md` is reachable only by direct read or grep — not by deterministic context loading. No PDR formalizes the artifact type.

**Resolutions to choose from:**

- Formalize `.evidence.md` via a methodology PDR (parallel to `.adr.md` / `.pdr.md` / `PLAN.md` / `ISSUES.md`) and extend `/spec-tree:contextualizing` to include it in the glob set.
- Fold the diagnostic content into the PDR's Rationale or an appendix and delete the standalone file.
- Rename the file to `PLAN.md` or `ISSUES.md` so it lands inside the recognized taxonomy.

## 12. Repo-wide evidence links still contain legacy test naming (RESOLVED)

Resolved 2026-05-13. Every filename-shaped legacy reference (`*.unit.test.{ext}`, `*.integration.test.{ext}`, `*.e2e.test.{ext}`, `test_*.unit.{ext}`, `test_*.integration.{ext}`, `test_*.e2e.{ext}`) in spec assertions, spec-tree templates, examples, and methodology references was rewritten to the canonical `<subject>.<evidence>.<level>[.<runner>]` form, splitting mixed-evidence specs across one file per evidence type. Remaining mentions of the legacy tokens are scoped to:

- `plugins/{python,typescript}/skills/standardizing-*-tests/SKILL.md` — the forbidden-patterns lists that define what counts as legacy.
- `plugins/typescript/skills/auditing-typescript-tests/SKILL.md` and `plugins/develop/skills/auditing-skills/references/operational-effectiveness-examples.md` — historical failure cases that contrast legacy with canonical naming.
- `plugins/spec-tree/skills/authoring/SKILL.md` and `plugins/spec-tree/skills/testing/SKILL.md` — authoring/audit checklists that name the forbidden patterns so agents recognize and reject them.

## 13. Marketplace-scoped PDR MUST rules carry `[review]` where `[test]` is possible

`spx/15-test-infrastructure.pdr.md` Compliance MUST rules all tag `([review])`. Several are structurally checkable against this marketplace's own spec tree without human judgment:

- "Every spec tree governed by this methodology has the canonical subtree `infrastructure → testing → {generators, fixtures, harnesses}`" — a conformance test can walk `spx/` and assert the slugs exist at the expected indices.
- "Test files follow `<subject>.<evidence>.<level>[.<runner>]`" — a compliance test already exists for the naming convention via `15-test-language.adr.md` and the validator under `spx/15-validation.enabler/`. The PDR's rule should reuse or wrap that evidence rather than re-state it as `[review]`.

`[review]` is correct for cross-product rules (this repo cannot assert what other products do). The marketplace's own tree is in scope and should carry `[test]` evidence where the assertion is structurally checkable.

Surfaced by `claude-review` on PR 14 (2026-05-13).
