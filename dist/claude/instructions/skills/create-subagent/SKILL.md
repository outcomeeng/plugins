---
name: create-subagent
description: >-
  ALWAYS invoke this skill when creating, editing, or configuring subagents.
  NEVER create subagents without this skill.
argument-hint: "<configuration-path-or-role>"
arguments: configuration_target
allowed-tools: Read, Glob, Write, Edit, Skill, Bash(just build-skills:*), Bash(just check-skills:*), Bash(just docs-check:*), Bash(git add:*), Bash(git commit:*)
---

Invoke the `instructions:subagent-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `instructions:skill-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A subagent definition and its calling-skill integration,
with native configuration and an independently verifiable result contract.
</objective>

<workflow>

1. Require `$configuration_target`. When it is empty, request a configuration path
   or role and stop. Read the requested target and its governing requirements. Identify the role's
   owning skill, exact configured name, destination, selected profile, and result.
   Resolve a missing product decision in the invoking conversation before dependent edits.
2. Apply `/subagent-standards` to placement, capabilities, profiles, isolation,
   invocation, and evidence. Read the relevant references from the index below.
3. For a skill-backed role, author a thin wrapper that invokes the owning skill
   and relays its result. Keep task-specific behavior in that skill.
4. For a marketplace source, declare `profile: standard`, `profile: strong`, or
   `profile: fast` according to the governing selection. Let the product build
   emit the complete native configuration. For a product-owned native definition,
   use the selected complete configuration supplied by the loaded standards and examples.
5. Update the calling skill through `instructions:create-skill` so its explicit
   launch names the configured role and supplies only the target.
6. Run the product's author command and focused deterministic checks, then preserve
   the exact definition through the product's normal checkpoint workflow.
7. Apply `/subagent-standards` `<configuration_subject>` to identify the authored input
   and exact emitted definitions, or the directly authored native definition.
   Return the requested configuration path and configured role for the owning
   verification workflow. It dispatches `instructions:subagent-auditor`
   with that path alone; the audit independently discovers the generation relationship
   and its evidence. Keep native loading and one minimal isolated execution bound to
   the emitted definition under `/subagent-standards`.

This skill's write-focused tool grant does not launch a configuration while it is
being authored. The owning verification workflow performs the post-authoring
audit and invocation check after this skill returns.

</workflow>

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

Examples selected a model separately from reasoning controls and omitted required
controls. Use the complete native profile from the configuration owner.

**Invocation advice retained a retired tool contract.**

A handoff prescribed obsolete return fields and lifecycle tools. Use the root
guide's mechanics and the current native schema; retain the actual result.

</failure_modes>

<success_criteria>

- The definition implements the governing role and the complete selected native profile.
- The calling skill names the exact configured role and minimal target.
- The built native artifact is inspectable and the authoring checks pass.
- The handoff identifies the exact artifact, role, result contract, and outstanding verification.
- No configuration load or execution approval is claimed before its actual result exists.

</success_criteria>
