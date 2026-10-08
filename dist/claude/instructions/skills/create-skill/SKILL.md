---
name: create-skill
description: >-
  ALWAYS invoke this skill when creating, editing, or improving SKILL.md files or bundled workflows, references, templates, and scripts; explaining skill patterns; or verifying that skill content is current.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Skill, WebFetch, WebSearch
---

Use skill `instructions:skill-standards`.

Use skill `instructions:agent-prompt-standards`.

<objective>
A skill-authoring request routed to its matching typed workflow.
</objective>

<essential_principles>

- Apply every rule in the `/skill-standards` and `/agent-prompt-standards` rule catalogs to the bundle a route produces or changes, and return that bundle ready for independent verification once the target repository's deterministic skill checks pass.
- Dispatch no skill auditor and wait on no audit verdict. A verdict on a skill comes from `/audit-skill` run in an agent session separate from the one that authored the skill; the findings it records enter this skill as repair input.
- Apply changes only for a request to create, improve, or repair a skill. Pattern questions and verification without requested updates change no file.

</essential_principles>

<reference_loading>
When the skill takes arguments, injects state-dependent context, restricts tools, or references files, read `/skill-standards`'s `references/command-capabilities.md` before authoring that surface.

This skill provides routing, workflows, templates, and domain-workflow references for creating skills. It does not restate standards.
</reference_loading>

<material_change_name_review>

Before any route creates or materially changes skill content, apply `/skill-standards` `<naming_conventions>` and the repository's skill-authoring overlay. When repository policy requires plugin-wide naming review, produce this matrix for every skill the policy requires reviewing before route-specific edits begin:

| Current name | Skill type | Governing naming form | Proposed name or keep | Reason |
| ------------ | ---------- | --------------------- | --------------------- | ------ |

Classify every skill name independently. Read the source that declares any overlapping methodology vocabulary and inspect relevant file history before classifying a name as defective. Never infer a batch rename from a shared lexical token, suffix, or grammatical number. Apply only explicit operator-directed renames and names the classification proves nonconforming. Read-only routes skip this mutation gate.

</material_change_name_review>

<intake>
When the request already identifies one intent below, skip this menu and route directly. Otherwise ask:

What would you like to do?

1. Create a new skill
2. Improve or repair an existing skill
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

| Response                                          | Workflow                                               |
| ------------------------------------------------- | ------------------------------------------------------ |
| 1, "create", "new", "build"                       | `${CLAUDE_SKILL_DIR}/workflows/create-new-skill.md`    |
| 2, "improve", "edit", "repair", supplied findings | `${CLAUDE_SKILL_DIR}/workflows/repair-skill.md`        |
| 3, "add workflow"                                 | `${CLAUDE_SKILL_DIR}/workflows/add-workflow.md`        |
| 4, "add reference"                                | `${CLAUDE_SKILL_DIR}/workflows/add-reference.md`       |
| 5, "add template"                                 | `${CLAUDE_SKILL_DIR}/workflows/add-template.md`        |
| 6, "add script"                                   | `${CLAUDE_SKILL_DIR}/workflows/add-script.md`          |
| 7, "upgrade to router"                            | `${CLAUDE_SKILL_DIR}/workflows/upgrade-to-router.md`   |
| 8, "patterns", "understand patterns"              | `${CLAUDE_SKILL_DIR}/workflows/understand-patterns.md` |
| 9, "verify content", "current"                    | `${CLAUDE_SKILL_DIR}/workflows/verify-skill.md`        |

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
| `repair-skill.md`        | Repair findings or apply improvements  |
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
- A produced, improved, or repaired bundle passes the target repository's deterministic skill checks, violates no rule in the `/skill-standards` or `/agent-prompt-standards` rule catalog, and is returned with no audit dispatched or awaited.

</success_criteria>

<failure_modes>

**Failure 1: Claude generalized one rename across unlike skill types.** Claude saw plural workflow names and `-standards` reference names in one plugin, then proposed singularizing every shared-looking name before classifying each skill. The proposal contradicted the reference-skill `{domain}-standards` convention and treated grammatical number as a mechanical rule. Before any rename, emit the classification matrix required by the selected workflow, read declared vocabulary and relevant file history, and decide each name from its own skill type and invocation semantics.

**Failure 2: Claude looped one authoring round on audit verdicts.** Every route dispatched the skill auditor and repaired until a sealed run approved. Each run named its rules in its own words, so a finding on unchanged text reversed between runs, and one round launched audit after audit chasing findings the next run withdrew. Return the bundle once the deterministic checks pass and every catalog rule is applied; independent verification judges it outside this skill, and its findings come back through the repair route.

</failure_modes>
