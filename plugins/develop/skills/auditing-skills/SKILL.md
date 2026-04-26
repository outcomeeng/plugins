---
name: auditing-skills
description: >-
  ALWAYS invoke this skill when auditing, reviewing, or evaluating SKILL.md files.
  NEVER audit skills without this skill.
argument-hint: <skill-path>
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-skills/SKILL.md" || echo "standardizing-skills not found — invoke skill develop:standardizing-skills now"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-agent-prompts/SKILL.md" || echo "standardizing-agent-prompts not found — invoke skill develop:standardizing-agent-prompts now"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. Skill `develop:standardizing-skills`
2. Skill `develop:standardizing-agent-prompts`

</codex_fallback>

<objective>
Evaluate SKILL.md files against best practices for structure, conciseness, progressive disclosure, and effectiveness. Provide actionable findings with contextual judgment, not arbitrary scores.
</objective>

<constraints>
- NEVER modify files during audit - ONLY analyze and report findings
- MUST read all reference documentation before evaluating
- ALWAYS provide file:line locations for every finding
- NEVER generate fixes unless explicitly requested by the user
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
**MANDATORY**: Read standards FIRST, before auditing:

1. Read `/standardizing-skills` — the canonical standards for skill structure, frontmatter, XML tags, progressive disclosure, skill types, reference patterns, code-fence rules, bash restrictions, validation, and script testing. Then check for `spx/local/standardizing-skills.md` at the repository root and read it if it exists.
2. Read `/standardizing-agent-prompts` — voice, description style, constraint language, and prose anti-patterns. Already injected above.
3. Read the target skill files (SKILL.md and any `references/`, `workflows/`, `templates/`, `scripts/` subdirectories).
4. Read `${CLAUDE_SKILL_DIR}/references/xml-structure-examples.md` and `${CLAUDE_SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated violation examples.
5. Handle edge cases:
   - If `/standardizing-skills` or `/standardizing-agent-prompts` is unreadable, note under "Configuration Issues" and proceed with available content.
   - If YAML frontmatter is malformed, flag as critical issue.
   - If the skill references external files that don't exist, flag as critical issue and recommend fixing broken references.
   - If the skill is under 100 lines, note as "simple skill" in the context line and evaluate accordingly.
6. Evaluate the target skill against the standards loaded in steps 1-2.

**Use ACTUAL patterns from `/standardizing-skills`, not memory.** Never read `creating-skills/references/` for standards — that directory is workflow content only.
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
Read `${CLAUDE_SKILL_DIR}/references/xml-structure-examples.md` for annotated examples of each violation type.
</xml_structure_examples>

<operational_effectiveness_examples>
Read `${CLAUDE_SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated examples of each issue type.
</operational_effectiveness_examples>

<output_format>
Audit reports use severity-based findings, not scores. Generate output using this markdown template:

```markdown
## Audit: [skill-name]

**Verdict**: [1-2 sentences. Is this skill fit for purpose? State the main finding concretely — e.g., "Structurally sound but 30% over size limit with no failure modes." Not "This skill has some issues."]

**Context**: Skill type: [simple/complex/delegation/etc.] · Line count: [number] · Effort to address: [low/medium/high]

---

### Keep these aspects

What's working well and why removing it would hurt — each entry names the concrete consequence of losing it:

- **[Strength]** (`file:line`) — [what it does] → removing this would [specific consequence: e.g., "cause Claude to flag missing <quick_start> in validator skills where omission is correct"]
- ...

(If none: "No clear strengths — skill needs significant work.")

---

### Worth improving

Changes that yield concrete, named gains:

1. **[Issue]** (`file:line`)
   - Current: [what exists]
   - Change to: [what it should be]
   - Benefit: [specific gain — name the exact failure mode it prevents or the exact workflow step it improves. Not "improves clarity."]

(If none: "No improvements needed beyond must-fix items.")

---

### Must fix

Issues that break effectiveness or violate required patterns — each entry names what specifically fails if left unfixed:

1. **[Issue]** (`file:line`)
   - Current: [what exists]
   - Fix: [specific action]
   - Impact if unfixed: [what breaks — name the failure mode, not "reduces effectiveness"]

(If none: "No critical issues.")
```

Note: While this subagent uses pure XML structure, it generates markdown output for human readability.
</output_format>

<success_criteria>
Task is complete when:

- All reference documentation files have been read and incorporated
- All evaluation areas assessed (YAML, Structure, Content, Anti-patterns, **Operational Effectiveness**)
- Findings use Verdict / Keep these aspects / Worth improving / Must fix structure
- At least 3 specific findings provided with file:line locations (or explicit note that skill is well-formed)
- Every "Keep" entry names what would break or degrade if the strength were removed
- Every "Worth improving" entry names the specific failure mode prevented or workflow step improved
- Every "Must fix" entry names the specific failure that occurs if left unfixed
- Context section includes skill type, line count, and effort estimate
- Next-step options presented as a structured choice with genuine trade-offs
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
- [ ] Every "Keep" entry names the concrete consequence of removing the strength
- [ ] Every "Worth improving" entry names the specific gain, not a generic improvement
- [ ] Every "Must fix" entry names what specifically breaks if left unfixed
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

1. **Identify sequencing conflicts** — do any must-fix items interfere with or subsume others? (e.g., extracting to a workflow file makes heading conversion happen inside the new file — fixing headings in-place first means redoing them during extraction)
2. **Find the forcing decision** — which choice, once made, determines the shape of everything else?
3. **Group remaining fixes** — which can be committed immediately vs which depend on the forcing decision?

Present the forcing decision as a structured choice. Each option MUST name a real trade-off — what this approach does AND what it defers or makes easier. Never offer options where one sounds obviously correct.

**Good option**: "Restructure first — extract workflow → headings disappear naturally in the new file. One pass, no rework. Higher upfront effort."

**Bad option**: "Fix everything" — no trade-off stated, sounds obviously correct, requires no judgment.

If one option sounds obviously better than the others, the option set is wrong — redesign it.

</final_step>
