---
name: audit-commands
description: >-
  ALWAYS invoke this skill when auditing, reviewing, or evaluating slash command .md files.
  NEVER audit slash commands without this skill.
argument-hint: <command-path>
---

Invoke the `develop:create-commands` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `develop:agent-prompt-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Evaluate slash command .md files against best practices for structure, YAML configuration, argument usage, dynamic context, tool restrictions, and effectiveness. Then provide actionable findings with contextual judgment, not arbitrary scores.

This ensures commands follow security, clarity, and effectiveness standards.
</objective>

<quick_start>

1. Read best practices from the create-commands skill and its reference files
2. Read the command file at `$ARGUMENTS`
3. Evaluate against all areas: YAML, arguments, dynamic context, tool restrictions, content
4. Report findings using the severity-based output format

</quick_start>

<constraints>
- NEVER modify files during audit - ONLY analyze and report findings
- MUST read all reference documentation before evaluating
- ALWAYS provide file:line locations for every finding
- DO NOT generate fixes unless explicitly requested by the user
- NEVER make assumptions about command intent - flag ambiguities as findings
- MUST complete all evaluation areas (YAML, Arguments, Dynamic Context, Tool Restrictions, Content)
- ALWAYS apply contextual judgment based on command purpose and complexity

</constraints>

<focus_areas>
During audits, prioritize evaluation of:

- YAML compliance (description quality, allowed-tools configuration, argument-hint)
- Argument usage ($ARGUMENTS, positional arguments $1/$2/$3)
- Dynamic context loading (proper use of exclamation mark + backtick syntax)
- Tool restrictions (security, appropriate scope)
- File references (@ prefix usage)
- Clarity and specificity of prompt
- Multi-step workflow structure
- Security patterns (preventing destructive operations, data exfiltration)

</focus_areas>

<critical_workflow>
**MANDATORY**: Read best practices FIRST, before auditing:

1. Both skills are already injected above. Read the create-commands reference files:
   - `${CLAUDE_SKILL_DIR}/../create-commands/references/arguments.md`
   - `${CLAUDE_SKILL_DIR}/../create-commands/references/patterns.md`
   - `${CLAUDE_SKILL_DIR}/../create-commands/references/tool-restrictions.md`
2. The agent-prompt-standards skill is already injected above — covers voice, description style, constraint language, and anti-patterns.
3. Handle edge cases:
   - If reference files are missing or unreadable, note in findings under "Configuration Issues" and proceed with available content
   - If YAML frontmatter is malformed, flag as critical issue
   - If command references external files that don't exist, flag as critical issue and recommend fixing broken references
   - If command is <10 lines, note as "simple command" in context and evaluate accordingly
4. Read the command file at `$ARGUMENTS`
5. Evaluate against best practices from steps 1-3

**Use ACTUAL patterns from references, not memory.**
</critical_workflow>

<evaluation_areas>
<area name="yaml_configuration">
Check for:

- **description**: Clear, specific description of what the command does. No vague terms like "helps with" or "processes data". Should describe the action clearly.
- **allowed-tools**: Present when appropriate for security (git commands, thinking-only, read-only analysis). Properly formatted (array or bash patterns).
- **argument-hint**: Present when command uses arguments. Clear indication of expected arguments format.

</area>

<area name="arguments">
Check for:
- **Appropriate argument type**: Uses $ARGUMENTS for simple pass-through, positional ($1, $2, $3) for structured input
- **Argument integration**: Arguments properly integrated into prompt (e.g., "Fix issue #$ARGUMENTS", "@$ARGUMENTS")
- **Handling empty arguments**: Command works with or without arguments when appropriate, or clearly requires arguments

</area>

<area name="dynamic_context">
Check for:
- **Context loading**: Uses exclamation mark + backtick syntax for state-dependent tasks (git status, environment info)
- **Context relevance**: Loaded context is directly relevant to command purpose

</area>

<area name="tool_restrictions">
Check for:
- **Security appropriateness**: Restricts tools for security-sensitive operations (git-only, read-only, thinking-only)
- **Restriction specificity**: Uses specific patterns (Bash(git add:*)) rather than overly broad access

</area>

<area name="content_quality">
Check for:
- **Clarity**: Prompt is clear, direct, specific
- **Structure**: Multi-step workflows properly structured with numbered steps or sections
- **File references**: Uses @ prefix for file references when appropriate

</area>

<area name="prompt_craft">
Check against `/agent-prompt-standards` conventions:

- **Voice**: Uses imperative mood for instructions, "Claude" for failure modes/tendencies. Never "the agent", "the model", or "you"
- **Constraint language**: Strong modal verbs (MUST/NEVER/ALWAYS) in constraint blocks
- **Anti-patterns**: No banned phrases ("helpful assistant", "helps with", "please", "if possible"). No structural anti-patterns (explaining Claude to Claude, motivational prose)
- **Conciseness**: Only information Claude doesn't already have

</area>

<area name="anti_patterns">
Flag these issues:
- Vague descriptions ("helps with", "processes data")
- Missing tool restrictions for security-sensitive operations (git, deployment)
- No dynamic context for state-dependent tasks (git commands without git status)
- Poor argument integration (arguments not used or used incorrectly)
- Overly complex commands (should be broken into multiple commands)
- Missing description field
- Unclear instructions without structure

</area>
</evaluation_areas>

<contextual_judgment>
Apply judgment based on command purpose and complexity:

**Simple commands** (single action, no state):

- Dynamic context may not be needed - don't flag its absence
- Minimal tool restrictions may be appropriate
- Brief prompts are fine

**State-dependent commands** (git, environment-aware):

- Missing dynamic context is a real issue
- Tool restrictions become important

**Security-sensitive commands** (git push, deployment, file modification):

- Missing tool restrictions is critical
- Should have specific patterns, not broad access

**Delegation commands** (invoke subagents):

- `allowed-tools: Task` is appropriate
- Success criteria can focus on invocation
- Pre-validation may be redundant if subagent validates

Always explain WHY something matters for this specific command, not just that it violates a rule.
</contextual_judgment>

<output_format>
Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff the `critical-issues` row has no findings with severity `REJECT`; `FAIL` if any critical finding is `REJECT`; `UNKNOWN` if the command file cannot be read or the audit cannot complete. Recommendations land as `WARNING` findings under `recommendations`; strengths land as `INFO` findings under `strengths`; quick fixes land as `INFO` findings under `quick-fixes`.

```json
{
  "schema_version": 1,
  "skill": "audit-commands",
  "target": "<command-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    {
      "name": "critical-issues",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": [
        {
          "id": "f-001",
          "file": "<command-file>",
          "line": null,
          "rule": "<issue-category>",
          "severity": "REJECT",
          "message": "Current: <…>. Should be: <…>. Why it matters: <…>. Fix: <…>."
        }
      ]
    },
    { "name": "recommendations", "status": "PASS", "findings": [] },
    { "name": "strengths", "status": "PASS", "findings": [] },
    { "name": "quick-fixes", "status": "PASS", "findings": [] }
  ],
  "metadata": {
    "command_type": "simple | state-dependent | security-sensitive | delegation",
    "line_count": "<n>",
    "security_profile": "none | low | medium | high"
  }
}
```

</output_format>

<validation>
Before presenting audit findings, verify:

**Completeness checks**:

- [ ] All evaluation areas assessed (YAML, Arguments, Dynamic Context, Tool Restrictions, Content)
- [ ] Findings have file:line locations
- [ ] Assessment section provides clear summary
- [ ] Strengths identified

**Accuracy checks**:

- [ ] All line numbers verified against actual file
- [ ] Recommendations match command complexity level
- [ ] Context appropriately considered (simple vs state-dependent vs security-sensitive)

**Quality checks**:

- [ ] Findings are specific and actionable
- [ ] "Why it matters" explains impact for THIS command
- [ ] Remediation steps are clear
- [ ] No arbitrary rules applied without contextual justification

Only present findings after all checks pass.
</validation>

<success_criteria>
Task is complete when:

- All reference documentation files have been read and incorporated
- All evaluation areas assessed (YAML, Arguments, Dynamic Context, Tool Restrictions, Content)
- Contextual judgment applied based on command type and purpose
- Findings categorized by severity (Critical, Recommendations, Quick Fixes)
- At least 3 specific findings provided with file:line locations (or explicit note that command is well-formed)
- Assessment provides clear, actionable guidance
- Strengths documented (what's working well)
- Context section includes command type and security profile
- Next-step options presented to reduce user cognitive load

</success_criteria>

<final_step>
After presenting findings, offer:

1. Implement all fixes automatically
2. Show detailed examples for specific issues
3. Focus on critical issues only
4. Other

</final_step>
