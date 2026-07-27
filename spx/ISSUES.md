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

## Align Python and Rust test-standards subtrees to the semantic-binding foundation

The test-verification foundation (`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `15-test-infrastructure.pdr.md`) declares the semantic-binding-ownership model: the linked test owns every behavioral predicate and assertion call, and a test-file binding is judged by what it chooses — an observation or handle alias is valid, while a binding that chooses a case, expected result, configuration, setup policy, generator domain, fixture content, or verdict rule belongs to its semantic owner. The TypeScript standards subtree (`spx/43-typescript.enabler/25-typescript-standards.enabler`) is aligned to this model — the absolute "never declare variables or constants" rule replaced by the semantic-binding form citing the governing node, `([review])` migrated to `([audit])`, and "evidence type" retired to "assertion type". The Python and Rust subtrees are now aligned to this model. `spx/43-rust.enabler/rust.md` and the Python `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler` subtree cite the governing node for the seam rules, the superseded absolute declaration ban is removed from Python, and `([review])` is migrated to `([audit])` in every file that alignment touched. Roughly 37 `([review])` tags remain in the broader `spx/43-python.enabler` node and its untouched children (`python-standards.md`, `python-architecture.md`, `python-code.md`, `execution-level-guidance.md`, and `test-infrastructure-auditing.md`).

**Resolution shape**: the Python and Rust semantic-binding alignment landed by promoting the seam rules to the superset at `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and reducing the language nodes to deltas that cite it. TypeScript's top-level and subtree parity landed in the TypeScript seam-delta reduction — `spx/43-typescript.enabler/typescript.md`, `.../25-typescript-tests.enabler/typescript-tests.md`, `.../21-source-testability.enabler/source-testability.md`, and `.../32-test-data-ownership.enabler/test-data-ownership.md` reduced to cite the ancestor + PDR and declare only the TypeScript delta — so all three language subtrees are aligned. The only residual is the `([review])` → `([audit])` migration in untouched `spx/43-python.enabler` files, continued under the tree-wide `([review])` migration entry above.

**Evidence.** Surfaced by the CI reviewer on the TypeScript-alignment changeset as a cross-language `[consistency]` divergence: aligning one language subtree ahead of the others makes the sibling standards disagree until the others catch up. Each language subtree is a distinct, comparably sized slice, outside the scope of any single language's alignment change.

## Align tree-wide agent/runtime terminology with the SPX agent-harness PDR

The SPX product's `spx/12-agent-harness.pdr.md` (in the `@outcomeeng/spx` repo) fixes the vocabulary for agent concepts: **agent harness** (the SPX-managed repository behavior around agents), **agent** (a selectable coding agent — Codex, Claude Code), **agent adapter**, and **agent session**, and forbids collapsing those roles into one term. "Runtime" is not in that vocabulary. `spx/12-marketplace-state.adr.md` and the diagnostics node (`spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`, `15-version-floor.adr.md`, `diagnostics.md`, and `PLAN.md`) are aligned; the rest of this product's tree still uses "runtime" / "per-runtime" / "coding-agent runtime" / "runtime-divergent" for agent concepts.

Remaining drift (agent-concept "runtime" usage, distinct from generic "at runtime"):

- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` and `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler/runtime-parameterization.md` — "runtime-divergent", "per-runtime registry", "No runtime is the source language" (means per-agent-target rendering).
- `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md` — "per-runtime conditional", "runtime-divergent name".
- `spx/21-spec-tree.enabler/13-agent-environment.enabler/**` — "per-runtime session directory" (means per-agent).
- Node names encode the term: `spx/15-validation.enabler/32-runtime-token.enabler`, `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

**Resolution shape**: a whole-tree sweep aligning agent-concept "runtime" usage to "agent" / "agent harness" per `spx/12-agent-harness.pdr.md`, distinguishing it from generic execution-time "runtime". Because node names carry the term, the sweep includes `/refactor` node renames and is therefore a structural change, not a text-only pass — deferred from the scoped marketplace-state/diagnose terminology fix that surfaced it, by operator decision.

## 26 bundled reference files over 100 lines carry no table of contents

`/skill-standards` `<progressive_disclosure>` requires a table of contents at the top of every reference file over 100 lines, "so partial reads still see the full scope". Twenty-six files across seven plugins exceed the threshold without one, ranging from 108 to 971 lines:

- `hdl` — `review-systemverilog/references/systemverilog-idioms.md` (716), `review-vhdl/references/vhdl-idioms.md` (472)
- `instructions` — all seven `create-subagent/references/*.md` (410–971), both `audit-skill/references/*.md` (116, 140), both `create-skill/references/*.md` (113, 123)
- `rust` — `architect-rust/references/{adr-patterns,rust-principles}.md` (120, 108), `code-rust/references/outcome-engineering-patterns.md` (138), `rust-test-standards/references/level-1.md` (111)
- `spec-tree` — `audit-eval-evidence/references/evidence-model.md` (143)
- `typescript` — `architect-typescript/references/typescript-principles.md` (144), both `code-typescript/references/*.md` (116, 138), `typescript-test-standards/references/exception-implementations.md` (109)
- `work` — both `draw-excalidraw/references/*.md` (128, 202), both `sanitize-powerpoint/references/*.md` (134, 136)

A table of contents is satisfied by a `## Contents` section, an XML `<contents>` block, or a `<reference_index>` section; files already using one of those forms are excluded from the count above.

**Evidence.** Surfaced while satisfying the same requirement for the five `architect-python` references, which were fixed in the changeset that found it. The remaining twenty-six lie in plugins that changeset does not touch.

**Resolution shape**: add a table of contents to each file in the form its surrounding skill already uses — `## Contents` for markdown-structured references, `<contents>` for XML-structured ones — listing every top-level section. Run `instructions:skill-auditor` over each affected skill afterward. The sweep divides cleanly by plugin, so it can land as one changeset per plugin rather than one large one.

**Revisit condition.** Resolve per plugin when that plugin next needs a reference-file change, or as one dedicated sweep. `create-subagent` is the highest-value single target: seven files, 4,646 lines, the largest partial-read exposure in the marketplace.

## Agent-specific behavior is enumerated inside product-level decisions

Product-level decisions carry per-agent facts inline, so adding an agent harness edits decisions
whose subject is not that harness. `spx/12-marketplace-state.adr.md` enumerates each agent's
committed marketplace catalog, plugin-selection boundary, and configuration location — Codex's
`.agents/plugins/marketplace.json` and caller-selected `CODEX_HOME` beside Claude Code's
`.claude-plugin/marketplace.json` and project-scope `.claude/settings.json`. A third agent harness
therefore churns a product-level decision that governs state ownership rather than agent identity.

**Resolution shape**: author a `coding-agents` node with one child per agent, each child declaring
its own agent's capabilities and configuration locations — whether its plugin manifest can declare
agents, whether its agent namespace is flat, its native agent format and filename shape, and the
committed configuration it reads. The product-level decision then collapses to capability
assertions of the form `ALWAYS: each agent declares capability X, verified by that agent's node` and
`NEVER: agent-specific behavior is decided outside that agent's node`, so a new harness adds a child
rather than amending a decision. The node's location is undetermined and depends on concept
ownership and context-loading reach, so placement routes through `/decompose` rather than being
chosen when the node is authored.

**Evidence.** Surfaced while making `spx/12-marketplace-state.adr.md` and
`spx/18-plugin-build.enabler/15-build-architecture.adr.md` capability-keyed for committed agent
delivery. The build decision now resolves per-target agent format, filename shape, and namespace
behavior from the source-owned per-target registry, so a new target is a registry entry; the
catalog and state-boundary enumeration in the marketplace-state decision is the remaining
per-agent coupling.

**Revisit condition.** Resolve before a third agent harness ships, since that is the change the
coupling taxes. Related to the agent-harness terminology sweep recorded above, which the same
decomposition can carry.
