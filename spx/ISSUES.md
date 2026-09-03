# ISSUES — product-level hygiene

Cross-cutting imperfections noticed in the marketplace that do not belong to a single spec node. Each entry names a file, the exact rule it violates, and the smallest unit of work that resolves it.

`/contextualize` reads this file at product-root context-load time; the entries are visible to any session that enters `spx/`.

## Product-level assertions carry no evidence tags

The `/understand` artifact-placement table's Product spec row declares product-level assertions verified by linked evidence, and the `<verification_types>` rule requires each assertion to select test, evaluate, or audit from its real verdict. The six ALWAYS/NEVER bullets under `## Product-level assertions` in `spx/outcomeeng.product.md` carry no evidence tag, so the root spec fails the verification claim the closed taxonomy now makes for its artifact kind.

**Resolution shape**: route each of the six assertions through `/verify` to select its verification type from the verdict its real subject can produce — several are semantic constraints that resolve to `[audit]`, while the verbatim-identity rules may support `[eval]` evidence — then tag each assertion and establish any path-bearing evidence the selection requires.

**Why separate**: the tagging is a `/verify` pass over the product root with its own evidence-selection and possible eval-authoring chain, independent of the changeset that closed the placement taxonomy and surfaced the gap.

**Evidence.** Surfaced by the CI changeset review on the closed-taxonomy change (PR #517), which compared the new Product spec row's verification claim against the untagged root-spec assertions.

## Architecture standards restate the /understand decision template

A standard begins by loading the matching `/understand` template when one exists; no skill encodes the template's shape, because a restated shape drifts the moment the template advances. The prose plugin conforms. Six language-plugin files still restate the ADR section list inline: `src/plugins/python/skills/python-architecture-standards/SKILL.md` and `src/plugins/python/skills/architect-python/SKILL.md`, the TypeScript pair `src/plugins/typescript/skills/typescript-architecture-standards/SKILL.md` and `src/plugins/typescript/skills/architect-typescript/SKILL.md`, and the Rust pair `src/plugins/rust/skills/rust-architecture-standards/SKILL.md` and `src/plugins/rust/skills/architect-rust/SKILL.md`.

**Resolution shape**: replace each restated section list with a pointer that loads the decision template through the live `/understand` foundation, keeping only language-specific content rules (DI patterns, testability constraints, per-language verification routing). One sweep across the three language plugins, gated by `instructions:skill-auditor` per plugin.

**Evidence**: operator directive during the prose five-skill refactor (PR #523): template shape lives only in the `/understand` templates, and every standard begins by loading its template.

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
- `spec-tree` — `audit-eval-evidence/references/evidence-model.md` (143)
- `typescript` — `architect-typescript/references/typescript-principles.md` (144), both `code-typescript/references/*.md` (116, 138), `typescript-test-standards/references/exception-implementations.md` (109)
- `work` — both `draw-excalidraw/references/*.md` (128, 202), both `sanitize-powerpoint/references/*.md` (134, 136)

A table of contents is satisfied by a `## Contents` section, an XML `<contents>` block, or a `<reference_index>` section; files already using one of those forms are excluded from the count above.

**Evidence.** Surfaced while satisfying the same requirement for the five `architect-python` references, which were fixed in the changeset that found it. The remaining twenty-six lie in plugins that changeset does not touch.

**Resolution shape**: add a table of contents to each file in the form its surrounding skill already uses — `## Contents` for markdown-structured references, `<contents>` for XML-structured ones — listing every top-level section. Run `instructions:skill-auditor` over each affected skill afterward. The sweep divides cleanly by plugin, so it can land as one changeset per plugin rather than one large one.

**Revisit condition.** Resolve per plugin when that plugin next needs a reference-file change, or as one dedicated sweep. `create-subagent` is the highest-value single target: seven files, 4,646 lines, the largest partial-read exposure in the marketplace.

## Auditors read a conforming absent `<failure_modes>` section as a gap

`/agent-prompt-standards` `<failure_mode_writing>` prescribes omitting `<failure_modes>` from a skill that has not failed yet: "Never invent failure modes... Add failure modes as they occur in real usage." A new skill therefore conforms by carrying no such section. `instructions:audit-skill` nonetheless raises the absence as a `worth-improving` warning, and its own remedy then restates the standard back — "once a real near-miss occurs", "do not fabricate one if none has occurred". `spec-tree:changes-reviewer` reads the same absence as a coordination-note gap.

Across the contribute-plugin consolidation this fired six times over three skills and four verification rounds, each costing a full re-audit or re-review cycle to answer with the same reasoning. The warning is unactionable by construction: no edit satisfies it, and declining it leaves the next verifier to raise it again.

**Resolution shape**: teach the audit surface that the absence is conforming. Either `instructions:audit-skill` stops raising a bare missing-`<failure_modes>` as a finding for a skill whose history shows no observed failure, or it raises it only where a governing node, changelog, or commit history records one the skill omits. The reviewer's coordination-note rule needs the matching case: a note tracking work a standard declares complete-as-absent represents no future work, so its removal closes the item.

**Why separate**: the fix belongs to the `instructions` plugin's audit skill and to the review prompt, neither of which any skill-content changeset touches. Fixing it inside a plugin's own changeset would leave the next plugin paying the same rounds.

**Evidence**: `instructions:skill-auditor` warnings on `src/plugins/contribute/skills/open-upstream-issue/SKILL.md` and `src/plugins/contribute/skills/sync-fork/SKILL.md`, three rounds running, alongside `spec-tree:changes-reviewer` debt findings on the same absence in review runs `2026-08-17_00-39-40-323-2100d0f7fbde` and `2026-08-17_00-58-42-318-56d83c759ed7`.

## The non-interactive git guard sits on the command that cannot prompt

`GIT_TERMINAL_PROMPT=0` guards `gh pr create` in both `src/plugins/spec-tree/skills/open-pr/SKILL.md` (lines 87 and 116) and `src/plugins/contribute/skills/open-upstream-pr/SKILL.md` (lines 125 and 149). `gh` authenticates through its own stored credential against the GitHub API, so the variable has little to act on there. The `git push` each skill runs immediately before is the command that blocks an unattended run on a credential or host-key prompt, and neither carries the guard.

Moving it is not a text edit. Both skills declare narrow prefix-matched grants — `Bash(gh pr create:*)`, `Bash(git push:*)`, `Bash(git push -u origin HEAD:refs/heads/*)` — and an `ENV=value` prefix changes the command string the grant matches against. Whether Claude Code's matcher tolerates an environment-variable prefix decides between three different fixes: move the variable, drop it, or reach non-interactivity through `git -c` configuration. That question is unanswered, and the same answer governs both plugins.

**Resolution shape**: establish how the Bash grant matcher treats an environment-variable prefix, then apply one fix across both skills in the same change. Gate each plugin with `instructions:skill-auditor`.

**Why separate**: the pattern predates either changeset that touched these files and is identical in both plugins, so fixing it inside one plugin's changeset would leave the marketplace holding two spellings of the same convention.

**Evidence**: surfaced by the `instructions:skill-auditor` verdict on `src/plugins/contribute/skills/open-upstream-pr/SKILL.md` during the contribute-plugin consolidation, then found unchanged in `open-pr` by grepping `GIT_TERMINAL_PROMPT` across `src/plugins/`.

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

## Plugin changelog titles use two forms

Ten plugin changelogs open with "# Changelog — {plugin} plugin"; the prose changelog opens with "# Prose plugin changelog", the form the prose canon's em dash rule requires. One sweep renames the other ten titles to the dash-free form. Surfaced by the CI changeset review on the chat-voice branch; deferred there because the sweep touches ten plugins outside that changeset.

## Two verifier rules collide on pinning a spec-declared tuning value

The changes-reviewer requires a test to pin `SIGNAL_GRACE_SECONDS` to the spec's two-second
grace period with an independent literal, citing the mutation-check rule in
`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`;
the test-evidence-auditor rejects exactly that literal as a source-ownership violation, citing
`spx/12-shipped-scripting.adr.md` — a test restating a spec-declared value is a second declaration
whose agreement is audit evidence. The operator ruled the ADR governs: no literal pin, the
spec-to-constant agreement stays audit evidence, and the reviewer finding is dropped as unbacked.

**Resolution shape**: amend one of the two decisions so they compose — either scope the
mutation-check rule to exclude spec-declared values whose agreement the ADR routes to audit, or
carve an exception in the ADR for magnitude pins — so a reviewer and an evidence auditor reading
both rules reach one verdict.

**Evidence**: review runs `2026-08-31_00-51-25-312-913144ba274d`, `2026-08-31_00-56-11-491-d5964232aade`,
and `2026-08-31_01-31-25-945-65d0eb76b2fc` (blocking) each requested the pin; evidence-audit
verdicts on heads `629c24b790980aefa873ee6ffd4212e5f8611151` and `4ede96f0d1cb1c3855792f6c04bcca2c65e3e1ee`
rejected or upheld removal of the same literal; operator ruling recorded in the PR #549 body.
