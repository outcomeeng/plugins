---
name: audit-skills
description: >-
  SKILL.md audit methodology preloaded by the skill-auditor agent. Dispatch
  skill-auditor to audit SKILL.md files; the main conversation reaches this audit
  only through that agent.
argument-hint: <skill-path>
allowed-tools: Read, Grep, Glob, Bash, Skill
---

Invoke the `develop:skill-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `develop:agent-prompt-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<dispatch_gate>

This audit runs in the skill-auditor agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch the skill-auditor agent instead of running this audit here. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>
A verdict on a SKILL.md against `/skill-standards` and `/agent-prompt-standards`: findings grouped as keep-these-aspects / worth-improving / must-fix, each naming the location, the standard at issue, and the consequence — contextual judgment, never a score. The verdict spans YAML frontmatter, structure and progressive disclosure, content quality, operational effectiveness, command capabilities, prompt craft, and anti-patterns.
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

- YAML compliance (name length, description quality, directive style with negative constraint, `argument-hint` when arguments are used)
- Command capabilities (argument usage and integration, `!`-dynamic-context safety, `allowed-tools` tool-restriction security, `@` file references)
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
- **Procedural/operational balance** (skill states both how to DO the work and how to KNOW it was done right)

</focus_areas>

<audit_workflow>
**MANDATORY**: Read standards FIRST, before auditing:

1. Read `/skill-standards` — the canonical standards for skill structure, frontmatter, XML tags, progressive disclosure, skill types, reference patterns, code-fence rules, bash restrictions, validation, and script testing. Then check for `spx/local/skills.md` at the repository root and read it if it exists.
2. Read `/agent-prompt-standards` — voice, description style, constraint language, and prose anti-patterns. Already injected above.
3. Read the target skill files (SKILL.md and any `references/`, `workflows/`, `templates/`, `scripts/` subdirectories).
4. Read `${CLAUDE_SKILL_DIR}/references/xml-structure-examples.md` and `${CLAUDE_SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated violation examples. When the target carries command-capability fields — `argument-hint`/`arguments`, `allowed-tools`, `!`-dynamic context, or `@` file references — also read `/skill-standards`'s `references/command-capabilities.md` for the rules that govern that surface. When the target is an `audit-*` skill, also read `/skill-standards`'s `references/auditor-skeleton.md` — the `/skill-standards` table loaded in step 1 directs you to it; read the file itself explicitly — the canonical auditor structure the `auditor_skeleton_violation` check verifies against.
5. Handle edge cases:
   - If `/skill-standards` or `/agent-prompt-standards` is unreadable, note under "Configuration Issues" and proceed with available content.
   - If YAML frontmatter is malformed, flag as critical issue.
   - If the skill references external files that don't exist, flag as critical issue and recommend fixing broken references.
   - If the skill is under 100 lines, note as "simple skill" in the context line and evaluate accordingly.
6. Evaluate the target skill against the standards loaded in steps 1-2.

**Use ACTUAL patterns from `/skill-standards`, not memory.** Never read `create-skills/references/` for standards — that directory is workflow content only.
</audit_workflow>

<evaluation_areas>
<area name="yaml_frontmatter">
Check for:

- **name**: Lowercase-with-hyphens, max 64 chars, matches directory name, follows verb-noun convention (create-*, manage-*, setup-*, generate-*)
- **description**: Max 1024 chars, directive style (ALWAYS invoke + NEVER without), no XML tags
- **argument-hint**: Present when the skill takes arguments (the body substitutes a declared `$name`); omit for self-contained skills

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

- Every argument declared in `arguments` is substituted as `$name` in the body, and every `$name` the body substitutes is declared — neither orphaned
- `argument-hint` is present when the skill takes arguments
- A bare command-style `$ARGUMENTS` / `$1` copied into a skill body is a defect — skills name arguments through the `arguments` field
- Empty-argument handling is stated when the skill requires an argument or defines a no-argument fallback

**Dynamic-context safety** (`!`-backtick blocks inside `<context>`):

- Loaded state is directly relevant to the skill's task — not injected context the skill never reads
- Each command is filtered to bounded output and never grows monotonically (the block fires on every skill load)

**Tool-restriction security** (`allowed-tools`):

- Bash is restricted to the narrowest verb pattern that works (`Bash(git add:*)`, not bare `Bash` or `Bash(git *)`) when specific verbs suffice
- Destructive and network tools (`Write`, `Bash`, `WebFetch`) are absent unless the task genuinely needs them — a read-only or analysis skill cannot delete, force-push, deploy, or exfiltrate
- An `audit-*` skill carries `Read, Grep, Glob, Bash` (plus `Skill` when composing) and never `Write`/`Edit`

</area>

<area name="prompt_craft">
Check against `/agent-prompt-standards` conventions:

- **Voice**: Uses imperative mood for instructions, "Claude" for failure modes/tendencies. Never "the agent", "the model", or "you"
- **Description style**: Directive pattern (ALWAYS + optional NEVER). Language-after-artifact ordering. Matches user speech
- **Constraint language**: Strong modal verbs (MUST/NEVER/ALWAYS) in constraint blocks. No weak modals ("should", "try to", "consider") in constraints
- **Anti-patterns**: No banned phrases ("helpful assistant", "helps with", "processes data", "please", "if possible"). No structural anti-patterns (explaining Claude to Claude, motivational prose, empty disclaimers)
- **Conciseness**: Only information Claude doesn't already have. Concrete over abstract
- **Failure modes**: Written from actual experience, use "Claude" as subject, structured as what/why/how-to-avoid
- **Objective shape**: `<objective>` states the observable output in a definite shape — not an actor ("The skill", "Claude") or a bare activity verb ("Audit", "Evaluate", "Generate"), and not a behavioral claim. `<success_criteria>` proves the output (its sound-making properties), never a re-list of the workflow steps; the two do not duplicate (per `/agent-prompt-standards` `<objective_shape>`). For an `audit-*` skill, check the canonical structure in `/skill-standards` `references/auditor-skeleton.md`

</area>

<area name="anti_patterns">
Flag these issues:
- **markdown_headings_in_body**: Using markdown headings (##, ###) in skill body instead of pure XML
- **missing_required_tags**: Missing objective or success_criteria
- **actor_or_activity_objective**: `<objective>` opens with an actor ("The skill…", "Claude…") or a bare activity verb ("Audit…", "Evaluate…", "Generate…") instead of naming the observable output it produces
- **objective_criteria_duplication**: `<objective>` and `<success_criteria>` restate the same content — the objective names the output, success_criteria proves it
- **auditor_skeleton_violation**: an `audit-*` skill deviating from `/skill-standards` `references/auditor-skeleton.md` — `<output_format>` instead of `<verdict_format>`, a non-`<audit_workflow>` procedure name, a `<quick_start>` block, or an activity-shaped objective. The prose auditors (`audit-prose`, `audit-internal-docs`) are exempt from the procedure-name and `<dispatch_gate>` checks per the skeleton's `<prose_variant>`
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
- **heavy_context_block**: `<context>` bash commands that produce verbose or growing output (session lists, full file contents, cache enumerations) without filtering. The `<context>` block fires on every skill load — including false-positive activations from directive descriptions — so heavy commands compound. Flag as recommendation: filter the command (e.g., `--status doing,todo`, `head -N`) or move it to the workflow file that consumes the data.
- **orphaned_argument**: an argument declared in `arguments` that the body never substitutes, or a `$name` substituted in the body that `arguments` never declares. Flag as critical — the skill takes input it ignores, or substitutes an undefined name.
- **missing_argument_hint**: the skill takes arguments but omits `argument-hint`, so `/` autocomplete gives the user no signal about expected input. Flag as recommendation.
- **command_style_arguments**: a bare `$ARGUMENTS` or `$1`/`$2` copied from a slash command into a skill body instead of a named `$name` declared in `arguments`. Flag as critical.
- **overbroad_allowed_tools**: `allowed-tools` grants bare `Bash`, `Bash(git *)`, or a destructive/network tool the skill's task does not need, re-admitting the destructive or exfiltrating commands a narrower grant would bar. Flag as critical for security-sensitive skills.
- **irrelevant_dynamic_context**: a `<context>` `!` block injecting state the skill never reads. Flag as recommendation — it taxes every load without payoff.

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
Workflow heading → <workflow>
Success criteria heading → <success_criteria>
Quick start heading → <quick_start> (only if skill is an on-demand tool)
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

<verdict_format>
Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff the `must-fix` row has no findings; `FAIL` if any must-fix finding has severity `REJECT`. Worth-improving and Keep-these-aspects observations land as `WARNING` and `INFO` severity findings respectively under the corresponding rows — they do not flip the overall to `FAIL`.

```json
{
  "schema_version": 1,
  "skill": "audit-skills",
  "target": "<skill-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    {
      "name": "keep-these-aspects",
      "status": "PASS",
      "findings": [
        {
          "id": "f-001",
          "file": "<skill-file>",
          "line": null,
          "rule": "<strength-name>",
          "severity": "INFO",
          "message": "<what it does> — removing this would <specific consequence>"
        }
      ]
    },
    {
      "name": "worth-improving",
      "status": "PASS",
      "findings": [
        {
          "id": "f-002",
          "file": "<skill-file>",
          "line": null,
          "rule": "<issue-name>",
          "severity": "WARNING",
          "message": "Current: <what exists>. Change to: <what it should be>. Benefit: <specific gain>."
        }
      ]
    },
    {
      "name": "must-fix",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": [
        {
          "id": "f-003",
          "file": "<skill-file>",
          "line": null,
          "rule": "<issue-name>",
          "severity": "REJECT",
          "message": "Current: <what exists>. Fix: <specific action>. Impact if unfixed: <what breaks>."
        }
      ]
    }
  ],
  "metadata": { "skill_type": "simple | complex | delegation | etc.", "line_count": "<n>" }
}
```

Note: While this skill uses pure XML structure, it produces JSON output that the verdict toolchain renders as markdown for human readability.
</verdict_format>

<failure_modes>

**Failure 1: Approved a skill whose objective was still activity-shaped.** Claude read an `<objective>` that opened with a verb ("Audit…", "Generate…") or an actor ("The skill…") and passed it, because the activity reading felt natural. The objective states an output; an activity- or actor-shaped one is a must-fix the `actor_or_activity_objective` flag exists to catch. Read every objective against `/agent-prompt-standards` `<objective_shape>`, not by feel.

**Failure 2: Skipped an evaluation area and missed a whole class.** Claude judged YAML and structure, formed a verdict, and stopped — leaving prompt craft or anti-patterns unexamined, so a class of violations passed unseen. The verdict is sound only when every evaluation area was judged; a skipped area yields an unsound verdict, not a shorter one. Cover all seven areas before issuing the verdict.

**Failure 3: Scored the skill instead of judging it.** Claude assigned a number ("8/10 structure") instead of grouping findings as keep / worth-improving / must-fix, turning a verdict into a rating the author cannot act on. Each finding names a location, a standard, and a consequence; a score names none of them. Emit findings, never scores.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every evaluation area was judged with none skipped — YAML frontmatter, structure and progressive disclosure, content quality, operational effectiveness, command capabilities, prompt craft, and anti-patterns (coverage-complete).
- The verdict states an overall PASS/FAIL with findings grouped keep-these-aspects / worth-improving / must-fix.
- Each finding is falsifiable: it names the location (file:line), the standard at issue, and the consequence — every keep names what degrades if removed, every must-fix names the failure it prevents.
- The same SKILL.md yields the same verdict.

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
