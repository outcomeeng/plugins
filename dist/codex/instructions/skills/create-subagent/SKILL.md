---
name: create-subagent
description: >-
  ALWAYS invoke this skill when creating, editing, or configuring custom agents.
  NEVER create custom agents without this skill.
argument-hint: "<configuration-path-or-role>"
arguments: configuration_target
allowed-tools: Read, Glob, Write, Edit
---

Use skill `instructions:subagent-standards`.

Use skill `instructions:agent-prompt-standards`.

Use skill `instructions:skill-standards`.

<objective>
A finished custom agent definition and its calling-skill integration,
ready for independent verification, with native configuration and a declared result contract.
</objective>

<constraints>

- ALWAYS: apply every rule in the `/subagent-standards` and `/agent-prompt-standards` rule
  catalogs to the finished definition, and return it ready for independent verification once
  the product's author command and deterministic checks pass on it.
- NEVER: dispatch a custom agent auditor or wait on an audit verdict — a
  verdict on the definition comes from `/audit-subagent` run in an agent session separate from
  the one that authored it.

</constraints>

<workflow>

1. Require `$configuration_target`. When it is empty, request a configuration path
   or role and stop. Read the requested target and its governing requirements. Identify the role's
   owning skill, exact configured name, destination, selected profile, and result.
   Resolve a missing product decision in the invoking conversation before dependent edits.
2. Apply `/subagent-standards` to placement, capabilities, profiles, isolation,
   invocation, and evidence. Read the relevant references from the index below.
3. For a skill-backed role, author a thin wrapper that invokes the owning skill
   and relays its result. Keep task-specific behavior in that skill.
4. For a marketplace source, declare `profile: standard`, `profile: strong`,
   `profile: executor`, or `profile: fast` according to the governing selection. Let the product build
   emit the complete native configuration. For a product-owned native definition,
   use the selected complete configuration supplied by the loaded standards and examples.
5. Use skill `instructions:create-skill`. Update the calling skill through it so its
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

<reference>

Read only the references relevant to the role's actual work:

- [subagents.md](${SKILL_DIR}/references/subagents.md): native definitions,
  complete profile examples, capability selection, and skill-backed wrappers.
- [write-subagent-prompts.md](${SKILL_DIR}/references/write-subagent-prompts.md):
  converting a role requirement into a focused prompt and result contract.
- [evaluation-and-testing.md](${SKILL_DIR}/references/evaluation-and-testing.md):
  evidence design, native loading, and retained invocation results.
- [error-handling-and-recovery.md](${SKILL_DIR}/references/error-handling-and-recovery.md):
  diagnosing failure boundaries and returning actionable evidence.
- [context-management.md](${SKILL_DIR}/references/context-management.md):
  independent target discovery and bounded context for long work.
- [orchestration-patterns.md](${SKILL_DIR}/references/orchestration-patterns.md):
  explicit dependencies between skill-requested calls.
- [debugging-agents.md](${SKILL_DIR}/references/debugging-agents.md):
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
- No configuration load or execution approval is claimed before its actual result exists.

</success_criteria>
