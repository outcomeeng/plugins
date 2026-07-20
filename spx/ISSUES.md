# ISSUES — product-level hygiene

Cross-cutting imperfections noticed in the marketplace that do not belong to a single spec node. Each entry names a file, the exact rule it violates, and the smallest unit of work that resolves it.

`/contextualize` reads this file at product-root context-load time; the entries are visible to any session that enters `spx/`.

## Govern Go test conventions before a Go language plugin ships

The methodology documents Go's test-infrastructure home (`internal/testinfra/`) in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` and Go test-file naming (`<subject>.<evidence>.<level>[.<runner>]_test.go`) in the testing and understanding skill references. No decision governs Go test-runner selection (`go test`), subtest conventions, `t.Helper()` policy, or the per-language `[test]` runner the way `spx/15-test-language.adr.md` does for this product's own pytest suite — and that ADR does not mention Go.

**Resolution shape**: before a Go language plugin ships, author the governing decision(s) for Go test conventions and reconcile them with the test-infrastructure home already documented here. The package-name constraint (`internal/testinfra/` is package `testinfra`, never `test`) is already stated in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`, but its audit assertions cover the normative path generically — add a Go-specific audit assertion verifying the package name as part of this work.

## Lean PDR template vs. normative-heavy decisions (FOLLOW-UP)

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` is migrated to the lean decision template and conforms to its `## Product properties` cap of three items, but still departs from the template's minimal shape in two ways its normative substance forces: (1) three decision-body sections (`## Category Semantics`, `## Evidence Chain`, `## Spec Traceability`) between the opening statement and `## Rationale`, beyond the four-section shape (opening, `## Rationale`, `## Product properties`, `## Verification`); and (2) a multi-paragraph `## Rationale` that absorbs the former `## Context` and `## Trade-offs accepted` content (including the trade-offs table) rather than the one-to-two-sentence Rationale the template prescribes. Both deviations are content-driven: the per-language path table, the harness/generator/fixture category tables, the evidence-chain rules, traceability, and the folded context/trade-offs reasoning are the decision itself and have no home in the minimal four-section template; `/audit-pdr` approved the migrated structure, and the operator completed the mandated human content-preservation review against the pre-migration revision — confirming no normative content was lost — and approved the migration. The lean PDR template (`src/plugins/spec-tree/skills/understand/templates/decisions/decision-name.pdr.md`) prescribes the four-section shape and a one-to-two-sentence Rationale and does not describe an extension for normative-heavy decisions that legitimately need decision-body sections.

**Resolution shape**: decide whether to (a) amend the lean PDR template to describe an extension for normative-heavy decisions (decision-body sections and a longer Rationale), naming `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` as the reference, or (b) restructure this PDR into the minimal four-section shape without losing normative content. Until then, `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` stands as a documented deviation.

Identified during the lean-template migration of the product-level decision records.

## Migrate legacy `[review]` assertion tags to `[audit]` tree-wide

`[review]` is the legacy spelling of the `[audit]` assertion tag — it resolves to `[audit]` during migration per the inline `/understand` `<verification_model>`, and `reviewing` is a gate that backs no tag. Roughly 68 spec files across `spx/` still carry `([review])` on assertions (for example `spx/43-instructions.enabler/instructions.md` and `spx/15-validation.enabler/32-skill-frontmatter.enabler/skill-frontmatter.md`). The migration has been applied node by node where other work already touched a node — the sessions enabler, `76-sessions.enabler/32-session-skill-invocation.enabler`, and `21-spec-tree.enabler/18-context-loading.enabler` — so the spelling is mixed tree-wide with no single tracking location.

**Resolution shape**: batch-migrate the remaining `([review])` occurrences to `([audit])` node by node — the text of each assertion is unchanged, only the tag spelling — gating each batch with the spec auditor. Once the tree carries no `[review]`, remove the legacy-spelling note from inline `/understand` `<verification_model>`.

## Align tree-wide agent/runtime terminology with the SPX agent-harness PDR

The SPX product's `spx/12-agent-harness.pdr.md` (in the `@outcomeeng/spx` repo) fixes the vocabulary for agent concepts: **agent harness** (the SPX-managed repository behavior around agents), **agent** (a selectable coding agent — Codex, Claude Code), **agent adapter**, and **agent session**, and forbids collapsing those roles into one term. "Runtime" is not in that vocabulary. `spx/12-marketplace-state.adr.md` and the diagnostics node (`spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`, `15-version-floor.adr.md`, `diagnostics.md`, and `PLAN.md`) are aligned; the rest of this product's tree still uses "runtime" / "per-runtime" / "coding-agent runtime" / "runtime-divergent" for agent concepts.

Remaining drift (agent-concept "runtime" usage, distinct from generic "at runtime"):

- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` and `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler/runtime-parameterization.md` — "runtime-divergent", "per-runtime registry", "No runtime is the source language" (means per-agent-target rendering).
- `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md` — "per-runtime conditional", "runtime-divergent name".
- `spx/21-spec-tree.enabler/13-agent-environment.enabler/**` — "per-runtime session directory" (means per-agent).
- Node names encode the term: `spx/15-validation.enabler/32-runtime-token.enabler`, `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

**Resolution shape**: a whole-tree sweep aligning agent-concept "runtime" usage to "agent" / "agent harness" per `spx/12-agent-harness.pdr.md`, distinguishing it from generic execution-time "runtime". Because node names carry the term, the sweep includes `/refactor` node renames and is therefore a structural change, not a text-only pass — deferred from the scoped marketplace-state/diagnose terminology fix that surfaced it, by operator decision.

## rust-test-standards renders no language-specific shared-litmus section

`src/plugins/python/skills/python-test-standards/SKILL.md` and `src/plugins/typescript/skills/typescript-test-standards/SKILL.md` each carry a section that applies every question in `/test-evidence-standards` `<common_litmus_questions>` and every mutation in its `<mutation_litmus>`, then renders the language-specific form of those items while deferring to the shared set as complete. `src/plugins/rust/skills/rust-test-standards/SKILL.md` carries no equivalent section and no reference to `/test-evidence-standards`.

**Status against the standard.** This is parity, not a contradiction. rust-test-standards holds no inline litmus, predicate-seam, semantic-binding, oracle-independence, case-provenance, or mutation content, so the shared standard duplicates nothing there and invalidates none of its guidance. The Rust audit path still receives the shared litmus through the base `/audit-tests`, which invokes `/test-evidence-standards` for every language. The gap is only that Rust authors reading rust-test-standards do not get the Rust-specific rendering their Python and TypeScript counterparts get.

**Evidence.** Surfaced while wiring the shared `test-evidence-standards` skill into the Python and TypeScript authoring standards. The seam changeset touches the Rust auditor (`audit-rust-tests`) and Rust test skill (`test-rust`) but not `rust-test-standards`, so the file lies outside the changeset.

**Resolution shape**: add a shared-litmus section to `rust-test-standards` mirroring the Python and TypeScript siblings — apply the complete `/test-evidence-standards` litmus and mutation set, then render the Rust-specific form (borrow/lifetime bindings, `#[cfg(test)]` module ownership, trait-object doubles) without replacing or bounding the shared set. Run `instructions:skill-auditor` over `rust-test-standards` afterward.

## 26 bundled reference files over 100 lines carry no table of contents

`/skill-standards` `<progressive_disclosure>` requires a table of contents at the top of every reference file over 100 lines, "so partial reads still see the full scope". Twenty-six files across seven plugins exceed the threshold without one, ranging from 108 to 971 lines:

- `hdl` — `review-systemverilog/references/systemverilog-idioms.md` (716), `review-vhdl/references/vhdl-idioms.md` (472)
- `instructions` — all seven `create-subagents/references/*.md` (410–971), both `audit-skills/references/*.md` (116, 140), both `create-skill/references/*.md` (113, 123)
- `rust` — `architect-rust/references/{adr-patterns,rust-principles}.md` (120, 108), `code-rust/references/outcome-engineering-patterns.md` (138), `rust-test-standards/references/level-1.md` (111)
- `spec-tree` — `audit-eval-evidence/references/evidence-model.md` (143)
- `typescript` — `architect-typescript/references/typescript-principles.md` (144), both `code-typescript/references/*.md` (116, 138), `typescript-test-standards/references/exception-implementations.md` (109)
- `work` — both `draw-excalidraw/references/*.md` (128, 202), both `sanitize-powerpoint/references/*.md` (134, 136)

A table of contents is satisfied by a `## Contents` section, an XML `<contents>` block, or a `<reference_index>` section; files already using one of those forms are excluded from the count above.

**Evidence.** Surfaced while satisfying the same requirement for the five `architect-python` references, which were fixed in the changeset that found it. The remaining twenty-six lie in plugins that changeset does not touch.

**Resolution shape**: add a table of contents to each file in the form its surrounding skill already uses — `## Contents` for markdown-structured references, `<contents>` for XML-structured ones — listing every top-level section. Run `instructions:skill-auditor` over each affected skill afterward. The sweep divides cleanly by plugin, so it can land as one changeset per plugin rather than one large one.

**Revisit condition.** Resolve per plugin when that plugin next needs a reference-file change, or as one dedicated sweep. `create-subagents` is the highest-value single target: seven files, 4,646 lines, the largest partial-read exposure in the marketplace.
