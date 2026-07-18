<required_reading>

Read `/skill-standards` and `/agent-prompt-standards`. Read `spx/local/skills.md` when the target repository provides it.

</required_reading>

<process>

<step name="classify_question">

Identify whether the request concerns structure and naming, reusable domain design, technical execution, or behavior testing. Keep this route read-only unless the operator explicitly asks to improve a skill.

</step>

<step name="load_pattern_source">

| Question class                                                  | Source                                                   |
| --------------------------------------------------------------- | -------------------------------------------------------- |
| Structure, naming, frontmatter, progressive disclosure          | `/skill-standards`                                       |
| Variable inputs, abstraction, reusable domain design            | `${CLAUDE_SKILL_DIR}/references/reusability-patterns.md` |
| Files, data, external services, mutation, executable automation | `${CLAUDE_SKILL_DIR}/references/technical-patterns.md`   |
| Activation, routing, output, failure, or fresh-context testing  | `${CLAUDE_SKILL_DIR}/references/test-patterns.md`        |

Load every source whose class applies and no unrelated reference.

</step>

<step name="explain_application">

Map the relevant rule or pattern to the operator's concrete skill shape. Distinguish governing standards from optional domain patterns, name the trade-off, and give one representative application without creating files.

</step>

</process>

<success_criteria>

- The answer cites the governing standard or conditional pattern source for each recommendation.
- Only references applicable to the question are loaded.
- The explanation maps each recommendation to the concrete skill shape and performs no mutation.

</success_criteria>
