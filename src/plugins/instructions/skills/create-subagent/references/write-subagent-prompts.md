<derive_the_prompt>

1. Read the role's durable requirements and the owning skill.
2. Identify the artifact one invocation produces or judges.
3. Write the smallest wrapper that reaches the skill and preserves its result.
4. For behavior with no owning skill, create that skill through `instructions:create-skill`
   before placing workflow logic in a wrapper.
5. Apply `/subagent-standards` and `/agent-prompt-standards` to the complete definition.

</derive_the_prompt>

<task_boundary>

Put the launch condition, configured role, and supplied target in the calling skill.
Put target discovery and task execution in the invoked skill. A short target such as
`HEAD` can identify a complete task when the skill defines how to resolve it.

Use the result contract to distinguish findings, an absent prerequisite, and an unusable
result. Preserve field names and required sections from the invoked skill rather than
inventing a second wrapper-level format.

</task_boundary>

<prompt_review>

Read the wrapper as a fresh session receiving only its target:

- Locate the governing skill and the definition's configuration.
- Confirm that the skill discovers the requirements it needs.
- Identify the expected result without consulting an authoring conversation.
- Trace every granted capability to the skill's actual work.
- Remove repeated workflow prose whose owner is already loaded through the skill.

Examples clarify an observed ambiguity. Add one where it resolves that ambiguity;
the root guide owns any example needed to explain native invocation mechanics.

</prompt_review>
