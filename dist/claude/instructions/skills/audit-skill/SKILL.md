---
name: audit-skill
description: >-
  SKILL.md audit methodology — judges skill content for standards compliance,
  operational effectiveness, portability, voice, and structure.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash(python3 -c:*), Skill
---

Invoke the `instructions:skill-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `instructions:agent-prompt-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
An `APPROVED` or `REJECTED` verdict on a SKILL.md against `/skill-standards` and `/agent-prompt-standards`, with findings grouped as keep-these-aspects, worth-improving, and must-fix; every rejected finding names the artifact location, violated rule, and evidence.
</objective>

<constraints>
- NEVER modify files during audit - ONLY analyze and report findings
- NEVER report a score; report contextual judgment across the full skill-authoring surface
- MUST read all reference documentation before evaluating
- ALWAYS provide file:line locations for every finding
- NEVER generate fixes unless explicitly requested by the user
- NEVER make assumptions about skill intent - flag ambiguities as findings
- MUST complete all evaluation areas
- ALWAYS apply contextual judgment - what matters for a simple skill differs from a complex one

</constraints>

<focus_areas>
During audits, prioritize evaluation of:

- YAML compliance (name length, description quality by skill role, `argument-hint` when arguments are used)
- Command capabilities (argument usage and integration, `!`-dynamic-context safety, `allowed-tools` tool-restriction security, `@` file references)
- Pure XML structure (required tags, no markdown headings in body, proper nesting)
- Progressive disclosure structure against `/skill-standards`, including deterministic eager-payload measurement when its exception applies
- Conciseness and signal-to-noise ratio (every word earns its place)
- Required XML tags (objective, success_criteria)
- Conditional XML tags (appropriate for complexity level)
- XML structure quality (proper closing tags, semantic naming, no hybrid markdown/XML)
- Constraint strength (MUST/NEVER/ALWAYS vs weak modals)
- Error handling coverage (missing files, malformed input, edge cases)
- Example quality (concrete, realistic, demonstrates key patterns)
- **Operational effectiveness** (verifiable success criteria, failure modes, and observable validation)
- **Procedural/operational balance** (skill states both how to DO the work and how to KNOW it was done right)

</focus_areas>

<audit_workflow>
**MANDATORY**: Read standards FIRST, before auditing:

1. Read `/skill-standards` — the canonical standards for skill structure, frontmatter, XML tags, progressive disclosure, skill types, reference patterns, code-fence rules, bash restrictions, validation, and script testing. Then check for `spx/local/skills.md` at the repository root and read it if it exists.
2. Read `/agent-prompt-standards` — voice, description style, constraint language, and prose anti-patterns. Already injected above.
3. Read the target skill files (SKILL.md and any `references/`, `workflows/`, `templates/`, `scripts/` subdirectories).
4. When the target uses `/skill-standards`'s eager-foundation exception, run the following deterministic counter against every rendered target `SKILL.md`. Record each command's integer output in verdict metadata, then apply the exception's current threshold and qualitative checks from `/skill-standards`; never estimate the count from model inspection.

   ```bash
   python3 -c 'from pathlib import Path; import sys; print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))' "<rendered-SKILL.md>"
   ```

5. Read `${CLAUDE_SKILL_DIR}/references/xml-structure-examples.md` and `${CLAUDE_SKILL_DIR}/references/operational-effectiveness-examples.md` for annotated violation examples. When the target carries command-capability fields — `argument-hint`/`arguments`, `allowed-tools`, `!`-dynamic context, or `@` file references — also read `/skill-standards`'s `references/command-capabilities.md` for the rules that govern that surface. When the target is an `audit-*` skill, also read `/skill-standards`'s `references/auditor-skeleton.md` — the `/skill-standards` table loaded in step 1 directs you to it; read the file itself explicitly — the canonical auditor structure the `auditor_skeleton_violation` check verifies against.
6. Handle edge cases:
   - If `/skill-standards` or `/agent-prompt-standards` is unreadable, add a `REJECT` finding with rule `configuration_issue` to the `must-fix` row and proceed with available content; the incomplete audit remains `REJECTED`.
   - If YAML frontmatter is malformed, flag as critical issue.
   - If the skill references external files that don't exist, flag as critical issue and recommend fixing broken references.
   - If the skill references a bundled plugin file through repository-local authored or generated plugin paths, legacy plugin-root paths, or an authored Codex-only skill-directory token, flag as a portable file-reference defect.
   - If the skill is under 100 lines, record `simple` in `metadata.skill_type` and evaluate accordingly.
7. Evaluate the target skill against the standards loaded in steps 1-2.

**Use ACTUAL patterns from `/skill-standards`, not memory.** Never treat a creator skill's workflow references as standards — those references carry authoring workflow content only.
</audit_workflow>

<evaluation_areas>
<area name="yaml_frontmatter">
Check for:

- **name**: Lowercase letters, numbers, and hyphens only; max 64 chars; matches directory name
- **description**: Max 1024 chars, no XML tags; directive style for invoked skills; passive style for reference skills and exact-name protocol or loop-body skills
- **user-invocable**: `false` for reference skills loaded by other skills; default user-invocable for audit skills, whose descriptions state their own subject and judgment without routing language
- **argument-hint**: Present when the skill takes arguments (`$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, or a declared `$name`); omit for self-contained skills

</area>

<area name="structure_and_organization">
Check for:
- **Progressive disclosure**: Apply `/skill-standards`'s complete rule. For an eager-foundation exception, verify the deterministic rendered-payload counts recorded by step 4 together with the exception's effectiveness and internal-consistency conditions.
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

**Failure Modes Documentation**:

- Does the skill document what can go wrong in practice?
- Are failures from actual usage, not hypotheticals?
- Does each failure have: what happened, why it failed, how to avoid?
- ❌ Bad: No failure modes section
- ✅ Good: "Failure 1: Claude compared coverage per-story instead of per-file. Why: Multiple stories share one legacy file. Avoid: Always compare at legacy file level."

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

- Skill-bundled files use `${CLAUDE_SKILL_DIR}/references/...` or `${CLAUDE_SKILL_DIR}/scripts/...` in authored source.
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
- **auditor_skeleton_violation**: an `audit-*` skill deviating from `/skill-standards` `references/auditor-skeleton.md` — `<output_format>` instead of `<verdict_format>`, a non-`<audit_workflow>` procedure name, a `<quick_start>` block, or an objective outside the skeleton's verdict forms. The prose auditors (`audit-prose`, `audit-internal-docs`) are exempt from the procedure-name check per the skeleton's `<prose_variant>`
- **caller_coupling**: a skill naming, describing, detecting, constraining, refusing, or branching on the agent, skill, or context that invokes it, or halting because a particular caller loaded it — per `/skill-standards` `<skill_organization>` caller independence. A description that steers the reader to dispatch an agent is this finding in the frontmatter; a `<dispatch_gate>` or equivalent caller check in the body is this finding in the body
- **hybrid_xml_markdown**: Mixing XML tags with markdown headings in body
- **unclosed_xml_tags**: XML tags not properly closed
- **vague_descriptions**: "helps with", "processes data"
- **passive_description**: Uses passive "Use when" instead of directive "ALWAYS invoke... NEVER X without this skill"
- **too_many_options**: Multiple options without clear default
- **deeply_nested_references**: References more than one level deep from SKILL.md
- **windows_paths**: Backslash paths instead of forward slashes
- **bloat**: Obvious explanations, redundant content
- **unverifiable_success_criteria**: Success criteria that can't be tested with a command or boolean check
- **no_failure_modes**: Skill lacks documentation of what went wrong in practice
- **abstract_examples**: Examples that show patterns but not concrete values/outputs
- **orphaned_references**: Files in `references/` not cited from SKILL.md or any workflow file. Verify with `grep -rn "<filename>" <skill-dir>/`. Orphans inflate token cost via speculative reads (Claude tends to open siblings of cited references) and indicate either dead content or a missing cross-reference. Flag as critical: either delete the file or add an explicit `<required_reading>` reference from the workflow that needs it.
- **heavy_context_block**: `<context>` bash commands that produce verbose or growing output (session lists, full file contents, cache enumerations) without filtering. The `<context>` block fires on every skill load — including false-positive activations from directive descriptions — so heavy commands compound. Flag as recommendation: filter the command (e.g., `--status doing,todo`, `head -N`) or move it to the workflow file that consumes the data.
- **orphaned_argument**: an argument declared in `arguments` that the body never substitutes, or a `$name` substituted in the body that `arguments` never declares. Flag as critical — the skill takes input it ignores, or substitutes an undefined name.
- **missing_argument_hint**: the skill takes arguments but omits `argument-hint`, so `/` autocomplete gives the user no signal about expected input. Flag as recommendation.
- **argument_capture_regression**: a free-form instruction skill replaces `$ARGUMENTS` with a named positional argument or numbered token without proving the replacement captures the same whole input. Flag as critical — the skill can silently drop words from user instructions.
- **codex_rendering_assumption**: authored source claims Codex directly consumes Claude-only SKILL.md syntax rather than treating Codex output as a generated rendering concern. Flag as recommendation when wording only confuses authors; flag as critical when it causes a broken generated Codex surface.
- **overbroad_allowed_tools**: `allowed-tools` grants bare `Bash`, `Bash(git *)`, or a destructive/network tool the skill's task does not need, re-admitting the destructive or exfiltrating commands a narrower grant would bar. Flag as critical for security-sensitive skills.
- **irrelevant_dynamic_context**: a `<context>` `!` block injecting state the skill never reads. Flag as recommendation — it taxes every load without payoff.
- **nonportable_bundled_file_reference**: skill prose references a bundled plugin file through repository-local authored or generated plugin paths, legacy plugin-root paths, or an authored Codex-only skill-directory token. Flag as critical: authored source must use `${CLAUDE_SKILL_DIR}/references/...` or `${CLAUDE_SKILL_DIR}/scripts/...` for files bundled with the current skill, or describe the owning workflow/capability when the file belongs elsewhere.
- **fixed_scratch_path**: skill content names a temporary path instead of deriving one per invocation — `/tmp`, `/var/tmp`, `/private/var/tmp`, `~/tmp`, or a `${TMPDIR:-/tmp}` fallback. Flag as critical per `/skill-standards` `<path_boundary>`: concurrent invocations of the skill overwrite each other's scratch state, and the path lies outside the directories the consumer's session declares. The fix is `mktemp -d` / `mktemp -t` in shell or `tempfile.mkdtemp` / `TemporaryDirectory` in Python, with removal on every exit path. Judge the surrounding intent, not the literal alone: a path inside a fenced block the skill presents as prohibited is the rule being taught, not broken.
- **unconfirmed_out_of_checkout_write**: a workflow step writes outside the invocation checkout — a home-directory configuration path, another repository's checkout, a location resolved from a registration rather than named by the operator — with no confirmation step stating the absolute destination before the write. Flag as critical: resolving a path is not authorization to write to it. A read-only inspection of such a path is not this finding.
- **boundary_evasion_guidance**: skill content frames a permission prompt, sandbox refusal, or tool-layer decline as an obstacle and documents a way around it — a shell redirect standing in for a refused tool write, a broader permission substituted for a narrow one, a path rewritten to dodge a check. Flag as critical: the skill converts one operator's approval into a standing bypass for every session that loads it. Naming which path is inside the boundary is the correct guidance; routing around the check is not.

</area>
</evaluation_areas>

<contextual_judgment>
Apply judgment based on skill complexity and purpose:

**Simple skills** (single task, <100 lines):

- Required tags only is appropriate - don't flag missing conditional tags
- Minimal examples acceptable
- Light validation sufficient
- Operational effectiveness: success criteria should still be verifiable, while failure modes remain proportional to observed history

**Complex skills** (multi-step, external APIs, security concerns):

- Missing conditional tags (security_checklist, validation, error_handling) is a real issue
- Comprehensive examples expected
- Thorough validation required
- **Operational effectiveness is CRITICAL**: Must have verifiable success criteria, observable validation, and failure modes
- Flag heavily procedural skills that lack operational content as critical issue

**Delegation skills** (invoke subagents):

- Success criteria can focus on invocation success
- Pre-validation may be redundant if subagent validates
- Operational effectiveness: subagent skill must have it; delegation skill can be lighter

**Migration/transformation skills** (change state, move files, update systems):

- **Highest operational bar**: These skills change things that are hard to undo
- MUST state authority, validation, and recovery boundaries before destructive operations
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

<verdict_format>
Emit a structured verdict. The skill's entire output is the verdict payload.

The skill's `overall` is `APPROVED` iff the `must-fix` row has no `REJECT` findings; otherwise it is `REJECTED`. An audit that cannot complete records a `REJECT` finding in `must-fix` and returns `REJECTED`. Worth-improving and keep-these-aspects observations land as `WARNING` and `INFO` findings respectively and do not reject the skill.

```json
{
  "schema_version": 1,
  "skill": "audit-skill",
  "target": "<skill-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {
      "name": "keep-these-aspects",
      "status": "PASS",
      "findings": [
        {
          "id": "f-001",
          "file": "<skill-file>",
          "line": 12,
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
          "line": 24,
          "rule": "<issue-name>",
          "severity": "WARNING",
          "message": "Current: <what exists>. Change to: <what it should be>. Benefit: <specific gain>."
        }
      ]
    },
    {
      "name": "must-fix",
      "status": "PASS | FAIL",
      "findings": [
        {
          "id": "f-003",
          "file": "<skill-file>",
          "line": 36,
          "rule": "<issue-name>",
          "severity": "REJECT",
          "message": "Current: <what exists>. Fix: <specific action>. Impact if unfixed: <what breaks>."
        }
      ]
    }
  ],
  "metadata": {
    "skill_type": "simple | complex | delegation | etc.",
    "line_count": "<n>",
    "eager_payload_code_points": { "<rendered-SKILL.md>": "<n>" }
  }
}
```

Omit `eager_payload_code_points` when the eager-foundation exception does not apply.

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
- The verdict states an overall APPROVED/REJECTED with findings grouped keep-these-aspects / worth-improving / must-fix.
- Each finding is falsifiable: it names the location (file:line), the standard at issue, and the consequence — every keep names what degrades if removed, every must-fix names the failure it prevents.
- The same SKILL.md yields the same verdict.

</success_criteria>

<validation>
Before presenting audit findings, verify:

**Completeness checks**:

- [ ] All evaluation areas assessed (including operational effectiveness)
- [ ] Findings have file:line locations
- [ ] Emitted verdict rows provide a clear summary
- [ ] Strengths identified

**Accuracy checks**:

- [ ] All line numbers verified against actual file
- [ ] Recommendations match skill complexity level
- [ ] Context appropriately considered (simple vs complex skill)
- [ ] Every eager-foundation exception includes deterministic code-point counts for every rendered target
- [ ] Operational effectiveness evaluated proportionally (critical for complex/migration skills)

**Quality checks**:

- [ ] Findings are specific and actionable
- [ ] Every "Keep" entry names the concrete consequence of removing the strength
- [ ] Every "Worth improving" entry names the specific gain, not a generic improvement
- [ ] Every "Must fix" entry names what specifically breaks if left unfixed
- [ ] No arbitrary rules applied without contextual justification

**Operational effectiveness checks** (for complex skills):

- [ ] Evaluated whether success criteria are verifiable (commands, thresholds)
- [ ] Checked for observable validation in multi-step workflows
- [ ] Looked for failure modes documentation
- [ ] Assessed procedural vs operational balance
- [ ] Flagged abstract examples that should be concrete

Only present findings after all checks pass.
</validation>
