---
name: auditing-skills
description: >-
  ALWAYS invoke this skill when auditing, reviewing, or evaluating SKILL.md files.
  NEVER audit skills without this skill.
argument-hint: <skill-path>
---

<objective>
Evaluate SKILL.md files against best practices for structure, conciseness, progressive disclosure, and effectiveness. Provide actionable findings with contextual judgment, not arbitrary scores.
</objective>

<constraints>
- NEVER modify files during audit - ONLY analyze and report findings
- MUST read all reference documentation before evaluating
- ALWAYS provide file:line locations for every finding
- DO NOT generate fixes unless explicitly requested by the user
- NEVER make assumptions about skill intent - flag ambiguities as findings
- MUST complete all evaluation areas (YAML, Structure, Content, Anti-patterns)
- ALWAYS apply contextual judgment - what matters for a simple skill differs from a complex one

</constraints>

<focus_areas>
During audits, prioritize evaluation of:

- YAML compliance (name length, description quality, directive style with negative constraint)
- Pure XML structure (required tags, no markdown headings in body, proper nesting)
- Progressive disclosure structure (SKILL.md < 500 lines, references one level deep)
- Conciseness and signal-to-noise ratio (every word earns its place)
- Required XML tags (objective, success_criteria)
- Conditional XML tags (appropriate for complexity level)
- XML structure quality (proper closing tags, semantic naming, no hybrid markdown/XML)
- Constraint strength (MUST/NEVER/ALWAYS vs weak modals)
- Error handling coverage (missing files, malformed input, edge cases)
- Example quality (concrete, realistic, demonstrates key patterns)
- **Operational effectiveness** (verifiable success criteria, verification gates, failure modes)
- **Procedural/operational balance** (skill tells you how to DO and how to KNOW you did it right)

</focus_areas>

<critical_workflow>
**MANDATORY**: Read best practices FIRST, before auditing:

1. Locate the creating-skills skill and its references:
   - Use Glob: `.claude/plugins/cache/**/creating-skills/SKILL.md`
   - Then read its SKILL.md for overview
2. Read creating-skills/references/use-xml-tags.md for required/conditional tags, XML structure requirements
3. Read creating-skills/references/skill-patterns.md for YAML, naming, progressive disclosure patterns
4. Read creating-skills/references/core-principles.md for XML structure, conciseness, context window principles
5. Locate and read the standardizing-agent-prompts skill:
   - Use Glob: `.claude/plugins/cache/**/standardizing-agent-prompts/SKILL.md`
   - Covers voice, description style, constraint language, and anti-patterns
6. Handle edge cases:
   - If reference files are missing or unreadable, note in findings under "Configuration Issues" and proceed with available content
   - If YAML frontmatter is malformed, flag as critical issue
   - If skill references external files that don't exist, flag as critical issue and recommend fixing broken references
   - If skill is <100 lines, note as "simple skill" in context and evaluate accordingly
7. Read the skill files (SKILL.md and any references/, docs/, scripts/ subdirectories)
8. Evaluate against best practices from steps 1-5

**Use ACTUAL patterns from references, not memory.**
</critical_workflow>

<evaluation_areas>
<area name="yaml_frontmatter">
Check for:

- **name**: Lowercase-with-hyphens, max 64 chars, matches directory name, follows verb-noun convention (create-*, manage-*, setup-*, generate-*)
- **description**: Max 1024 chars, directive style (ALWAYS invoke + NEVER without), no XML tags

</area>

<area name="structure_and_organization">
Check for:
- **Progressive disclosure**: SKILL.md is overview (<500 lines), detailed content in reference files, references one level deep
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
- Can you answer "did I succeed?" with a boolean, not a judgment call?
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
- Can you compare your output to the example to verify correctness?
- ❌ Bad: "Coverage should match between legacy and SPX tests"
- ✅ Good: "Legacy: 24 tests, 86.3% on state.ts. SPX: 24 tests, 86.3% on state.ts. ✓ Match"

**Procedural vs Operational Balance**:

- Procedural = HOW to do steps
- Operational = how to KNOW you did it right
- Skills need both; flag if heavily imbalanced toward procedural

</area>

<area name="prompt_craft">
Check against `/standardizing-agent-prompts` conventions:

- **Voice**: Uses imperative mood for instructions, "Claude" for failure modes/tendencies. Never "the agent", "the model", or "you"
- **Description style**: Directive pattern (ALWAYS + optional NEVER). Language-after-artifact ordering. Matches user speech
- **Constraint language**: Strong modal verbs (MUST/NEVER/ALWAYS) in constraint blocks. No weak modals ("should", "try to", "consider") in constraints
- **Anti-patterns**: No banned phrases ("helpful assistant", "helps with", "processes data", "please", "if possible"). No structural anti-patterns (explaining Claude to Claude, motivational prose, empty disclaimers)
- **Conciseness**: Only information Claude doesn't already have. Concrete over abstract
- **Failure modes**: Written from actual experience, use "Claude" as subject, structured as what/why/how-to-avoid

</area>

<area name="anti_patterns">
Flag these issues:
- **markdown_headings_in_body**: Using markdown headings (##, ###) in skill body instead of pure XML
- **missing_required_tags**: Missing objective or success_criteria
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
- Flag missing operational content as critical, not recommendation

Always explain WHY something matters for this specific skill, not just that it violates a rule.
</contextual_judgment>

<legacy_skills_guidance>
Some skills were created before pure XML structure became the standard. When auditing legacy skills:

- Flag markdown headings as critical issues for SKILL.md
- Include migration guidance in findings: "This skill predates the pure XML standard. Migrate by converting markdown headings to semantic XML tags."
- Provide specific migration examples in the findings
- Don't be more lenient just because it's legacy - the standard applies to all skills
- Suggest incremental migration if the skill is large: SKILL.md first, then references

**Migration pattern**:

```
## Workflow → <workflow>
## Success criteria → <success_criteria>
## Quick start → <quick_start> (only if skill is an on-demand tool)
```

</legacy_skills_guidance>

<reference_file_guidance>
Reference files in the `references/` directory should also use pure XML structure (no markdown headings in body). However, be proportionate with reference files:

- If reference files use markdown headings, flag as recommendation (not critical) since they're secondary to SKILL.md
- Still recommend migration to pure XML
- Reference files should still be readable and well-structured
- Table of contents in reference files over 100 lines is acceptable

**Priority**: Fix SKILL.md first, then reference files.
</reference_file_guidance>

<xml_structure_examples>
**What to flag as XML structure violations:**

<example name="markdown_headings_in_body">
❌ Flag as critical:
```markdown
## Quick start

Extract text with pdfplumber...

## Advanced features

Form filling...

````
✅ Should be:
```xml
<quick_start>
Extract text with pdfplumber...
</quick_start>

<advanced_features>
Form filling...
</advanced_features>
````

**Why**: Markdown headings in body is a critical anti-pattern. Pure XML structure required.
</example>

<example name="missing_required_tags">
❌ Flag as critical:
```xml
<workflow>
1. Do step one
2. Do step two
</workflow>
```

Missing: `<objective>`, `<success_criteria>`

✅ Should have both required tags:

```xml
<objective>What the skill does and why it matters</objective>

<success_criteria>How to know it worked</success_criteria>
```

**Why**: Required tags are non-negotiable for all skills. `<quick_start>` is conditional — include for on-demand tool skills, omit for foundation/gate/validator/reference skills.
</example>

<example name="hybrid_xml_markdown">
❌ Flag as critical:
```markdown
<objective>
PDF processing capabilities
</objective>

## Quick start

Extract text...

## Advanced features

Form filling...

````
✅ Should be pure XML:
```xml
<objective>
PDF processing capabilities
</objective>

<quick_start>
Extract text...
</quick_start>

<advanced_features>
Form filling...
</advanced_features>
````

**Why**: Mixing XML with markdown headings creates inconsistent structure.
</example>

<example name="unclosed_xml_tags">
❌ Flag as critical:
```xml
<objective>
Process PDF files

<quick_start>
Use pdfplumber...
</quick_start>

````
Missing closing tag: `</objective>`

✅ Should properly close all tags:
```xml
<objective>
Process PDF files
</objective>

<quick_start>
Use pdfplumber...
</quick_start>
````

**Why**: Unclosed tags break parsing and create ambiguous boundaries.
</example>

<example name="inappropriate_conditional_tags">
Flag when conditional tags don't match complexity:

**Over-engineered simple skill** (flag as recommendation):

```xml
<objective>Convert CSV to JSON</objective>
<quick_start>Use pandas.to_json()</quick_start>
<context>CSV files are common...</context>
<workflow>Step 1... Step 2...</workflow>
<advanced_features>See [advanced.md]</advanced_features>
<security_checklist>Validate input...</security_checklist>
<testing>Test with all models...</testing>
```

**Why**: Simple single-domain skill only needs required tags. Too many conditional tags add unnecessary complexity.

**Under-specified complex skill** (flag as critical):

```xml
<objective>Manage payment processing with Stripe API</objective>
<quick_start>Create checkout session</quick_start>
<success_criteria>Payment completed</success_criteria>
```

**Why**: Payment processing needs security_checklist, validation, error handling patterns. Missing critical conditional tags.
</example>
</xml_structure_examples>

<operational_effectiveness_examples>
Examples of operational effectiveness issues to flag:

<example name="unverifiable_success_criteria">
❌ Flag as critical for complex skills:
```xml
<success_criteria>
Task is complete when:
- All stories have SPX tests
- Coverage verified
- Legacy tests removed
</success_criteria>
```

**Why it fails**: "Coverage verified" is not testable. Verified how? What threshold? What command?

✅ Should be:

````xml
<success_criteria>
Task is complete when:
- All stories have SPX tests (verify: `ls spx/.../tests/*.test.ts` returns files for each story)
- Coverage parity confirmed (verify: both commands below show same % for target files)
  ```bash
  pnpm vitest run tests/legacy/... --coverage | grep "target.ts"
  pnpm vitest run spx/.../tests --coverage | grep "target.ts"
````

- Legacy tests removed via git rm (verify: `git status` shows deletions staged)

**Threshold**: Coverage delta must be ≤0.5%. If larger, STOP and identify missing tests.
</success_criteria>

````
**Why it works**: Every criterion has a verification command and a pass/fail threshold.
</example>

<example name="missing_verification_gates">
❌ Flag as critical for multi-step skills:
```xml
<workflow>
1. Read DONE.md files from worktree
2. Create SPX tests matching DONE.md entries
3. Verify coverage matches
4. Remove legacy tests with git rm
5. Create SPX-MIGRATION.md
</workflow>
````

**Why it fails**: No stop points. Agent could remove legacy tests before verifying coverage.

✅ Should be:

```xml
<workflow>1. Read DONE.md files from worktree
2. Create SPX tests matching DONE.md entries

**GATE 1**: Before proceeding, verify:
- [ ] SPX test count matches DONE.md entry count
- [ ] All SPX tests pass: `pnpm vitest run spx/.../tests`
If gate fails, fix tests before continuing.

3. Verify coverage matches (run both, compare percentages)
4. Remove legacy tests with git rm

**GATE 2**: Before committing, verify:
- [ ] `pnpm test` passes
- [ ] `git status` shows only expected changes
If gate fails, do not commit.

5. Create SPX-MIGRATION.md</workflow>
```

**Why it works**: Explicit gates prevent proceeding with broken state.
</example>

<example name="missing_failure_modes">
❌ Flag as recommendation for complex skills:
Skill has detailed workflow but no `<failure_modes>` section.

**Why it matters**: Agents will make the same mistakes that previous agents made. Failure modes capture hard-won operational knowledge.

✅ Should include:

```xml
<failure_modes>Failures from actual usage:

**Failure 1: Compared coverage at wrong granularity**
- What happened: Agent saw 39% coverage for one story and stopped, thinking migration failed
- Why it failed: Multiple stories share one legacy file; per-story coverage is meaningless
- How to avoid: ALWAYS compare at legacy file level, not story level

**Failure 2: Removed shared legacy file too early**
- What happened: Agent removed tests/integration/cli.test.ts after migrating story-32
- Why it failed: Stories 43 and 54 also contributed tests to that file
- How to avoid: Build legacy_file → [stories] map BEFORE migration. Only remove after ALL contributing stories migrated.</failure_modes>
```

**Why it works**: Future agents learn from past mistakes without repeating them.
</example>

<example name="abstract_vs_concrete_examples">
❌ Flag as recommendation:
```xml
<success_criteria>
Coverage should match between legacy and SPX tests.
</success_criteria>
```

**Why it fails**: What does "match" mean? What numbers? How do I compare my output?

✅ Should be:

```xml
<success_criteria>Coverage must match. Concrete example from actual migration:

Legacy tests:
  tests/unit/status/state.test.ts (5 tests)
  tests/integration/status/state.integration.test.ts (19 tests)
  Total: 24 tests, 86.3% coverage on src/status/state.ts

SPX tests:
  spx/.../21-initial.story/tests/state.unit.test.ts (5 tests)
  spx/.../32-transitions.story/tests/state.integration.test.ts (7 tests)
  spx/.../43-concurrent.story/tests/state.integration.test.ts (4 tests)
  spx/.../54-edge-cases.story/tests/state.integration.test.ts (8 tests)
  Total: 24 tests, 86.3% coverage on src/status/state.ts

Verdict: ✓ Test counts match (24=24), coverage matches (86.3%=86.3%)</success_criteria>
```

**Why it works**: Agent can compare their actual output to the example and know if they succeeded.
</example>

<example name="procedural_without_operational">
❌ Flag as critical for complex skills:
Skill has detailed `<workflow>` (450 lines of steps) but:
- `<success_criteria>` is 3 lines of vague statements
- No `<verification_gates>`
- No `<failure_modes>`

**Pattern**: Heavy procedural, light operational = agents know HOW but not WHETHER they succeeded.

**Why it matters**: This is the most common skill failure mode. The skill tells you what to do but not how to verify you did it right. Agents follow steps, produce wrong output, and don't realize it.

✅ Balanced skill has roughly equal investment in:

- Procedural content (workflow, steps, commands)
- Operational content (success criteria, verification gates, failure modes, concrete examples)

</example>
</operational_effectiveness_examples>

<output_format>
Audit reports use severity-based findings, not scores. Generate output using this markdown template:

```markdown
## Audit Results: [skill-name]

### Assessment

[1-2 sentence overall assessment: Is this skill fit for purpose? What's the main takeaway?]

### Critical Issues

Issues that hurt effectiveness or violate required patterns:

1. **[Issue category]** (file:line)
   - Current: [What exists now]
   - Should be: [What it should be]
   - Why it matters: [Specific impact on this skill's effectiveness]
   - Fix: [Specific action to take]

2. ...

(If none: "No critical issues found.")

### Recommendations

Improvements that would make this skill better:

1. **[Issue category]** (file:line)
   - Current: [What exists now]
   - Recommendation: [What to change]
   - Benefit: [How this improves the skill]

2. ...

(If none: "No recommendations - skill follows best practices well.")

### Strengths

What's working well (keep these):

- [Specific strength with location]
- ...

### Quick Fixes

Minor issues easily resolved:

1. [Issue] at file:line → [One-line fix]
2. ...

### Context

- Skill type: [simple/complex/delegation/etc.]
- Line count: [number]
- Estimated effort to address issues: [low/medium/high]
```

Note: While this subagent uses pure XML structure, it generates markdown output for human readability.
</output_format>

<success_criteria>
Task is complete when:

- All reference documentation files have been read and incorporated
- All evaluation areas assessed (YAML, Structure, Content, Anti-patterns, **Operational Effectiveness**)
- Contextual judgment applied based on skill type and complexity
- Findings categorized by severity (Critical, Recommendations, Quick Fixes)
- At least 3 specific findings provided with file:line locations (or explicit note that skill is well-formed)
- Assessment provides clear, actionable guidance
- Strengths documented (what's working well)
- Context section includes skill type and effort estimate
- Next-step options presented to reduce user cognitive load
- **For complex/migration skills**: Explicitly evaluated verifiable success criteria, verification gates, and failure modes

</success_criteria>

<validation>
Before presenting audit findings, verify:

**Completeness checks**:

- [ ] All evaluation areas assessed (including operational effectiveness)
- [ ] Findings have file:line locations
- [ ] Assessment section provides clear summary
- [ ] Strengths identified

**Accuracy checks**:

- [ ] All line numbers verified against actual file
- [ ] Recommendations match skill complexity level
- [ ] Context appropriately considered (simple vs complex skill)
- [ ] Operational effectiveness evaluated proportionally (critical for complex/migration skills)

**Quality checks**:

- [ ] Findings are specific and actionable
- [ ] "Why it matters" explains impact for THIS skill
- [ ] Remediation steps are clear
- [ ] No arbitrary rules applied without contextual justification

**Operational effectiveness checks** (for complex skills):

- [ ] Evaluated whether success criteria are verifiable (commands, thresholds)
- [ ] Checked for verification gates in multi-step workflows
- [ ] Looked for failure modes documentation
- [ ] Assessed procedural vs operational balance
- [ ] Flagged abstract examples that should be concrete

Only present findings after all checks pass.
</validation>

<final_step>
Before offering next steps, reason about the findings:

1. **Identify sequencing conflicts** — do any fixes interfere with or subsume others? (e.g., extracting to a workflow file makes heading conversion happen inside the new file — fixing headings in-place first means redoing them during extraction)
2. **Find the forcing decision** — which choice, once made, determines the shape of everything else?
3. **Group remaining fixes** — which can be committed immediately vs which depend on the forcing decision?

Present the forcing decision as a structured choice. Each option MUST name a real trade-off — what this approach does AND what it defers or makes easier. Never offer options where one sounds obviously correct.

**Good option**: "Restructure first — extract workflow → headings disappear naturally in the new file. One pass, no rework. Higher upfront effort."

**Bad option**: "Fix everything" — no trade-off stated, sounds obviously correct, requires no judgment.

If one option sounds obviously better than the others, the option set is wrong — redesign it.

</final_step>
