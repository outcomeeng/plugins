---
name: create-skill
description: >-
  ALWAYS invoke this skill when creating, editing, or improving skills or bundled skill components, including SKILL.md, workflows, references, templates, or scripts.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Skill, WebFetch, WebSearch
---

{!% require_skill 'instructions:skill-standards' %!}

{!% require_skill 'instructions:agent-prompt-standards' %!}

<objective>
A skill-authoring request routed to its matching typed workflow.
</objective>

<essential_principles>

- Apply `/skill-standards` and the repository's `spx/local/skills.md` overlay before proposing any skill name.
- Classify every skill name independently. A shared word, suffix, or grammatical number never establishes a batch rename.
- Keep audit-only work read-only. Apply changes only when the operator requested creation or improvement.

</essential_principles>

<reference_loading>
Before creating, editing, or auditing any skill, read `/skill-standards` — the single source of truth for all skill standards (frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence rules, bash restrictions, validation, script testing). Then check for `spx/local/skills.md` at the repository root and read it if it exists.

Also read `/agent-prompt-standards` for voice, description style, constraint language, and anti-pattern conventions before writing prompt text.

When the skill takes arguments, injects state-dependent context, restricts tools, or references files — the capabilities a slash command also carried — follow the command-capability rules `/skill-standards` carries (its `<frontmatter>` points to the `command-capabilities` reference) for `argument-hint`/`arguments`, `!`-dynamic-context, `allowed-tools`-security, and `@`-file references before authoring that surface.

This skill provides routing, workflows, templates, and domain-workflow references for creating skills. It does not restate standards.
</reference_loading>

<intake>
What would you like to do?

1. Create a new skill
2. Audit or improve an existing skill
3. Add a workflow
4. Add a reference
5. Add a template
6. Add a script
7. Upgrade a skill to a router
8. Understand skill patterns
9. Verify skill content is current

**Wait for response before proceeding.**
</intake>

<routing>

| Response                                 | Workflow                                               |
| ---------------------------------------- | ------------------------------------------------------ |
| 1, "create", "new", "build"              | `${CLAUDE_SKILL_DIR}/workflows/create-new-skill.md`    |
| 2, "audit", "improve", "review", "check" | `${CLAUDE_SKILL_DIR}/workflows/audit-skill.md`         |
| 3, "add workflow"                        | `${CLAUDE_SKILL_DIR}/workflows/add-workflow.md`        |
| 4, "add reference"                       | `${CLAUDE_SKILL_DIR}/workflows/add-reference.md`       |
| 5, "add template"                        | `${CLAUDE_SKILL_DIR}/workflows/add-template.md`        |
| 6, "add script"                          | `${CLAUDE_SKILL_DIR}/workflows/add-script.md`          |
| 7, "upgrade to router"                   | `${CLAUDE_SKILL_DIR}/workflows/upgrade-to-router.md`   |
| 8, "patterns", "understand", "help"      | `${CLAUDE_SKILL_DIR}/workflows/understand-patterns.md` |
| 9, "verify content", "current"           | `${CLAUDE_SKILL_DIR}/workflows/verify-skill.md`        |

**Intent-based routing** (if user provides clear context):

- "verify content is current" → `${CLAUDE_SKILL_DIR}/workflows/verify-skill.md`
- "audit this skill" → `${CLAUDE_SKILL_DIR}/workflows/audit-skill.md`
- "create skill for X" → `${CLAUDE_SKILL_DIR}/workflows/create-new-skill.md`
- "add a template" → `${CLAUDE_SKILL_DIR}/workflows/add-template.md`
- "add a script" → `${CLAUDE_SKILL_DIR}/workflows/add-script.md`
- "explain skill patterns" → `${CLAUDE_SKILL_DIR}/workflows/understand-patterns.md`

**After reading the workflow, follow it exactly.**

</routing>

<reference_index>
All in `${CLAUDE_SKILL_DIR}/references/`:

| File                      | Purpose                                                          |
| ------------------------- | ---------------------------------------------------------------- |
| `reusability-patterns.md` | Varies-vs-constant analysis, domain-specific authoring patterns  |
| `test-patterns.md`        | Evaluation-driven development, iterative testing, feedback loops |
| `technical-patterns.md`   | Error handling, security, dependencies for skills-that-do-things |

Standards live in `/skill-standards`. These references cover authoring workflow only.

</reference_index>

<workflows_index>
All in `${CLAUDE_SKILL_DIR}/workflows/`:

| Workflow                 | Purpose                                |
| ------------------------ | -------------------------------------- |
| `create-new-skill.md`    | Build a skill from scratch             |
| `audit-skill.md`         | Check skill against best practices     |
| `add-workflow.md`        | Add a workflow to existing skill       |
| `add-reference.md`       | Add a reference to existing skill      |
| `add-template.md`        | Add a reusable skill template          |
| `add-script.md`          | Add a tested executable skill script   |
| `upgrade-to-router.md`   | Convert simple skill to router pattern |
| `understand-patterns.md` | Explain applicable authoring patterns  |
| `verify-skill.md`        | Check if content is still accurate     |

</workflows_index>

<templates_index>
All in `${CLAUDE_SKILL_DIR}/templates/`:

| Template              | Purpose                       |
| --------------------- | ----------------------------- |
| `simple-skill.md`     | Single-file skill scaffold    |
| `router-skill.md`     | Router pattern skill scaffold |
| `builder-skill.md`    | Builder type template         |
| `guide-skill.md`      | Guide type template           |
| `automation-skill.md` | Automation type template      |
| `analyzer-skill.md`   | Analyzer type template        |
| `validator-skill.md`  | Validator type template       |
| `reference-skill.md`  | Reference type template       |

</templates_index>

<success_criteria>

- Representative input selects exactly one intended workflow, and every routing target exists in `<workflows_index>`.
- Each selected workflow loads only the standards and conditional references its route requires.
- A produced or improved skill passes the target repository's deterministic skill checks and an independent `/audit-skills` audit with zero must-fix items against `/skill-standards`.

</success_criteria>

<failure_modes>

**Failure 1: Claude generalized one rename across unlike skill types.** Claude saw plural workflow names and `-standards` reference names in one plugin, then proposed singularizing every shared-looking name before classifying each skill. The proposal contradicted the reference-skill `{domain}-standards` convention and treated grammatical number as a mechanical rule. Before any rename, emit the classification matrix required by the selected workflow, read declared vocabulary and relevant file history, and decide each name from its own skill type and invocation semantics.

</failure_modes>
