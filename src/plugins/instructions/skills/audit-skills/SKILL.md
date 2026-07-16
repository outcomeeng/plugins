---
name: audit-skills
description: >-
  SKILL.md audit methodology preloaded by the skill-auditor agent. The main
  conversation reaches this audit only through that agent.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

{!% require_skill 'instructions:skill-standards' %!}

{!% require_skill 'instructions:agent-prompt-standards' %!}

<dispatch_gate>

This audit runs in the skill-auditor agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch the skill-auditor agent instead of running this audit here. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>
A verdict on skill content against `/skill-standards` and `/agent-prompt-standards` — APPROVED, or REJECTED with each rejecting finding naming the file and line, the violated rule, the evidence, and the required correction.
</objective>

<constraints>
- NEVER modify files during audit - ONLY analyze and report findings
- NEVER report a score or a non-rejecting observation; emit only the terminal verdict and rejecting findings
- MUST read all reference documentation before evaluating
- ALWAYS provide file:line locations for every finding
- NEVER implement, patch, or generate replacement content; each rejecting finding states only the required correction needed to satisfy the violated rule
- NEVER make assumptions about skill intent - flag ambiguities as findings
- MUST complete all evaluation areas (YAML, Structure, Content, Anti-patterns)
- ALWAYS apply contextual judgment - what matters for a simple skill differs from a complex one

</constraints>

<focus_areas>
During audits, prioritize evaluation of:

- YAML compliance (name length, description quality by skill role, `argument-hint` when arguments are used)
- Command capabilities (argument usage and integration, `!`-dynamic-context safety, `allowed-tools` tool-restriction security, `@` file references)
- Pure XML structure (required tags, no markdown headings in body, proper nesting)
- Progressive disclosure structure (SKILL.md < 500 lines or a standards-conformant eager foundation, references one level deep)
- Conciseness and signal-to-noise ratio (every word earns its place)
- Required XML tags (objective, success_criteria)
- Conditional XML tags (appropriate for complexity level)
- XML structure quality (proper closing tags, semantic naming, no hybrid markdown/XML)
- Constraint strength (MUST/NEVER/ALWAYS vs weak modals)
- Error handling coverage (missing files, malformed input, edge cases)
- Example quality (concrete, realistic, demonstrates key patterns)
- **Operational effectiveness** (verifiable success criteria, verification gates, failure modes)
- **Procedural/operational balance** (skill states both how to DO the work and how to KNOW it was done right)

</focus_areas>

<audit_workflow>
**MANDATORY**: Read standards FIRST, before auditing:

1. Read `/skill-standards` — the canonical standards for skill structure, frontmatter, XML tags, progressive disclosure, skill types, reference patterns, code-fence rules, bash restrictions, validation, and script testing. Then check for `spx/local/skills.md` at the repository root and read it if it exists.
2. Read `/agent-prompt-standards` — voice, description style, constraint language, and prose anti-patterns. Already injected above.
3. Read the target skill files (SKILL.md and any `references/`, `workflows/`, `templates/`, `scripts/` subdirectories).
4. Read `${CLAUDE_SKILL_DIR}/references/xml-structure-examples.md` and `${CLAUDE_SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated violation examples. When the target carries command-capability fields — `argument-hint`/`arguments`, `allowed-tools`, `!`-dynamic context, or `@` file references — also read `/skill-standards`'s `references/command-capabilities.md` for the rules that govern that surface. When the target is an `audit-*` skill, also read `/skill-standards`'s `references/auditor-skeleton.md` — the `/skill-standards` table loaded in step 1 directs you to it; read the file itself explicitly — the canonical auditor structure the `auditor_skeleton_violation` check verifies against. When scoped content includes any file under `scripts/`, also read `/skill-standards`'s `references/script-standards.md` and audit every bundled script against its validation-message and pre-inclusion testing rules.
5. Handle edge cases:
   - If `/skill-standards` or `/agent-prompt-standards` is unreadable, emit `REJECTED` with a finding naming the unreadable standard and the incomplete audit coverage.
   - If YAML frontmatter is malformed, emit a rejecting finding naming the malformed field or delimiter.
   - If the skill references external files that don't exist, emit a rejecting finding naming each broken reference and its required correction.
   - If the skill references a bundled plugin file through repository-local authored or generated plugin paths, legacy plugin-root paths, or an authored Codex-only skill-directory token, flag as a portable file-reference defect.
   - If the skill is under 100 lines, evaluate it as a simple skill without emitting a classification or context line.
6. Evaluate the target skill against the standards loaded in steps 1-2.

**Use ACTUAL patterns from `/skill-standards`, not memory.** Never read `create-skills/references/` for standards — that directory is workflow content only.
</audit_workflow>

<evaluation_areas>
<area name="yaml_frontmatter">
Check for:

- **name**: Lowercase letters, numbers, and hyphens only; max 64 chars; matches directory name
- **description**: Max 1024 chars, no XML tags; directive style for invoked skills; passive style for reference skills and exact-name protocol or loop-body skills
- **user-invocable**: `false` for reference skills loaded by other skills; default user-invocable for agent-preloaded audit skills with a passive description and `<dispatch_gate>`
- **argument-hint**: Present when the skill takes arguments (`$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, or a declared `$name`); omit for self-contained skills

</area>

<area name="structure_and_organization">
Check for:
- **Progressive disclosure**: SKILL.md is an overview (<500 lines) with one-level references, or an eager foundation whose always-loaded canonical payload satisfies `/skill-standards`' exception
  - Every inlined reference would otherwise be mandatory on every invocation
  - Inlining removes secondary discovery/read obligations and leaves one canonical copy
  - Repeated summaries, examples, and failure explanations are consolidated
  - Conditional operational detail, templates, examples, and repository-local overlays remain separate
  - The resulting eager payload is measured in characters and audited for effectiveness and internal consistency; report the measured character count
- **XML structure quality**:
  - Required tags present (objective, success_criteria)
  - Conditional tags appropriate for skill type (quick_start for on-demand tools only — omit for foundation/gate/validator/reference skills)
  - No markdown headings in body (pure XML)
  - Proper XML nesting and closing tags
  - Conditional tags appropriate for complexity level
- **File naming**: Descriptive, forward slashes, organized by domain

</area>

<area name="content_quality">
Check for:
- **Conciseness**: Only context Claude doesn't have. Apply critical test: "Does removing this reduce effectiveness?"
- **Clarity**: Direct, specific instructions without analogies or motivational prose
- **Specificity**: Matches degrees of freedom to task fragility
- **Examples**: Concrete, minimal, directly applicable

</area>

<area name="operational_effectiveness">
Check whether the skill provides operational wisdom, not just procedural steps:

**Success Criteria Verifiability**:

- Are success criteria concrete and testable? (commands to run, thresholds to check)
- Can "did I succeed?" be answered with a boolean, not a judgment call?
- ❌ Bad: "Task complete when migration is done"
- ✅ Good: "Coverage on src/foo.ts must be ≥86%. Run: `pnpm test --coverage | grep foo.ts`"

**Verification Gates**:

- Are there explicit "STOP and verify before proceeding" checkpoints?
- Do gates have pass/fail criteria with specific commands?
- ❌ Bad: "Verify coverage matches before removing legacy tests"
- ✅ Good: "GATE 2: Run `pnpm test --coverage` for both legacy and SPX. If delta >0.5%, STOP."

**Failure Modes Documentation**:

- Does the skill document what can go wrong in practice?
- Are failures from actual usage, not hypotheticals?
- Does each failure have: what happened, why it failed, how to avoid?
- ❌ Bad: No failure modes section
- ✅ Good: "Failure 1: Agent compared coverage per-story instead of per-file. Why: Multiple stories share one legacy file. Avoid: Always compare at legacy file level."

**Example Concreteness**:

- Do examples show real outputs with actual values?
- Can the output be compared to the example to verify correctness?
- ❌ Bad: "Coverage should match between legacy and SPX tests"
- ✅ Good: "Legacy: 24 tests, 86.3% on state.ts. SPX: 24 tests, 86.3% on state.ts. ✓ Match"

**Procedural vs Operational Balance**:

- Procedural = HOW to do steps
- Operational = how to KNOW it was done right
- Skills need both; flag if heavily imbalanced toward procedural

</area>

<area name="command_capabilities">
Check the capability surface a SKILL.md carries that a slash command also had, against `/skill-standards` `references/command-capabilities.md` (read it when any of these apply):

**Argument usage**:

- `argument-hint` is present when the skill takes arguments.
- `$ARGUMENTS` preserves the full instruction string. It is valid when the skill accepts free-form natural-language instructions, forwards instructions to another skill, or needs to distinguish empty input from an instructed change.
- `$ARGUMENTS[N]` / `$N` are valid for stable positional tokens.
- Every argument declared in `arguments` is substituted as `$name` in the body, and every `$name` the body substitutes is declared — neither orphaned.
- A migration from `$ARGUMENTS` to `arguments` preserves behavior only when the named argument's token boundary matches the skill's intent. Flag free-form whole-string skills that use a single named positional argument without proving rest-of-line capture.
- Empty-argument handling is stated when the skill requires an argument or defines a no-argument fallback.
- Authored plugin source skills target Claude Code SKILL.md syntax. Codex-specific rendering belongs to the build step; flag source prose that claims Codex consumes a Claude-only form directly, but do not flag Claude-supported source syntax merely because Codex may need generated adaptation.

**Dynamic-context safety** (`!`-backtick blocks inside `<context>`):

- Loaded state is directly relevant to the skill's task — not injected context the skill never reads
- Each command is filtered to bounded output and never grows monotonically (the block fires on every skill load)

**Tool-restriction security** (`allowed-tools`):

- Bash is restricted to the narrowest verb pattern that works (`Bash(git add:*)`, not bare `Bash` or `Bash(git *)`) when specific verbs suffice
- Destructive and network tools (`Write`, `Bash`, `WebFetch`) are absent unless the task needs them — a read-only or analysis skill cannot delete, force-push, deploy, or exfiltrate
- An `audit-*` skill carries `Read, Grep, Glob, Bash` (plus `Skill` when composing) and never `Write`/`Edit`

**File-reference portability**:

- Skill-bundled files use `${CLAUDE_SKILL_DIR}/references/...` or `${CLAUDE_SKILL_DIR}/scripts/...` in authored source. {!# no-codex-skill-dir-rewrite #!}
- Generated Codex output may contain Codex's skill-directory token; authored source must not.
- Repository-local authored or generated plugin paths and legacy plugin-root paths are defects in skill prose when they identify bundled plugin files.

</area>

<area name="prompt_craft">
Check against `/agent-prompt-standards` conventions:

- **Voice**: Uses imperative mood for instructions, "Claude" for failure modes/tendencies. Never "the agent", "the model", or "you"
- **Description style**: Directive pattern (ALWAYS + optional NEVER). Language-after-artifact ordering. Matches user speech
- **Constraint language**: Strong modal verbs (MUST/NEVER/ALWAYS) in constraint blocks. No weak modals ("should", "try to", "consider") in constraints
- **Anti-patterns**: No banned phrases ("helpful assistant", "helps with", "processes data", "please", "if possible"). No structural anti-patterns (explaining Claude to Claude, motivational prose, empty disclaimers)
- **Conciseness**: Only information Claude doesn't already have. Concrete over abstract
- **Failure modes**: Written from actual experience, use "Claude" as subject, structured as what/why/how-to-avoid
- **Objective shape**: `<objective>` states the observable output in a definite shape — not an actor ("The skill", "Claude") or a bare activity verb ("Audit", "Evaluate", "Generate"), and not a behavioral claim. It is **one sentence** (two only when the output has two distinct parts): the output target, not a summary of the skill. Every clause names a property of the output; a clause describing *when* the skill runs (→ `description`), *how* it runs (→ `<workflow>`), or *what it avoids* (→ `<constraints>`) is bloat that must be cut. `<success_criteria>` proves the output (its sound-making properties), never a re-list of the workflow steps; the two do not duplicate (per `/agent-prompt-standards` `<objective_shape>`). For an `audit-*` skill, check the canonical structure in `/skill-standards` `references/auditor-skeleton.md`; code-auditor and test-auditor objectives may use the skeleton's APPROVED/REJECTED field form without a separate finding-category sentence

</area>

<area name="anti_patterns">
Flag these issues:
- **markdown_headings_in_body**: Using markdown headings (##, ###) in skill body instead of pure XML
- **missing_required_tags**: Missing objective or success_criteria
- **actor_or_activity_objective**: `<objective>` opens with an actor ("The skill…", "Claude…") or a bare activity verb ("Audit…", "Evaluate…", "Generate…") instead of naming the observable output it produces
- **objective_criteria_duplication**: `<objective>` and `<success_criteria>` restate the same content — the objective names the output, success_criteria proves it
- **objective_bloat**: `<objective>` runs past one sentence (two when the output has two distinct parts) or carries clauses describing when the skill runs, how it runs (steps, gates, orchestration), or what it avoids — content that belongs in `description`/`<workflow>`/`<constraints>`, not the output target
- **auditor_skeleton_violation**: an `audit-*` skill deviating from `/skill-standards` `references/auditor-skeleton.md` — `<output_format>` instead of `<verdict_format>`, a non-`<audit_workflow>` procedure name, a `<quick_start>` block, or an objective outside the skeleton's verdict forms. The prose auditors (`audit-prose`, `audit-internal-docs`) are exempt from the procedure-name and `<dispatch_gate>` checks per the skeleton's `<prose_variant>`
- **hybrid_xml_markdown**: Mixing XML tags with markdown headings in body
- **unclosed_xml_tags**: XML tags not properly closed
- **vague_descriptions**: "helps with", "processes data"
- **passive_description**: Uses passive "Use when" instead of directive "ALWAYS invoke... NEVER X without this skill"
- **too_many_options**: Multiple options without clear default
- **deeply_nested_references**: References more than one level deep from SKILL.md
- **windows_paths**: Backslash paths instead of forward slashes
- **bloat**: Obvious explanations, redundant content
- **unverifiable_success_criteria**: Success criteria that can't be tested with a command or boolean check
- **no_verification_gates**: Complex multi-step skill without explicit stop-and-check points
- **no_failure_modes**: Skill lacks documentation of what went wrong in practice
- **abstract_examples**: Examples that show patterns but not concrete values/outputs
- **orphaned_references**: Files in `references/` not cited from SKILL.md or any workflow file. Verify with `grep -rn "<filename>" <skill-dir>/`. Orphans inflate token cost via speculative reads (Claude tends to open siblings of cited references) and indicate either dead content or a missing cross-reference. Flag as critical: either delete the file or add an explicit `<required_reading>` reference from the workflow that needs it.
- **heavy_context_block**: `<context>` bash commands that produce verbose or growing output (session lists, full file contents, cache enumerations) without filtering. The `<context>` block fires on every skill load — including false-positive activations from directive descriptions — so heavy commands compound. Reject and require a bounded command (e.g., `--status doing,todo`, `head -N`) or relocation to the workflow file that consumes the data.
- **orphaned_argument**: an argument declared in `arguments` that the body never substitutes, or a `$name` substituted in the body that `arguments` never declares. Flag as critical — the skill takes input it ignores, or substitutes an undefined name.
- **missing_argument_hint**: the skill takes arguments but omits `argument-hint`, so `/` autocomplete gives the user no signal about expected input. Reject and require an accurate hint.
- **argument_capture_regression**: a free-form instruction skill replaces `$ARGUMENTS` with a named positional argument or numbered token without proving the replacement captures the same whole input. Flag as critical — the skill can silently drop words from user instructions.
- **codex_rendering_assumption**: authored source claims Codex directly consumes Claude-only SKILL.md syntax rather than treating Codex output as a generated rendering concern. Reject when the assumption produces a broken or misleading generated Codex surface; otherwise emit no finding.
- **overbroad_allowed_tools**: `allowed-tools` grants bare `Bash`, `Bash(git *)`, or a destructive/network tool the skill's task does not need, re-admitting the destructive or exfiltrating commands a narrower grant would bar. Flag as critical for security-sensitive skills.
- **irrelevant_dynamic_context**: a `<context>` `!` block injecting state the skill never reads. Reject because it taxes every load without payoff.
- **nonportable_bundled_file_reference**: skill prose references a bundled plugin file through repository-local authored or generated plugin paths, legacy plugin-root paths, or an authored Codex-only skill-directory token. Flag as critical: authored source must use `${CLAUDE_SKILL_DIR}/references/...` or `${CLAUDE_SKILL_DIR}/scripts/...` for files bundled with the current skill, or describe the owning workflow/capability when the file belongs elsewhere. {!# no-codex-skill-dir-rewrite #!}

</area>
</evaluation_areas>

<contextual_judgment>
Apply judgment based on skill complexity and purpose:

**Simple skills** (single task, <100 lines):

- Required tags only is appropriate - don't flag missing conditional tags
- Minimal examples acceptable
- Light validation sufficient
- Operational effectiveness: success criteria should still be verifiable, but gates/failure modes not expected

**Complex skills** (multi-step, external APIs, security concerns):

- Missing conditional tags (security_checklist, validation, error_handling) is a real issue
- Comprehensive examples expected
- Thorough validation required
- **Operational effectiveness is CRITICAL**: Must have verifiable success criteria, verification gates, and failure modes
- Flag heavily procedural skills that lack operational content as critical issue

**Delegation skills** (invoke subagents):

- Success criteria can focus on invocation success
- Pre-validation may be redundant if subagent validates
- Operational effectiveness: subagent skill must have it; delegation skill can be lighter

**Migration/transformation skills** (change state, move files, update systems):

- **Highest operational bar**: These skills change things that are hard to undo
- MUST have verification gates before destructive operations
- MUST have failure modes from actual usage
- MUST have concrete examples showing before/after with real values
- Reject missing operational content

Always explain WHY something matters for this specific skill, not just that it violates a rule.
</contextual_judgment>

<legacy_skills_guidance>
Some skills were created before pure XML structure became the standard. When auditing legacy skills:

- Flag every markdown heading in SKILL.md as a pure-XML violation with its file and line, the governing rule, the observed heading, and the consequence.
- Apply the current standard without leniency for the skill's age.
- State the required correction at the rule level; do not write replacement XML, migration examples, sequencing advice, or a remediation plan.

</legacy_skills_guidance>

<reference_file_guidance>
Reference files in the `references/` directory should also use pure XML structure (no markdown headings in body). However, be proportionate with reference files:

- Do not reject a reference file solely for markdown headings when its governing structure permits them; emit no non-rejecting style observation
- Still recommend migration to pure XML
- Reference files should still be readable and well-structured
- Table of contents in reference files over 100 lines is acceptable

**Priority**: Fix SKILL.md first, then reference files.
</reference_file_guidance>

<xml_structure_examples>
Read `${CLAUDE_SKILL_DIR}/references/xml-structure-examples.md` for annotated examples of each violation type.
</xml_structure_examples>

<operational_effectiveness_examples>
Read `${CLAUDE_SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated examples of each issue type.
</operational_effectiveness_examples>

<verdict_format>
Emit one terminal verdict as the first line.

- Emit `APPROVED` when no rejecting finding exists.
- Emit `REJECTED` when one or more rejecting findings exist or the audit cannot complete.
- After `REJECTED`, list every rejecting finding as `file:line — violated rule: evidence. Required correction: action.`
- Emit no JSON envelope, numeric score, mutation offer, or prose before the terminal verdict.
  </verdict_format>

<failure_modes>

**Failure 1: Approved a skill whose objective was still activity-shaped.** Claude read an `<objective>` that opened with a verb ("Audit…", "Generate…") or an actor ("The skill…") and passed it, because the activity reading felt natural. The objective states an output; an activity- or actor-shaped one is a rejecting finding the `actor_or_activity_objective` flag exists to catch. Read every objective against `/agent-prompt-standards` `<objective_shape>`, not by feel.

**Failure 2: Skipped an evaluation area and missed a whole class.** Claude judged YAML and structure, formed a verdict, and stopped — leaving prompt craft or anti-patterns unexamined, so a class of violations passed unseen. The verdict is sound only when every evaluation area was judged; a skipped area yields an unsound verdict, not a shorter one. Cover all seven areas before issuing the verdict.

**Failure 3: Scored the skill instead of judging it.** Claude assigned a number ("8/10 structure") instead of issuing a terminal verdict with concrete rejecting findings, turning a verdict into a rating the author cannot act on. Each rejecting finding names a location, a standard, evidence, and a required correction; a score names none of them. Emit the verdict and rejecting findings, never scores.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every evaluation area was judged with none skipped — YAML frontmatter, structure and progressive disclosure, content quality, operational effectiveness, command capabilities, prompt craft, and anti-patterns (coverage-complete).
- The verdict states `APPROVED` or `REJECTED`; only a rejected verdict carries findings.
- Each rejecting finding is falsifiable: it names the location (file:line), the standard at issue, the evidence, and the required correction.
- The same SKILL.md yields the same verdict.

</success_criteria>

<validation>
Before presenting audit findings, verify:

**Completeness checks**:

- [ ] All evaluation areas assessed (including operational effectiveness)
- [ ] Findings have file:line locations
- [ ] The first output line is exactly `APPROVED` or `REJECTED`
- [ ] An approved verdict emits no findings; a rejected verdict emits every rejecting finding

**Accuracy checks**:

- [ ] All line numbers verified against actual file
- [ ] Rejection thresholds reflect the target skill's complexity and governing standards
- [ ] Context appropriately considered (simple vs complex skill)
- [ ] Operational effectiveness evaluated proportionally (critical for complex/migration skills)

**Quality checks**:

- [ ] Findings are specific and actionable
- [ ] Every rejecting finding names the violated rule, evidence, required correction, and concrete failure it prevents
- [ ] No non-rejecting observations, strengths, recommendations, or mutation offers appear
- [ ] No arbitrary rules applied without contextual justification

**Operational effectiveness checks** (for complex skills):

- [ ] Evaluated whether success criteria are verifiable (commands, thresholds)
- [ ] Checked for verification gates in multi-step workflows
- [ ] Looked for failure modes documentation
- [ ] Assessed procedural vs operational balance
- [ ] Flagged abstract examples that should be concrete

Only present findings after all checks pass.
</validation>
