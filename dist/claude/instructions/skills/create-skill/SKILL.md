---
name: create-skill
description: >-
  ALWAYS invoke this skill when creating, editing, or improving SKILL.md files or bundled workflows, references, templates, and scripts; explaining skill patterns; or verifying that skill content is current.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Skill, Agent, WebFetch, WebSearch
---

Invoke the `instructions:skill-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `instructions:agent-prompt-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A skill-authoring request routed to its matching typed workflow.
</objective>

<essential_principles>

- Before any material skill change, apply `/skill-standards` and the repository overlay's required plugin-wide naming review.
- Classify every skill name independently. A shared word, suffix, or grammatical number never establishes a batch rename.
- Keep audit-only work read-only. Apply changes only when the operator requested creation or improvement.
- Dispatch every skill audit through the typed `skill-auditor` role. If the role is unavailable or returns no complete structured verdict, report `BLOCKED`; never invoke `/audit-skill` in the authoring context.

</essential_principles>

<reference_loading>
Before creating, editing, or auditing any skill, read `/skill-standards`, then check for `spx/local/skills.md` at the repository root and read it if it exists.

Also read `/agent-prompt-standards` for voice, description style, constraint language, and anti-pattern conventions before writing prompt text.

When the skill takes arguments, injects state-dependent context, restricts tools, or references files, read `/skill-standards`'s `references/command-capabilities.md` before authoring that surface.

This skill provides routing, workflows, templates, and domain-workflow references for creating skills. It does not restate standards.
</reference_loading>

<material_change_name_review>

Before any route creates or materially changes skill content, apply `/skill-standards` `<naming_conventions>` and the repository's skill-authoring overlay. When repository policy requires plugin-wide naming review, produce this matrix for every skill the policy requires reviewing before route-specific edits begin:

| Current name | Skill type | Governing naming form | Proposed name or keep | Reason |
| ------------ | ---------- | --------------------- | --------------------- | ------ |

Read the source that declares any overlapping methodology vocabulary and inspect relevant file history before classifying a name as defective. Never infer a batch rename from a shared lexical token, suffix, or grammatical number. Apply only explicit operator-directed renames and names the classification proves nonconforming. Audit-only requests and read-only pattern questions skip this mutation gate.

</material_change_name_review>

<intake>
When the request already identifies one intent below, skip this menu and route directly. Otherwise ask:

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

**Wait for a response only after asking this menu.**
</intake>

<routing>

| Response                                         | Workflow                                               |
| ------------------------------------------------ | ------------------------------------------------------ |
| 1, "create", "new", "build"                      | `${CLAUDE_SKILL_DIR}/workflows/create-new-skill.md`    |
| 2, "audit", "improve", "review", "check quality" | `${CLAUDE_SKILL_DIR}/workflows/audit-skill.md`         |
| 3, "add workflow"                                | `${CLAUDE_SKILL_DIR}/workflows/add-workflow.md`        |
| 4, "add reference"                               | `${CLAUDE_SKILL_DIR}/workflows/add-reference.md`       |
| 5, "add template"                                | `${CLAUDE_SKILL_DIR}/workflows/add-template.md`        |
| 6, "add script"                                  | `${CLAUDE_SKILL_DIR}/workflows/add-script.md`          |
| 7, "upgrade to router"                           | `${CLAUDE_SKILL_DIR}/workflows/upgrade-to-router.md`   |
| 8, "patterns", "understand patterns"             | `${CLAUDE_SKILL_DIR}/workflows/understand-patterns.md` |
| 9, "verify content", "current"                   | `${CLAUDE_SKILL_DIR}/workflows/verify-skill.md`        |

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
| `auditor-skill.md`    | Auditor type template         |
| `validator-skill.md`  | Validator type template       |
| `reference-skill.md`  | Reference type template       |

</templates_index>

<success_criteria>

- For every route, one canonical trigger and its nearest adjacent trigger select exactly the intended workflow, and every routing target exists in `<workflows_index>`.
- Each selected workflow loads only the standards and conditional references its route requires.
- Each selected workflow produces the output declared by its own success criteria.
- A produced or improved skill passes the target repository's deterministic skill checks and receives an `APPROVED` verdict from the typed `skill-auditor` over the complete bundle.

</success_criteria>

<failure_modes>

**Failure 1: Claude generalized one rename across unlike skill types.** Claude saw plural workflow names and `-standards` reference names in one plugin, then proposed singularizing every shared-looking name before classifying each skill. The proposal contradicted the reference-skill `{domain}-standards` convention and treated grammatical number as a mechanical rule. Before any rename, emit the classification matrix required by the selected workflow, read declared vocabulary and relevant file history, and decide each name from its own skill type and invocation semantics.

</failure_modes>
