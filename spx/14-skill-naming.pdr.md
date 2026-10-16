# Skill Naming

A skill's name states the artifact one invocation acts on, across every plugin in the marketplace. A skill that performs one step on the artifacts of one type is named `{role}-{type}`, and its installed name is the only selector of that type's skills.

## Rationale

The installed name is the one identifier every workflow, reference and user already holds, so a name that states role and whole type finds the skill with nothing else to keep in step. A registry, applicability field or plugin category would be a second source that drifts from the shipped names.

## Product properties

1. A skill's name states its role and the complete token of its type.
2. Each skill ships under one name, with no alias.
3. The installed skill name is the only selector of a type's skills.

## Verification

### Testing

- ALWAYS: every skill reference in authored plugin content and in the toolchain names a skill a marketplace plugin ships, written literally, through a brace alternation whose every member a plugin ships, or through a placeholder template that at least one shipped skill name matches ([compliance])

### Audit

- ALWAYS: every artifact type the marketplace's skills act on has one type token, a singular kebab-case phrase naming that type, such as `skill`, `subagent`, `change`, `python-code`, or `pulumi-typescript`, which may contain hyphens ([audit])
- ALWAYS: a skill that performs one step on the artifacts of one type is named `{role}-{type}`, where the role names the step, such as `architect`, `author`, or `audit`, and the type is the type's complete token; the type's standards skill is `{type}-standards` ([audit])
- NEVER: a registry, applicability field, product-to-plugin assignment, or plugin category selects a type's skills; a workflow finds the skill for a step on a type by the name `{role}-{type}` ([audit])
- ALWAYS: an artifact that needs the work of several types takes a type of its own, whose token names the combination, such as `pulumi-typescript`, and that type's skills compose the supporting types' skills ([audit])
- ALWAYS: a skill that acts on a changeset or across the spec tree, such as `commit-changes`, `review-changes`, `audit-tests`, `audit-specs`, or `test`, and a standards skill that governs a class of artifacts, such as `agent-prompt-standards`, take their names under the rules for a workflow skill outside the `{role}-{type}` form and for a reference skill outside the `{type}-standards` form ([audit])
- NEVER: a role its plugin does not ship changes a type's token; each missing role is a capability gap ([audit])
- ALWAYS: a workflow skill outside the `{role}-{type}` form names the artifact one invocation produces or judges, in the grammatical number that invocation handles, and never derives that number from a sibling skill's name, a directory name, or a shipped artifact ([audit])
- ALWAYS: a reference skill outside the `{type}-standards` form is a noun phrase naming the domain it standardizes, whose number follows the domain rather than any invocation ([audit])
- ALWAYS: a thin agent fronting a skill takes its name from the artifact that skill names ([audit])
- ALWAYS: a skill whose name misstates its artifact or the scope of one invocation is renamed to match, the rename moves every reference outside the changelogs that record it, and the skill's behavior is never widened to match a name that overstates its scope ([audit])
- ALWAYS: a renamed skill's plugin changelog maps its old name to its new one ([audit])
