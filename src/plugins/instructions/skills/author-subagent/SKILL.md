---
name: author-subagent
description: >-
  ALWAYS invoke this skill when creating, editing, or configuring {{! term('configured_agents') !}}.
  NEVER create {{! term('configured_agents') !}} without this skill.
argument-hint: "<configuration-path-or-role> [repair-input]"
arguments: configuration_target
allowed-tools: Read, Glob, Write, Edit, Bash, {{! tool('use_skill') !}}
---

{!% require_skill 'instructions:subagent-standards' %!}

{!% require_skill 'instructions:agent-prompt-standards' %!}

{!% require_skill 'instructions:skill-standards' %!}

<objective>
A finished {{! term('configured_agent') !}} definition and its calling-skill integration,
ready for independent verification, with native configuration and a declared result contract.
</objective>

<constraints>

- ALWAYS: apply every rule in the `/subagent-standards` and `/agent-prompt-standards` rule
  catalogs to the finished definition, and return it ready for independent verification once
  the product's author command and deterministic checks pass on it.
- NEVER: dispatch a {{! term('configured_agent') !}} auditor or wait on an audit verdict — a
  verdict on the definition comes from `/audit-subagent` run in an agent session separate from
  the one that authored it.
- ALWAYS: write to the invocation checkout. Reach a user-scope destination outside it —
  creating, editing, or deleting — only after the operator confirms the exact absolute
  destination; one approval covers one write.
- NEVER: widen an approved checkout-scope write to user scope on the judgment that the
  configured agent suits other projects.

</constraints>

<intake>

Select the route from the task message:

| Task message carries                                                                                   | Route                    |
| ------------------------------------------------------------------------------------------------------ | ------------------------ |
| A target path or role only                                                                             | `<workflow>`             |
| A target followed by a sealed run file and the instruction to attend to every rule the run names       | `<repair_from_run_file>` |
| A target followed by the command line and complete output of a deterministic command that failed on it | `<repair_from_command>`  |

</intake>

<workflow>

1. Require `$configuration_target`. When it is empty, return a `blocked` result naming the
   missing configuration path or role. Read the requested target and its governing requirements. Identify the role's
   owning skill, exact configured name, destination, selected profile, and result.
   Return a `blocked` result naming the missing input when a product decision or a required
   input is absent. When the definition already holds the requested result, return an
   `unchanged` result naming the committed head and the path that holds it, and edit nothing.
2. Apply `/subagent-standards` to placement, capabilities, profiles, isolation,
   invocation, and evidence. Read the relevant references from the index below.
3. For a skill-backed role, author a thin wrapper that invokes the owning skill
   and relays its result. Keep task-specific behavior in that skill.
4. For a marketplace source, declare `profile: standard`, `profile: strong`,
   `profile: executor`, or `profile: fast` according to the governing selection. Let the product build
   emit the complete native configuration. For a product-owned native definition,
   use the selected complete configuration supplied by the loaded standards and examples.
5. Use skill `instructions:author-skill`. Update the calling skill through it so its
   explicit launch names the configured role and supplies only the target.
6. Run the product's author command, then apply `/subagent-standards` `<configuration_subject>`
   to identify the authored input and exact emitted definitions, or the directly authored
   native definition.
7. Check the finished definition against every row of the `/subagent-standards` and
   `/agent-prompt-standards` rule catalogs, each row at the surface its stating section
   names — template syntax and profile selection at the authored input, native fields,
   permissions, and complete profile values in each emitted definition. Repair each
   violation at its authored source and repeat steps 6 and 7 until no row is violated.
8. Run the focused deterministic checks, then preserve the exact definition through the
   product's normal checkpoint workflow. A later edit repeats steps 6 to 8, so the
   returned definition is the state those checks passed on.
9. Return the configuration path, the configured role, the emitted definitions, and the
   verification still outstanding under `/subagent-standards`: an `/audit-subagent` run in
   a separate agent session, and native loading with one minimal isolated execution of the
   emitted definition.

This skill launches no configuration it authors.

</workflow>

<repair_from_run_file>

Read every finding to repair, by its `<unit>:<rule-id>` key, from the run file alone, and read
the definition to repair from the unit the run records for it. Ignore any summary, remedy, or
class name in the task message. Attend to every rule the run names and sweep each named class
across the whole target. Then follow the `<repair>` steps.

</repair_from_run_file>

<repair_from_command>

Repair the defect the command's output names at its authored source, never in an emitted
definition. Then follow the `<repair>` steps.

</repair_from_command>

<repair>

1. Repair each finding across every instance the cited clause covers, and change nothing the
   clause does not require.
2. Before returning, list every same-class site and every dependency the repair changed — a
   renamed field, a changed profile, a changed result contract — and resolve each, in the
   authored input and in each emitted definition.
3. Run workflow steps 6 to 8 on the repaired definition.
4. Return the repaired definition with, for each repair, the clause applied and the check that
   shows the class closed, plus the outstanding verification the workflow names. Return a
   `blocked` result naming the missing input when the run file or the command output is absent.

</repair>

<reference>

Read only the references relevant to the role's actual work:

- [subagents.md](${CLAUDE_SKILL_DIR}/references/subagents.md): native definitions,
  complete profile examples, capability selection, and skill-backed wrappers.
- [write-subagent-prompts.md](${CLAUDE_SKILL_DIR}/references/write-subagent-prompts.md):
  converting a role requirement into a focused prompt and result contract.
- [evaluation-and-testing.md](${CLAUDE_SKILL_DIR}/references/evaluation-and-testing.md):
  evidence design, native loading, and retained invocation results.
- [error-handling-and-recovery.md](${CLAUDE_SKILL_DIR}/references/error-handling-and-recovery.md):
  diagnosing failure boundaries and returning actionable evidence.
- [context-management.md](${CLAUDE_SKILL_DIR}/references/context-management.md):
  independent target discovery and bounded context for long work.
- [orchestration-patterns.md](${CLAUDE_SKILL_DIR}/references/orchestration-patterns.md):
  explicit dependencies between skill-requested calls.
- [debugging-agents.md](${CLAUDE_SKILL_DIR}/references/debugging-agents.md):
  inspecting native observations without changing the attempted launch.

</reference>

<failure_modes>

**Claude retained independent configuration fields.**

Claude's examples selected a model separately from its reasoning controls and omitted
controls the harness requires. A model chosen apart from its profile drifts from the
configuration owner, and a hand-assembled block leaves out whatever that owner adds.
Declare one central profile and use its complete native configuration as one unit.

**Claude prescribed a retired tool contract in invocation advice.**

Claude's handoff prescribed return fields and lifecycle tools an earlier tool version
exposed. The advice was copied from earlier guidance instead of read from the current
native tool schema. Use the invocation mechanics of the root harness instruction file
`/subagent-standards` `<invocation>` names and the current native schema, and report the
actual result.

</failure_modes>

<success_criteria>

- The definition implements the governing role and the complete selected native profile.
- The finished definition violates no rule in the `/subagent-standards` or
  `/agent-prompt-standards` rule catalog and is returned with no audit dispatched or awaited.
- The calling skill's launch instruction names the exact configured role and supplies only the target.
- The product's author command and focused deterministic checks exit zero on the returned
  definition, and every emitted definition the result names exists at its path.
- The result names the configuration path, the configured role, each emitted definition, the
  pending `/audit-subagent` run, and the pending native loading and minimal isolated execution.
- A repair returns, for each finding, the clause applied and the check that shows the class
  closed, with every same-class site and changed dependency resolved.
- A definition that already holds the requested result returns `unchanged`; an absent input
  or composed skill returns `blocked`.
- No configuration load or execution approval is claimed before its actual result exists.

</success_criteria>
