# Skill Naming

A skill's name states the artifact one invocation acts on, and the rule holds across every plugin in the marketplace. A skill that performs one step on the artifacts of one type is named `{role}-{type}`; the installed name is the only selector of a type's skills. A workflow skill outside that form names the artifact one invocation produces or judges, in the grammatical number a single invocation handles, and a reference skill is a noun phrase naming the domain it standardizes.

## Rationale

Product engineers type the skill name and reason about scope from it, so a name whose grammatical number disagrees with one invocation misstates what a single call does before the skill runs. Naming the artifact per invocation gives every plugin one decidable rule in place of per-plugin convention, and it refines the invocation-artifact decision in [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) by fixing what the `/<skill-name>` token says.

Selecting a type's skills by the name `{role}-{type}` alone leaves no registry, applicability field, or category to keep in step with the skills it describes. A reference that names no shipped skill fails at the moment a workflow follows it, so every reference resolves against the skills the marketplace ships.

## Product properties

1. A skill's name states the artifact one invocation acts on.
2. A type's skills are found by the name `{role}-{type}` alone.
3. A workflow skill outside the `{role}-{type}` form names the artifact one invocation produces or judges, in the grammatical number that invocation handles.
4. A reference skill's name is a noun phrase naming the domain it standardizes, whose number follows the domain rather than any invocation.
5. Every skill reference in authored plugin content and in the toolchain names a skill the marketplace ships.

## Verification

- ALWAYS: a skill's name states the artifact one invocation acts on, across every plugin in the marketplace
- ALWAYS: every artifact type the marketplace's skills act on has one type token, a singular kebab-case phrase naming that type, such as `skill`, `subagent`, `change`, `python-code`, or `pulumi-typescript`; a token may contain hyphens, and no word of it is a classification of its own
- ALWAYS: a skill that performs one step on the artifacts of one type is named `{role}-{type}`, where the role names the step, such as `architect`, `author`, or `audit`, and the type is the type's complete token; the type's standards skill is `{type}-standards`
- ALWAYS: the installed skill name is the only selector of a type's skills: a workflow finds the skill for a step on a type by the name `{role}-{type}`
- NEVER: a registry, applicability field, product-to-plugin assignment, or plugin category selects a type's skills
- ALWAYS: an artifact that needs the work of several types takes a type of its own, whose token names the combination, such as `pulumi-typescript`, and that type's skills compose the supporting types' skills
- ALWAYS: a skill that acts on a changeset or on the spine, such as `commit-changes`, `review-changes`, `audit-tests`, `audit-specs`, or `test`, and a standards skill that governs a class of artifacts, such as `agent-prompt-standards`, takes its name under the grammatical-number and reference-noun rules
- ALWAYS: a type whose plugin ships only some of its roles keeps its token, and each role it lacks is a capability gap, never a reason for a different name
- ALWAYS: a rename moves every reference to the old name outside the changelogs that record it and leaves no alias
- ALWAYS: a renamed skill's plugin changelog maps its old name to its new one
- ALWAYS: every skill reference in authored plugin content and in the toolchain names a skill a marketplace plugin ships, written literally, through a brace alternation whose every member a plugin ships, or through a placeholder template that at least one shipped skill name matches

### Audit

- ALWAYS: a workflow skill invocable as `/<skill-name>` names the artifact one invocation produces or judges, in the grammatical number that invocation handles ([audit])
- ALWAYS: a reference skill is named as a noun phrase naming the domain it standardizes ([audit])
- ALWAYS: a thin agent fronting a skill takes its name from the artifact that skill names ([audit])
- ALWAYS: a skill whose name misstates the scope of one invocation is renamed to match the invocation ([audit])
- NEVER: a skill's grammatical number is derived from a sibling skill's name, a directory name, or a shipped artifact rather than from the artifact one invocation acts on ([audit])
- NEVER: a skill's behavior is widened to match a name that overstates its scope ([audit])
