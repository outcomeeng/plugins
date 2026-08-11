# ISSUES — product-level hygiene

Cross-cutting imperfections noticed in the marketplace that do not belong to a single spec node. Each entry names a file, the exact rule it violates, and the smallest unit of work that resolves it.

`/contextualize` reads this file at product-root context-load time; the entries are visible to any session that enters `spx/`.

## Govern Go test conventions before a Go language plugin ships

The methodology documents Go's test-infrastructure home (`internal/testinfra/`) in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` and Go test-file naming (`<subject>.<evidence>.<level>[.<runner>]_test.go`) in the testing and understanding skill references. No decision governs Go test-runner selection (`go test`), subtest conventions, `t.Helper()` policy, or the per-language `[test]` runner the way `spx/15-test-language.adr.md` does for this product's own pytest suite — and that ADR does not mention Go.

**Resolution shape**: before a Go language plugin ships, author the governing decision(s) for Go test conventions and reconcile them with the test-infrastructure home already documented here. The package-name constraint (`internal/testinfra/` is package `testinfra`, never `test`) is already stated in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`, but its audit assertions cover the normative path generically — add a Go-specific audit assertion verifying the package name as part of this work.

**Also gated by this**: the managed instruction-block router renders no Go language block, because `LANGUAGE_BY_EXTENSION` in `src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` maps only `py`, `ts`, and `rs`, and the template declares only `lang:python`, `lang:typescript`, and `lang:rust`. A Go product therefore renders with an empty language list and no Go test-naming guidance. Adding a `lang:go` block requires the audit-skill table it introduces to name `audit-go-code`, `audit-go-tests`, and `audit-go-architecture` — skills `spx/21-spec-tree.enabler/17-audit.adr.md` requires of every plugin that defines a programming language, and which do not exist because no Go plugin ships. Add the Go language block to the template and the extension map in the same change that ships the Go plugin.

**Evidence**: observed running the update workflow against a Go product, whose router carried an empty `langs:` marker and no Go test-naming table.

## Lean PDR template vs. normative-heavy decisions (FOLLOW-UP)

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` is migrated to the lean decision template and conforms to its `## Product properties` cap of three items, but still departs from the template's minimal shape in two ways its normative substance forces: (1) three decision-body sections (`## Category Semantics`, `## Evidence Chain`, `## Spec Traceability`) between the opening statement and `## Rationale`, beyond the four-section shape (opening, `## Rationale`, `## Product properties`, `## Verification`); and (2) a multi-paragraph `## Rationale` that absorbs the former `## Context` and `## Trade-offs accepted` content (including the trade-offs table) rather than the one-to-two-sentence Rationale the template prescribes. Both deviations are content-driven: the per-language path table, the harness/generator/fixture category tables, the evidence-chain rules, traceability, and the folded context/trade-offs reasoning are the decision itself and have no home in the minimal four-section template; `/audit-pdr` approved the migrated structure, and the operator completed the mandated human content-preservation review against the pre-migration revision — confirming no normative content was lost — and approved the migration. The lean PDR template (`src/plugins/spec-tree/skills/understand/templates/decisions/decision-name.pdr.md`) prescribes the four-section shape and a one-to-two-sentence Rationale and does not describe an extension for normative-heavy decisions that legitimately need decision-body sections.

**Resolution shape**: decide whether to (a) amend the lean PDR template to describe an extension for normative-heavy decisions (decision-body sections and a longer Rationale), naming `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` as the reference, or (b) restructure this PDR into the minimal four-section shape without losing normative content. Until then, `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` stands as a documented deviation.

Identified during the lean-template migration of the product-level decision records.

## Align tree-wide agent/runtime terminology with the SPX agent-harness PDR

The SPX product's `spx/12-agent-harness.pdr.md` (in the `@outcomeeng/spx` repo) fixes the vocabulary for agent concepts: **agent harness** (the SPX-managed repository behavior around agents), **agent** (a selectable coding agent — Codex, Claude Code), **agent adapter**, and **agent session**, and forbids collapsing those roles into one term. "Runtime" is not in that vocabulary. `spx/12-marketplace-state.adr.md` and the diagnostics node (`spx/21-spec-tree.enabler/79-diagnostics.enabler/13-diagnose-engine.adr.md`, `15-version-floor.adr.md`, `diagnostics.md`, and `PLAN.md`) are aligned; the rest of this product's tree still uses "runtime" / "per-runtime" / "coding-agent runtime" / "runtime-divergent" for agent concepts.

Remaining drift (agent-concept "runtime" usage, distinct from generic "at runtime"):

- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` and `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler/runtime-parameterization.md` — "runtime-divergent", "per-runtime registry", "No runtime is the source language" (means per-agent-target rendering).
- `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md` — "per-runtime conditional", "runtime-divergent name".
- `spx/21-spec-tree.enabler/13-agent-environment.enabler/**` — "per-runtime session directory" (means per-agent).
- Node names encode the term: `spx/15-validation.enabler/32-runtime-token.enabler`, `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

**Resolution shape**: a whole-tree sweep aligning agent-concept "runtime" usage to "agent" / "agent harness" per `spx/12-agent-harness.pdr.md`, distinguishing it from generic execution-time "runtime". Because node names carry the term, the sweep includes `/refactor` node renames and is therefore a structural change, not a text-only pass — deferred from the scoped marketplace-state/diagnose terminology fix that surfaced it, by operator decision.

## 22 bundled reference files over 100 lines carry no table of contents

`/skill-standards` `<progressive_disclosure>` requires a table of contents at the top of every reference file over 100 lines, "so partial reads still see the full scope". Twenty-two files across six plugins exceed the threshold without one, ranging from 109 to 971 lines:

- `hdl` — `review-systemverilog/references/systemverilog-idioms.md` (716), `review-vhdl/references/vhdl-idioms.md` (472)
- `instructions` — all seven `create-subagent/references/*.md` (410–971), both `audit-skill/references/*.md` (116, 140), both `create-skill/references/*.md` (113, 123)
- `rust` — none. The predicate-seam correction resolved every rust reference file over the threshold: the three `rust-test-standards/references/level-{1,2,3}.md` files and `code-rust/references/test-patterns.md` gained `<contents>` blocks as it edited them, and the revisit condition below then carried `architect-rust/references/{adr-patterns,rust-principles}.md` and `code-rust/references/outcome-engineering-patterns.md` in the same changeset.
- `spec-tree` — `audit-eval-evidence/references/evidence-model.md` (143)
- `typescript` — `architect-typescript/references/typescript-principles.md` (144), both `code-typescript/references/*.md` (116, 138), `typescript-test-standards/references/exception-implementations.md` (109)
- `work` — both `draw-excalidraw/references/*.md` (128, 202), both `sanitize-powerpoint/references/*.md` (134, 136)

A table of contents is satisfied by a `## Contents` section, an XML `<contents>` block, or a `<reference_index>` section; files already using one of those forms are excluded from the count above.

**Evidence.** Surfaced while satisfying the same requirement for the five `architect-python` references, which were fixed in the changeset that found it. The remaining twenty-six lie in plugins that changeset does not touch.

**Resolution shape**: add a table of contents to each file in the form its surrounding skill already uses — `## Contents` for markdown-structured references, `<contents>` for XML-structured ones — listing every top-level section. Run `instructions:skill-auditor` over each affected skill afterward. The sweep divides cleanly by plugin, so it can land as one changeset per plugin rather than one large one.

**Revisit condition.** Resolve per plugin when that plugin next needs a reference-file change, or as one dedicated sweep. `create-subagent` is the highest-value single target: seven files, 4,646 lines, the largest partial-read exposure in the marketplace.

## A shipped skill tells a Codex reader that Claude Code invoked it

`<accessing_skill_files>` in several skills reads "When this skill is invoked, Claude Code provides the base directory in the loading message". The build substitutes `${CLAUDE_SKILL_DIR}` for `${SKILL_DIR}` when rendering the Codex tree but leaves the sentence, so `dist/codex/**` ships a claim about the wrong runtime to a Codex-reading agent. The variable substitution itself is correct; only the prose is wrong.

`src/plugins/typescript/skills/architect-typescript/SKILL.md` still carries it. The two rust instances were corrected to "the skill loader provides the base directory" in the changeset that found them.

**Resolution shape**: phrase the mechanism runtime-neutrally wherever the sentence appears, and prefer that phrasing in the skill templates so a new skill does not reintroduce it.

**Why the remainder is separate.** Correcting the typescript instance needs a typescript version bump and its own `skill-auditor` gate, in a plugin the rust-scoped changeset that found this deliberately does not touch.

**Evidence.** Raised by `instructions:skill-auditor` against `code-rust`, which named the cross-plugin spread.

## Reference files structure their own sections as markdown headings

`/skill-standards` `<reference_file_guidance>` prefers semantic XML for a reference file's own structure, reserving markdown for content that is itself a markdown artifact. `architect-rust/references/{adr-patterns,rust-principles}.md` structure themselves with `#`/`##` headings, as do reference files in several other plugins; the sibling `code-rust/references/{test-patterns,outcome-engineering-patterns}.md` already use pure XML. In `adr-patterns.md` the markdown *inside* each pattern is correct — an ADR is a markdown artifact — and only the file's own scaffolding is at issue.

**Resolution shape**: convert each reference file's own sections to semantic XML tags, leaving markdown-artifact examples alone.

**Why this is separate.** The auditor rates it recommendation-level rather than critical, and it spans plugins; `spx/43-typescript.enabler/ISSUES.md` already records the TypeScript half under "Legacy XML Structure Cleanup". One pass per plugin, each with its own gate.

**Evidence.** Raised by `instructions:skill-auditor` against `architect-rust`.

## Three test-standards skills open with success criteria nothing can check

`python-test-standards`, `rust-test-standards`, and `typescript-test-standards` each open `<success_criteria>` with bullets asserting upstream skill sequencing — that `/test` selected the assertion type before implementation, and that the language standards skill loaded before the test standards reference. Neither is a property of the produced test artifact, so no check against a test file can falsify either. The remaining criteria in each skill are checkable, and each skill's `<predicate_and_oracle_litmus>` already operationalizes them into concrete inversion and mutation checks.

**Resolution shape**: fold the sequencing bullets into `<objective>` or `<reference_note>` as preconditions and scope `<success_criteria>` to properties the litmus section already makes checkable.

**Why this is separate.** The three skills carry the pattern verbatim, so correcting one diverges it from two untouched siblings — the divergence `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`'s defect-class-sweep rule exists to prevent. The fix is one cross-plugin pass over three plugins, each needing its own `skill-auditor` gate and version bump.

**Evidence.** Raised by `instructions:skill-auditor` against `rust-test-standards` during the predicate-seam correction, which names the cross-plugin scope in the finding itself.

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
