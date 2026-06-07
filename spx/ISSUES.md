# ISSUES — product-level hygiene

Cross-cutting imperfections noticed in the marketplace that do not belong to a single spec node. Each entry names a file, the exact rule it violates, and the smallest unit of work that resolves it.

`/contextualizing` reads this file at product-root context-load time; the entries are visible to any session that enters `spx/`.

## Lint and format drift in `outcomeeng_*` and `outcomeeng/vendor/`

`uv run ruff check .` reports 5 errors, all fixable with `--fix`:

- `outcomeeng/scripts/validate_plugins.py` — `F541` extraneous `f` prefix on a literal-only f-string.
- `outcomeeng/vendor/anthropics_skills/quick_validate.py` — `F401` unused import (vendored third-party code — `pyproject.toml` already excludes the directory from mypy via `tool.mypy.overrides`; consider adding a ruff `per-file-ignores` entry for `outcomeeng/vendor/**` instead of editing the vendored file).
- `outcomeeng_evals/cli/commands/run.py` — `F401`.
- `outcomeeng_testing/generators/directives.py` — `F401`.
- `spx/32-distribution.enabler/tests/test_distribute_skills.scenario.l1.py` — `F401` (`import os` unused).

`uv run ruff format --check .` reports 4 files needing reformat (same set as above plus `outcomeeng_evals/cli/commands/run.py`).

**Resolution shape**: small `chore(repo): ruff --fix + ruff format` PR. Vendored code gets a `per-file-ignores` rather than an in-file edit. Audit gate: re-run `uv run ruff check . && uv run ruff format --check .` after the fix.

## Stale relative links in spec-tree spec files (RESOLVED)

`spx validation markdown` no longer reports relative-link errors. The session
handoff plan now points at `src/plugins/spec-tree/...`, matching the authored
plugin source tree.

**Resolution evidence**: `spx validation markdown` passes.

## Govern Go test conventions before a Go language plugin ships

The methodology documents Go's test-infrastructure home (`internal/testinfra/`) in `spx/15-test-infrastructure.pdr.md` and Go test-file naming (`<subject>.<evidence>.<level>[.<runner>]_test.go`) in the testing and understanding skill references. No decision governs Go test-runner selection (`go test`), subtest conventions, `t.Helper()` policy, or the per-language `[test]` runner the way `spx/15-test-language.adr.md` does for this product's own pytest suite — and that ADR does not mention Go.

**Resolution shape**: before a Go language plugin ships, author the governing decision(s) for Go test conventions and reconcile them with the test-infrastructure home already documented here. The package-name constraint (`internal/testinfra/` is package `testinfra`, never `testing`) is already stated in `spx/15-test-infrastructure.pdr.md`, but its audit assertions cover the normative path generically — add a Go-specific audit assertion verifying the package name as part of this work.

## `just check` does not run ruff or `spx validation markdown` (RESOLVED)

`spx/15-validation.enabler/65-check-pipeline.enabler/` declares a signal-safe Python orchestrator at `outcomeeng/scripts/check.py` that replaces the prior bash heredoc. The new step list includes `fmt-check → ruff → manifests → skills → docs-check → markdown → pytest`, so the two previously-missing checks now run on every `just check`. The lint and format entry above remains in scope for a separate `chore(repo): ruff --fix + ruff format` PR if the current branch does not resolve it directly.

## Shipped skill content cites marketplace-internal decision paths (RESOLVED)

`AGENTS.md` "Two audiences, two design surfaces" requires authored skill content under `src/plugins/` to render into portable plugin output: "never a marketplace-internal node path, never a PDR or ADR specific to this product." The shipped skill, command, and template bodies that cited this marketplace's own decision files by `spx/<NN>-<slug>.{pdr,adr}.md` path are reframed to state the rule portably — pointing to the governing skill, or stating it inline — without the product path:

- `src/plugins/spec-tree/commands/review-changes.md` — the two `spx/15-agent-pr-authority.pdr.md` citations now point to the `standardizing-merging` skill.
- `src/plugins/spec-tree/skills/auditing/SKILL.md` — the `spx/15-audit-verdict-format.pdr.md` reference and the `spx/13-plugin-and-runtime-conventions.adr.md` comment now state the rule inline.
- `src/plugins/spec-tree/skills/decomposing/references/archetypes/{website,toolchain}/seed-tree.json` and `toolchain/example/xideck.md` — provenance notes name "the normative test-infrastructure subtree" without the PDR path.
- `src/plugins/spec-tree/skills/bootstrapping/templates/spx-claude.md` — the per-project evidence-lane sentence drops the "e.g., `spx/14-verification.pdr.md` in this marketplace" example.

Left as-is (not violations): fictional example paths illustrating format (`spx/15-product-offering.pdr.md`; `spx/15-api-contract.adr.md`, `spx/22-cache-policy.adr.md`, `spx/15-build.adr.md`; the `spx/15-auth-strategy.adr.md` numeric-prefix illustration in `spx-claude.md`), and the archetype `leoherd`/`xiperlabs`/`xideck` `source` annotations that intentionally name the external products each archetype was distilled from. Spec assertions inside `spx/**` that cite a governing decision by full path are correct and out of scope — the rule governs shipped skill bodies, not the spec tree.

**Resolution evidence**: `grep -rnE "spx/[0-9]{2}-[a-z-]+\.(pdr|adr)\.md" src/plugins/` returns only illustrative and external-product references; `just check-skills` and `just docs-check` pass.

## Lean PDR template vs. normative-heavy decisions (FOLLOW-UP)

`spx/15-test-infrastructure.pdr.md` is migrated to the lean decision template and conforms to its `## Product properties` cap of three items, but still departs from the template's minimal shape in two ways its normative substance forces: (1) three decision-body sections (`## Category Semantics`, `## Evidence Chain`, `## Spec Traceability`) between the opening statement and `## Rationale`, beyond the four-section shape (opening, `## Rationale`, `## Product properties`, `## Verification`); and (2) a multi-paragraph `## Rationale` that absorbs the former `## Context` and `## Trade-offs accepted` content (including the trade-offs table) rather than the one-to-two-sentence Rationale the template prescribes. Both deviations are content-driven: the per-language path table, the harness/generator/fixture category tables, the evidence-chain rules, traceability, and the folded context/trade-offs reasoning are the decision itself and have no home in the minimal four-section template; `/audit-pdr` approved the migrated structure, and the operator completed the mandated human content-preservation review against the pre-migration revision — confirming no normative content was lost — and approved the migration. The lean PDR template (`src/plugins/spec-tree/skills/understanding/templates/decisions/decision-name.pdr.md`) prescribes the four-section shape and a one-to-two-sentence Rationale and does not describe an extension for normative-heavy decisions that legitimately need decision-body sections.

**Resolution shape**: decide whether to (a) amend the lean PDR template to describe an extension for normative-heavy decisions (decision-body sections and a longer Rationale), naming `spx/15-test-infrastructure.pdr.md` as the reference, or (b) restructure this PDR into the minimal four-section shape without losing normative content. Until then, `spx/15-test-infrastructure.pdr.md` stands as a documented deviation.

Identified during the lean-template migration of the product-level decision records.
