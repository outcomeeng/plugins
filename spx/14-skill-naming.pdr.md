# Skill Naming

A skill's name states the artifact one invocation acts on. A workflow skill invocable as `/<skill-name>` names that artifact in the grammatical number a single invocation handles; a reference skill is a noun phrase naming the domain it standardizes. The rule holds across every plugin in the marketplace.

## Rationale

Product engineers type the skill name and reason about scope from it, so a name whose grammatical number disagrees with one invocation misstates what a single call does before the skill runs. Naming the artifact per invocation gives every plugin one decidable rule in place of per-plugin convention, and it refines the invocation-artifact decision in `spx/13-plugin-and-runtime-conventions.adr.md` by fixing what the `/<skill-name>` token says.

## Product properties

1. A workflow skill's name states the artifact one invocation produces or judges, in the grammatical number that invocation handles.
2. A reference skill's name is a noun phrase naming the domain it standardizes, whose number follows the domain rather than any invocation.
3. A name that overstates one invocation's scope is a defect in the name, never a licence to widen the skill.

## Verification

- ALWAYS: a workflow skill invocable as `/<skill-name>` names the artifact one invocation produces or judges, in the grammatical number that invocation handles
- ALWAYS: a reference skill is named as a noun phrase naming the domain it standardizes
- ALWAYS: a thin agent fronting a skill takes its name from the artifact that skill names
- ALWAYS: a skill whose name misstates the scope of one invocation is renamed to match the invocation
- NEVER: a skill's grammatical number is derived from a sibling skill's name, a directory name, or a shipped artifact rather than from the artifact one invocation acts on
- NEVER: a skill's behavior is widened to match a name that overstates its scope
