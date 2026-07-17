---
name: create-skills
description: >-
  ALWAYS invoke this skill when creating, editing, improving, or extending skills, or when learning skill-authoring patterns.
allowed-tools: Read, Glob, Grep, Write, Edit, Agent, Skill, request_user_input, Bash(python3 "${SKILL_DIR}/scripts/quick_validate.py":*), Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*)
---

Invoke the `instructions:skill-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `instructions:agent-prompt-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A completed skill-authoring or pattern-understanding result produced through the matching typed workflow or reference.
</objective>

<essential_principles>
Before creating, editing, or auditing any skill, read `/skill-standards` — the single source of truth for all skill standards (frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence rules, bash restrictions, validation, script testing). Then check for `spx/local/skills.md` at the repository root and read it if it exists.

Also read `/agent-prompt-standards` for voice, description style, constraint language, and anti-pattern conventions before writing prompt text.

When the skill takes arguments, injects state-dependent context, restricts tools, or references files — the capabilities a slash command also carried — follow the command-capability rules `/skill-standards` carries (its `<frontmatter>` points to the `command-capabilities` reference) for `argument-hint`/`arguments`, `!`-dynamic-context, `allowed-tools`-security, and `@`-file references before authoring that surface.

This skill provides routing, workflows, templates, and domain-workflow references for creating skills. It does not restate standards.

Use Bash only for the bundled structural validator, generated-script success/failure tests, and the clean checkpoint those gates require. Identify the target repository's declared build and deterministic-check commands and return them to the caller's repository workflow; this portable skill does not pre-authorize product-specific command names.
</essential_principles>

<intake>
What would you like to do?

1. Create a new skill
2. Audit or improve an existing skill
3. Add a component (workflow, reference, template, script)
4. Understand skill patterns

**Wait for response before proceeding.**
</intake>

<routing>

| Response                                 | Workflow                                                                                                          |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 1, "create", "new", "build"              | `${SKILL_DIR}/workflows/create-new-skill.md`                                                                      |
| 2, "audit", "improve", "review", "check" | `${SKILL_DIR}/workflows/audit-skill.md`                                                                           |
| 3, "add workflow"                        | `${SKILL_DIR}/workflows/add-workflow.md`                                                                          |
| 3, "add reference"                       | `${SKILL_DIR}/workflows/add-reference.md`                                                                         |
| 3, "upgrade to router"                   | `${SKILL_DIR}/workflows/upgrade-to-router.md`                                                                     |
| 4, "patterns", "understand", "help"      | Read `/skill-standards` for structure; then `${SKILL_DIR}/references/reusability-patterns.md` for domain patterns |

**Intent-based routing** (if user provides clear context):

- "verify content is current" → `${SKILL_DIR}/workflows/verify-skill.md`
- "audit this skill" → `${SKILL_DIR}/workflows/audit-skill.md`
- "create skill for X" → `${SKILL_DIR}/workflows/create-new-skill.md`

**After reading the workflow, follow it exactly.**

</routing>

<reference_index>
All in `${SKILL_DIR}/references/`:

| File                      | Purpose                                                          |
| ------------------------- | ---------------------------------------------------------------- |
| `reusability-patterns.md` | Varies-vs-constant analysis, domain-specific authoring patterns  |
| `test-patterns.md`        | Evaluation-driven development, iterative testing, feedback loops |
| `technical-patterns.md`   | Error handling, security, dependencies for skills-that-do-things |

Standards live in `/skill-standards`. These references cover authoring workflow only.

</reference_index>

<workflows_index>
All in `${SKILL_DIR}/workflows/`:

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
All in `${SKILL_DIR}/templates/`:

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
All in `${SKILL_DIR}/scripts/`:

| Script              | Purpose                              |
| ------------------- | ------------------------------------ |
| `init_skill.py`     | Initialize skill directory structure |
| `package_skill.py`  | Validate and package skill           |
| `quick_validate.py` | Quick YAML/structure validation      |

</scripts_index>

<success_criteria>

- [ ] The request routes to exactly one matching workflow or pattern reference.
- [ ] An authoring result passes `/audit-skills` with zero must-fix items against `/skill-standards`.
- [ ] A pattern-understanding result cites `/skill-standards` and the relevant authoring reference without changing files unless the user requested a change.

</success_criteria>
