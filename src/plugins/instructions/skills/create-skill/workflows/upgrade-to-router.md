<required_reading>

Read `/skill-standards`'s `references/runtime-variables.md`. Read `${CLAUDE_SKILL_DIR}/references/reusability-patterns.md`, `${CLAUDE_SKILL_DIR}/references/test-patterns.md`, and `${CLAUDE_SKILL_DIR}/templates/router-skill.md` before rewriting the target.

</required_reading>

<process>

<step name="resolve_target">

Use the exact skill path supplied by the operator or established from the repository's authored layout. Read the complete skill bundle and record its current line count, user intents, common principles, route-specific procedures, references, and bundled assets. Never assume a user-home or runtime-cache destination.

</step>

<step name="prove_router_shape">

Convert only when the skill has distinct user intents, conditional workflows, or a cohesive overview whose route-specific detail exceeds the progressive-disclosure boundary. Preserve a simple skill when one workflow remains the clearest shape.

</step>

<step name="design_routes">

Map every existing behavior to exactly one destination:

| Content                                | Destination               |
| -------------------------------------- | ------------------------- |
| Output target and universal principles | Router `SKILL.md`         |
| Intent-specific procedure              | `workflows/{intent}.md`   |
| Conditional domain knowledge           | `references/{subject}.md` |
| Reusable output material               | `assets/` or `templates/` |

Identify duplicated, obsolete, and orphaned content before mutation.

</step>

<step name="rewrite_bundle">

Rewrite the bundle from `${CLAUDE_SKILL_DIR}/templates/router-skill.md` by applying `/skill-standards`'s router, workflow-file, XML, and bundled-path rules. Keep common principles in `SKILL.md` and route-specific procedure in the workflow that consumes it.

</step>

<step name="validate_equivalence">

Map every preserved behavior from the pre-upgrade inventory to its new location. Confirm no route, constraint, reference, or asset disappeared; remove only content proven duplicated or obsolete. Build the bundle with the target repository's canonical skill build — or, where the harness loads authored source unrendered, use the authored bundle directly. Exercise it in a context that loads the built skill rather than the files this session edited. Exercise every route plus one ambiguous input against it and fix each observed failure, then run repository checks and confirm the bundle violates no rule in the `/skill-standards` or `/agent-prompt-standards` rule catalog. An edit made after these checks repeats this step.

</step>

</process>

<success_criteria>

- The router conversion is justified by distinct intents or conditional detail.
- Every preserved behavior has one destination, with no duplication or orphaned bundled file.
- Every route resolves through an exact bundled path and produces its declared output.
- Repository checks pass and the bundle violates no catalog rule, on the exact state the exercise passed on.

</success_criteria>
