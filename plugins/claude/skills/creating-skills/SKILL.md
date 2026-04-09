---
name: creating-skills
description: >-
  ALWAYS invoke this skill when creating, editing, or improving SKILL.md files.
  NEVER create or modify skills without this skill.
---

<essential_principles>
Skills are prompts. All prompting best practices apply. Be clear, be direct, assume Claude is smart.

**Pure XML Structure**: No markdown headings (#) in skill body. Use semantic XML tags:

- `<objective>` - What the skill does (required)
- `<success_criteria>` - How to know it worked (required)
- `<quick_start>` - Fast-path guidance (conditional — include for on-demand tools, omit for foundation/gate/validator skills)

**Progressive Disclosure**: SKILL.md under 500 lines. Details go in `references/` and `workflows/`.

**Router Pattern** (for complex skills):

```
skill-name/
├── SKILL.md              # Router + essential principles
├── workflows/            # Step-by-step procedures (FOLLOW)
├── references/           # Domain knowledge (READ)
├── templates/            # Output structures (COPY + FILL)
└── scripts/              # Executable code (RUN)
```

**Skill Types**: Match structure to purpose:

| Type       | Purpose              | Key Output                   |
| ---------- | -------------------- | ---------------------------- |
| Builder    | Create artifacts     | Code, documents, widgets     |
| Guide      | Provide instructions | Tutorials, workflows         |
| Automation | Execute workflows    | Processed files, deployments |
| Analyzer   | Extract insights     | Reports, summaries           |
| Validator  | Enforce quality      | Pass/fail assessments        |
| Reference  | Share knowledge      | Standards loaded by others   |

**Domain Discovery**: Research the domain BEFORE asking users. Users want expertise IN the skill.
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
| Response | Workflow |
|----------|----------|
| 1, "create", "new", "build" | `${CLAUDE_SKILL_DIR}/workflows/create-new-skill.md` |
| 2, "audit", "improve", "review", "check" | `${CLAUDE_SKILL_DIR}/workflows/audit-skill.md` |
| 3, "add workflow" | `${CLAUDE_SKILL_DIR}/workflows/add-workflow.md` |
| 3, "add reference" | `${CLAUDE_SKILL_DIR}/workflows/add-reference.md` |
| 3, "upgrade to router" | `${CLAUDE_SKILL_DIR}/workflows/upgrade-to-router.md` |
| 4, "patterns", "understand", "help" | Read `${CLAUDE_SKILL_DIR}/references/skill-patterns.md` |

**Intent-based routing** (if user provides clear context):

- "verify content is current" → `${CLAUDE_SKILL_DIR}/workflows/verify-skill.md`
- "audit this skill" → `${CLAUDE_SKILL_DIR}/workflows/audit-skill.md`
- "create skill for X" → `${CLAUDE_SKILL_DIR}/workflows/create-new-skill.md`

**After reading the workflow, follow it exactly.**
</routing>

<quick_reference>
**YAML Frontmatter** (required):

```yaml
---
name: skill-name # lowercase-with-hyphens, ≤64 chars
description: >- # Directive, ≤1024 chars. Add NEVER only if it disambiguates.
  ALWAYS invoke this skill when <triggers>.
---
```

**Simple Skill Structure**:

```text
<objective>What the skill does</objective>
<workflow>Step-by-step procedure</workflow>
<success_criteria>How to know it worked</success_criteria>
```

Add `<quick_start>` only for on-demand tool skills with a meaningful fast path.

**Router Skill Structure**:

```text
<essential_principles>Always applies</essential_principles>
<intake>Question to ask user</intake>
<routing>Maps answers to workflows</routing>
<reference_index>Available references</reference_index>
<workflows_index>Available workflows</workflows_index>
```

**Naming Convention**: Prefer gerund form (verb + -ing):

- `creating-skills`, `processing-pdfs`, `reviewing-code`

</quick_reference>

<reference_index>
All in `${CLAUDE_SKILL_DIR}/references/`:

| File                    | Purpose                                          |
| ----------------------- | ------------------------------------------------ |
| core-principles.md      | XML structure, conciseness, degrees of freedom   |
| use-xml-tags.md         | Required and conditional XML tags                |
| skill-patterns.md       | Type-specific patterns, templates, assets        |
| reusability-patterns.md | Variations vs constants, adaptable skills        |
| testing-patterns.md     | Evaluation-driven development, iterative testing |
| technical-patterns.md   | Error handling, security, dependencies           |

</reference_index>

<workflows_index>
All in `${CLAUDE_SKILL_DIR}/workflows/`:

| Workflow             | Purpose                                |
| -------------------- | -------------------------------------- |
| create-new-skill.md  | Build a skill from scratch             |
| audit-skill.md       | Check skill against best practices     |
| add-workflow.md      | Add a workflow to existing skill       |
| add-reference.md     | Add a reference to existing skill      |
| upgrade-to-router.md | Convert simple skill to router pattern |
| verify-skill.md      | Check if content is still accurate     |

</workflows_index>

<templates_index>
All in `${CLAUDE_SKILL_DIR}/templates/`:

| Template            | Purpose                       |
| ------------------- | ----------------------------- |
| simple-skill.md     | Single-file skill scaffold    |
| router-skill.md     | Router pattern skill scaffold |
| builder-skill.md    | Builder type template         |
| guide-skill.md      | Guide type template           |
| automation-skill.md | Automation type template      |
| analyzer-skill.md   | Analyzer type template        |
| validator-skill.md  | Validator type template       |

</templates_index>

<scripts_index>
All in `${CLAUDE_SKILL_DIR}/scripts/`:

| Script            | Purpose                              |
| ----------------- | ------------------------------------ |
| init_skill.py     | Initialize skill directory structure |
| package_skill.py  | Validate and package skill           |
| quick_validate.py | Quick YAML/structure validation      |

</scripts_index>

<success_criteria>
A well-structured skill:

- Has valid YAML frontmatter (name + description)
- Uses pure XML structure (no markdown headings in body)
- Has essential principles inline in SKILL.md (if router pattern)
- Routes to appropriate workflows based on user intent
- Keeps SKILL.md under 500 lines
- Has been tested with real usage

</success_criteria>
