<required_reading>

Read `/skill-standards`' `references/rule-catalog.md` and `/agent-prompt-standards`' `<rule_catalog>`, then the section each finding's rule ID names.

</required_reading>

<process>

<step name="resolve_input">

Take the target skill path and the findings of the sealed audit run the request supplies. Each finding names a file, a catalog rule ID, its locations, and its evidence. A request that supplies no finding and no explicit improvement names that gap and stops before any edit.

Resolve the target to its `SKILL.md` plus every file recursively present under `references/`, `workflows/`, `templates/`, `assets/`, and `scripts/`, including uncited and orphaned bundled files.

</step>

<step name="complete_name_review">

Complete the router's `<material_change_name_review>` before applying any change.

</step>

<step name="repair_findings">

For every finding, read the section its rule ID names and repair every listed location. Then apply that rule across the complete bundle and repair every other instance of the same rule, because the next audit judges every changed file against it. Settle every operator-owned decision that changes behavior before editing.

Before changing behavior, load `${CLAUDE_SKILL_DIR}/references/test-patterns.md`. Load `${CLAUDE_SKILL_DIR}/references/reusability-patterns.md` when the repair changes variable inputs, clarification, abstraction level, or tool choice. Load `${CLAUDE_SKILL_DIR}/references/technical-patterns.md` when the repair touches files, data, external services, state mutation, or executable automation. Preserve unaffected content and keep standards in `/skill-standards` rather than copying them into the target skill.

</step>

<step name="validate">

Apply every catalog rule to each file the repair changed. Confirm every bundled citation resolves, run the target repository's canonical skill build and deterministic checks, and return the repaired bundle ready for independent verification.

</step>

</process>

<repair_anti_patterns>

| Anti-pattern          | Rejected behavior                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------ |
| Single-site repair    | Fixing the listed location while another instance of the same rule stays in the bundle     |
| Self-verification     | Dispatching `instructions:skill-auditor` or invoking `/audit-skill` from this workflow     |
| Runtime-specific path | Assuming a home-directory skill location instead of using the supplied or repository path  |
| Lexical batch rename  | Renaming unlike skill types because their names share a token, suffix, or grammatical form |
| Restated standards    | Copying `/skill-standards` rules into this workflow                                        |

</repair_anti_patterns>

<success_criteria>

- Every supplied finding and every other instance of its rule in the bundle is repaired.
- The repaired bundle passes the target repository's deterministic skill checks and returns ready for independent verification.
- Every proposed rename has a complete classification row grounded in the declared naming form, vocabulary source, and relevant history.
- `/skill-standards` remains the single rule source.

</success_criteria>
