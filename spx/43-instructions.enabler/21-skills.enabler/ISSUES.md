# Issues: Skill Authoring

Actionable findings from the post-merge skill audit of PR 458 at
`f5aa313016964a10854117e026ec4c3529106490`.

## Split router authority by workflow needs

`src/plugins/instructions/skills/create-skill/SKILL.md:5` grants `Bash`, `Write`,
`WebFetch`, and `WebSearch` to every route. Read-only audit and pattern-explanation
routes inherit mutation and network capabilities they do not use.

Required handling: narrow the router's top-level `allowed-tools` surface or split
routes whose authority requirements differ. Preserve the tools required by creation
and improvement workflows without granting them to read-only routes.

Source: skill-auditor finding `f-003`, rule `overbroad_allowed_tools`, severity
`WARNING`.

## Reconcile the auditor Bash capability contract

`src/plugins/instructions/skills/create-skill/templates/auditor-skill.md:5` now uses
`allowed-tools: Read, Grep, Glob, Skill`. The post-merge audit requires `Bash` for
auditor command-based verification, while an earlier audit rejected bare `Bash` as
overbroad. `/skill-standards`'s command-capability rules also require command-specific
`Bash(<command>:*)` grants. A generic auditor template cannot select those commands
without knowing the generated auditor's workflow.

Required handling: decide whether every auditor requires `Bash`, define how a generic
template expresses least-privilege command grants, and align `/skill-standards`,
`/audit-skills`, and the auditor template so the same surface cannot be rejected both
for granting and omitting bare `Bash`.

Source: skill-auditor finding `f-004`, rule `read_only_audit_capabilities`, severity
`REJECT`, reconciled with the earlier `overbroad_allowed_tools` rejection.

## Revalidate after exercise-driven edits

`src/plugins/instructions/skills/create-skill/workflows/create-new-skill.md:79`
allows the representative exercise to trigger iterative edits after deterministic
checks and the skill audit have already completed. The final bundle can therefore
differ from the bundle those gates evaluated.

Required handling: run the representative exercise before final validation, or loop
every exercise-driven edit back through deterministic checks and the complete-bundle
skill audit before publication.

Source: PR 458 review comment `3610850053`, classified as `DEBT` in the `evidence`
category after merge.

## Consolidate the create-subagent bundle

The approved complete-bundle skill audit at
`401712deec4ee7eb307c4a02947b31f5850ea72d` identified two maintenance
recommendations after the invocation-check repair converged:

- `src/plugins/instructions/skills/create-subagent/SKILL.md` repeats prompt
  structure, XML, invocation, and management guidance that also appears in
  `references/write-subagent-prompts.md` and `references/subagents.md`; the
  authored overview remains under the 500-line limit at 472 lines, but the
  duplication leaves little room for future required guidance.
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

This is a separate content-consolidation refactor across the overview and five
references. It does not block the current rename and invocation-lifecycle repair,
which the same audit approved with no must-fix findings.

The complete-bundle skill audit after the rename and the xml_tag_formatting fix
added four `WARNING` findings that belong to this refactor and are deferred here,
not fixed in the rename changeset, because each removes or reworks
reference/overview content rather than propagating the rename:

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

## Give the subagent cluster a canonical-rules owner (symmetric triad)

The skills-about-skills cluster resolves rule ownership with three peers — builder
`/create-skill`, canonical-rules owner `/skill-standards`, auditor `/audit-skills` —
and `skills.md:17,24` bind the discipline: `/skill-standards` owns every rule
`/audit-skills` enforces, and no rule is restated inside the builder or the auditor.
The subagent cluster ships only a builder (`/create-subagent`) and an auditor
(`/audit-subagents`) with no canonical-rules owner, so the auditor has nothing to
load but the builder's seven references and keeps a parallel rulebook of its own.

Spec grounding:

- `instructions.md:12` centralizes prompt voice, description, and constraint
  conventions in `/agent-prompt-standards`, shared across skills **and subagents**.
  `src/plugins/instructions/skills/audit-subagents/SKILL.md:116-124`
  (`<area name="prompt_craft">`) says "Check against `/agent-prompt-standards`
  conventions" and then re-lists Voice, Description, Constraint, and Anti-patterns —
  a restatement of content that assertion places in `/agent-prompt-standards`.
- The restatement is a defect class, not a single site.
  `src/plugins/instructions/skills/audit-skills/SKILL.md:73-217`
  (`<evaluation_areas>`, including its own `prompt_craft` and `anti_patterns`
  areas) restates `/skill-standards` the same way, violating `skills.md:24` directly.
  `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`
  property 7 requires a valid finding to be fixed across every same-class instance;
  fixing `audit-subagents` alone would be an invalid single-site fix.
- Subagent **structure** rules — frontmatter fields, tool grants, model selection,
  XML structure, the `inherit` prohibition — are governed by no assertion. Only
  prompt *craft* is reached by `instructions.md:12`; the subagent pair has no
  single-source assertion analogous to `skills.md:17,24`.

Decision (operator-approved): Shape A — symmetric triad. Introduce
`/subagent-standards` as a reference skill owning the canonical subagent rules;
`/create-subagent` and `/audit-subagents` both load it and neither restates. This
restores the `instructions.md:11` builder/auditor separation (the auditor stops
depending on the builder for the rules it enforces) and gives `/audit-subagents`
a legitimate load target so its `<evaluation_areas>`/`<anti_patterns>` rulebook can
be removed.

Required handling:

- Declare the architecture in the spec before the skill edits (truth flows down):
  add the subagent-cluster single-source assertion(s) mirroring `skills.md:17,24`,
  and resolve the node-placement question — `skills.md`'s `PROVIDES` covers only
  "SKILL.md files" while its parent covers skills **and** subagents, so the
  subagent cluster currently has no node-level spec home. Whether the subagent
  cluster becomes its own sibling node under `43-instructions.enabler` or
  `skills.md` broadens to cover both clusters is an index/decomposition question
  routed through `/decompose`, which owns proving the dependency consequence.
- Add `/subagent-standards`; migrate canonical subagent rules into it from
  `/create-subagent` and from the embedded rulebooks in both auditors.
- Sweep the defect class: strip `<evaluation_areas>` and `<anti_patterns>` from
  **both** `/audit-subagents` and `/audit-skills`; each loads its standards and
  enforces them without restating.
- Close the evidence gap flagged for `/audit-skills` in
  `spx/43-instructions.enabler/ISSUES.md` entry 4 for `/audit-subagents` too:
  both auditors are LLM-driven verdict producers and require `[eval]` evidence per
  `spx/15-spec-coverage.adr.md`, yet every assertion here is `[audit]`/`[review]`.
- Regenerate both runtime trees, run the focused skill checks, dispatch the typed
  `skill-auditor` on every changed skill surface (required for any skill-surface
  edit), run `changes-reviewer`, then `just check-full`.

This is a separate larger concern: a new skill, spec restructuring with a
decomposition decision, content migration out of a 472-line builder, and a
two-auditor sweep — reason recorded per `spx/15-merging.pdr.md`. It subsumes the
"Consolidate the create-subagent bundle" entry above (extracting the canonical
rules into `/subagent-standards` is that consolidation under a governing
principle) and should reconcile with `spx/43-instructions.enabler/ISSUES.md`
entries 3 (verdict-row taxonomy), 4 (audit-skills eval coverage), 7 (runtime
terminology), and 9 (audit-skill target-argument convention). Begin it as the next
changeset after PR 465 merges, starting with the spec change.
