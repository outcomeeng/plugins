---
name: creating-skills
description: >-
  ALWAYS invoke this skill when creating, editing, or improving SKILL.md files.
---

<objective>
Route skill-creation, editing, and improvement work through typed workflows. Standards and anti-patterns live in `/standardizing-skills` and `/standardizing-agent-prompts`; this skill loads them, asks the user which workflow to run, and points at the right scaffold.
</objective>

<reference_loading>
Before creating, editing, or auditing any skill, read `/standardizing-skills` — the single source of truth for all skill standards (frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence rules, bash restrictions, validation, script testing). Then check for `spx/local/standardizing-skills.md` at the repository root and read it if it exists.

Also read `/standardizing-agent-prompts` for voice, description style, constraint language, and anti-pattern conventions before writing prompt text.

This skill provides routing, workflows, templates, and domain-workflow references for creating skills. It does not restate standards.
</reference_loading>

<intake>
What would you like to do?

1. Create a new skill
2. Audit or improve an existing skill
3. Add a component (workflow, reference, template, script)
4. Understand skill patterns

**Wait for response before proceeding.**
</intake>

<routing>

| Response                                 | Workflow                                                                                                                      |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 1, "create", "new", "build"              | `${CLAUDE_SKILL_DIR}/workflows/create-new-skill.md`                                                                           |
| 2, "audit", "improve", "review", "check" | `${CLAUDE_SKILL_DIR}/workflows/audit-skill.md`                                                                                |
| 3, "add workflow"                        | `${CLAUDE_SKILL_DIR}/workflows/add-workflow.md`                                                                               |
| 3, "add reference"                       | `${CLAUDE_SKILL_DIR}/workflows/add-reference.md`                                                                              |
| 3, "upgrade to router"                   | `${CLAUDE_SKILL_DIR}/workflows/upgrade-to-router.md`                                                                          |
| 4, "patterns", "understand", "help"      | Read `/standardizing-skills` for structure; then `${CLAUDE_SKILL_DIR}/references/reusability-patterns.md` for domain patterns |

**Intent-based routing** (if user provides clear context):

- "verify content is current" → `${CLAUDE_SKILL_DIR}/workflows/verify-skill.md`
- "audit this skill" → `${CLAUDE_SKILL_DIR}/workflows/audit-skill.md`
- "create skill for X" → `${CLAUDE_SKILL_DIR}/workflows/create-new-skill.md`

**After reading the workflow, follow it exactly.**

</routing>

<reference_index>
All in `${CLAUDE_SKILL_DIR}/references/`:

| File                      | Purpose                                                          |
| ------------------------- | ---------------------------------------------------------------- |
| `reusability-patterns.md` | Varies-vs-constant analysis, domain-specific authoring patterns  |
| `testing-patterns.md`     | Evaluation-driven development, iterative testing, feedback loops |
| `technical-patterns.md`   | Error handling, security, dependencies for skills-that-do-things |

Standards live in `/standardizing-skills`. These references cover authoring workflow only.

</reference_index>

<workflows_index>
All in `${CLAUDE_SKILL_DIR}/workflows/`:

| Workflow               | Purpose                                |
| ---------------------- | -------------------------------------- |
| `create-new-skill.md`  | Build a skill from scratch             |
| `audit-skill.md`       | Check skill against best practices     |
| `add-workflow.md`      | Add a workflow to existing skill       |
| `add-reference.md`     | Add a reference to existing skill      |
| `upgrade-to-router.md` | Convert simple skill to router pattern |
| `verify-skill.md`      | Check if content is still accurate     |

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

</templates_index>

<scripts_index>
All in `${CLAUDE_SKILL_DIR}/scripts/`:

| Script              | Purpose                              |
| ------------------- | ------------------------------------ |
| `init_skill.py`     | Initialize skill directory structure |
| `package_skill.py`  | Validate and package skill           |
| `quick_validate.py` | Quick YAML/structure validation      |

</scripts_index>

<success_criteria>
A well-structured skill passes `/auditing-skills` with zero must-fix items against the standards in `/standardizing-skills`.
</success_criteria>
