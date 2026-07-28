# Issues: Subagent Authoring

Known defects in the subagent cluster. Coordination note; not spec truth.

## Consolidate the create-subagent bundle

A complete-bundle skill audit identified two maintenance recommendations after
the invocation-check repair converged:

- `src/plugins/instructions/skills/create-subagent/SKILL.md` repeats prompt
  structure, XML, invocation, and management guidance that also appears in
  `references/write-subagent-prompts.md` and `references/subagents.md`; the
  authored overview remains under the 500-line limit, but the duplication
  leaves little room for future required guidance.
- `references/subagents.md`, `references/orchestration-patterns.md`,
  `references/error-handling-and-recovery.md`, and
  `references/debugging-agents.md` contain fast-moving benchmark or runtime
  performance figures that do not define stable authoring behavior.

Required handling: map each duplicated overview section to its owning reference,
retain only trigger-time and fast-path guidance in `SKILL.md`, replace unstable
figures with durable decision guidance or current authoritative citations, and
exercise the affected create/edit paths in fresh contexts. Regenerate both runtime
trees, run the focused skill checks, and obtain a complete-bundle
`instructions:skill-auditor` verdict before publication.

The overview's section order belongs to the same rework. `SKILL.md`'s one hard rule
— {{! term('configured_agents') !}} are black boxes that cannot interact with users —
sits inside `<critical_constraint>` nested under `<execution_model>`, after
`<quick_start>`, `<file_structure>`, and `<configuration>`. A rule whose violation
manifests as a silently hung {{! term('configured_agent') !}} reads better near the
objective, and the sibling `/create-skill` surfaces its rules in a top-level block.
Decide the builder-skill section taxonomy once during the rework rather than moving
this block ahead of it.

This is a separate content-consolidation refactor across the overview and five
references. Each skill audit binds to the exact committed head it ran against, so
this entry records finding content only and makes no standing approval claim.
`spx/43-instructions.enabler/21-subagents.enabler/PLAN.md` carries the
`/subagent-standards` extraction that subsumes the duplication half of this entry;
the unstable-figure findings below stand on their own.

A complete-bundle skill audit added four `WARNING` findings that belong to this
refactor, because each removes or reworks reference/overview content rather than
propagating a rename:

- f-005 — `references/context-management.md` `<framework_support>` describes
  LangChain and LlamaIndex memory patterns that neither Claude Code nor Codex
  custom-agent configuration integrates; cut to the file-based memory pattern the
  config actually supports (~45 lines).
- f-006 — `references/error-handling-and-recovery.md` presents uncited precise
  percentages ("32% of failures", "28%", "24%") as measured fact; cite the source
  or reframe qualitatively, per `/agent-prompt-standards` `<failure_mode_writing>`.
- f-007 — `SKILL.md` `<failure_modes>` sole entry documents a failure in authoring
  this SKILL.md (line budget) rather than a failure while using the skill to create
  a subagent; relocate to a maintainer note or drop the section.
- f-008 — `references/debugging-agents.md` `<monitoring>` prescribes dashboards,
  alert-threshold tables, and per-invocation cost tracking as if the product ships
  that observability; cut or reframe as optional external guidance (~55 lines).

Reconcile with `spx/43-instructions.enabler/ISSUES.md` entries 3 (verdict-row
taxonomy), 4 (audit-skill eval coverage), 7 (runtime terminology), and 9
(audit-skill target-argument convention) before editing the auditor surface.

## `/create-subagent` states a description rule `/agent-prompt-standards` owns

`spx/43-instructions.enabler/instructions.md:12` centralizes prompt voice,
description, and constraint conventions in `/agent-prompt-standards` for skills
**and** subagents, and
`spx/43-instructions.enabler/21-subagents.enabler/subagents.md:20` forbids
restating a canonical rule inside `/create-subagent`. The `<clear_triggers>` block
in `src/plugins/instructions/skills/create-subagent/references/subagents.md` still
carries a description-convention statement of its own rather than deferring
outright, and `write-subagent-prompts.md` carries a parallel
`<anti_pattern name="unclear_trigger">` block.

This is a placement question, not a disagreement: every worked example, the
`audit-subagent` description-style rule, the two `instructions` auditor
descriptions, and all ten `spec-tree` agent descriptions now use the directive
form `/agent-prompt-standards` `<description_style>` prescribes. What remains is
that the rule is stated in more than one file.

**Resolution shape**: resolve inside the `/subagent-standards` extraction above.
Decide whether `<clear_triggers>` keeps a specificity rule that cites the standard
for wording, or disappears into `/subagent-standards` entirely, then apply the same
choice to `write-subagent-prompts.md`'s parallel block in one pass.

**Evidence.** The changeset that renamed these skills first introduced a competing
convention — `audit-subagent`'s description-style rule forbade the directive
pattern, and two worked examples moved from directive to passive wording to match
it. Local review caught that the same changeset both created the instances and
recorded them as deferred. The competing rule and the reworded examples were
reverted to the standard, leaving only the placement question above. A
`subagent-auditor` run had separately recommended rewriting
`src/plugins/instructions/agents/subagent-auditor.md`'s directive description into
the passive form, citing those examples; that recommendation was dropped, and the
examples it cited no longer teach the weaker form.

## `/audit-subagent`'s objective states its categories in a second sentence

`src/plugins/instructions/skills/audit-subagent/SKILL.md` opens with the verdict
sentence and then names the four finding categories in a second sentence, while
the sibling `src/plugins/instructions/skills/audit-skill/SKILL.md` carries the
equivalent content in one sentence joined by a semicolon.

Successive `instructions:skill-auditor` runs read this differently. One run
flagged the shortened objective and required the categories be named; a later run
accepted the categories and flagged the second sentence. The two governing
references model the shape differently. `/skill-standards`
`references/auditor-skeleton.md` requires `<objective>` to carry the finding
categories, and its worked example states them in a second sentence.
`/agent-prompt-standards` `<objective_shape>` holds an objective to one sentence,
reaching for a second only when the output has two distinct parts, and gives the
canonical auditor shape as a single sentence whose em-dash clause names the
categories. Naming categories is settled; whether they form a second part is not.

Required handling: decide once whether an auditor's finding-category clause is a
distinct output part or a subordinate clause, record it so `<objective_shape>`
and the skeleton's worked example stop modelling opposite shapes, and bring both
auditor objectives onto the chosen shape.

Source: `instructions:skill-auditor` finding `f-009`, severity `WARNING`, on the
changeset merged as PR 488, reconciled against an earlier run's opposing finding.
