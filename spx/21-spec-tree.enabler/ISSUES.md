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

## 14. PDR Rust row lacks the hyphen→underscore explanation

`spx/15-test-infrastructure.pdr.md` shows both `<product>-testing` (Cargo package name) and `<product>_testing` (Rust import path) in the per-language table. Cargo normalizes hyphens to underscores in import paths, but readers unfamiliar with this convention may read the two forms as a contradiction. A single inline sentence — *Cargo normalizes hyphens to underscores in the import path: package `product-testing` → `use product_testing::...`* — closes the gap.

Surfaced by `claude-review` on PR 14 round 3 (2026-05-13).

## 15. `committing-changes` example uses uppercase `L1` instead of canonical `l1`

`plugins/spec-tree/skills/committing-changes/SKILL.md` example commit body says "L1 testing" while every other spec assertion, filename, and convention reference uses lowercase `l1`. The current level tokens were retained at the user's direction during PR 14, but the example body should eventually be brought into line so it does not teach the uppercase form to readers who skim examples without reading the surrounding skill.

Surfaced by `claude-review` on PR 14 rounds 2–3 (2026-05-13).
