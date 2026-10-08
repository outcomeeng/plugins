<required_reading>

Read `${CLAUDE_SKILL_DIR}/references/test-patterns.md` before changing behavior. Read `${CLAUDE_SKILL_DIR}/references/reusability-patterns.md` when the repair changes variable inputs, clarification, abstraction level, or tool choice. Read `${CLAUDE_SKILL_DIR}/references/technical-patterns.md` when the repair touches files, data, external services, state mutation, or executable automation.

</required_reading>

<process>

<step name="resolve_target">

Use the exact skill path the request names. When it names none, ask for the exact `SKILL.md` or skill-directory path; never assume a home-directory or runtime-cache location.

Read the complete bundle: `SKILL.md` and every file under `references/`, `workflows/`, `templates/`, `assets/`, and `scripts/`, including uncited files.

</step>

<step name="inventory_repair_input">

List each item the request supplies as one row:

| Input            | Row key                                    | Locations                    |
| ---------------- | ------------------------------------------ | ---------------------------- |
| Finding          | Its `<unit>:<rule-id>` key                 | Every location it names      |
| Requested change | A short name for the requirement it states | The paths the change touches |

A finding whose rule identifier names no row in the `/skill-standards` or `/agent-prompt-standards` rule catalog cites no rule: keep its row, mark it unrepaired with that reason, and never invent the rule it implies. Settle every operator-owned decision a row raises before changing behavior.

</step>

<step name="complete_name_review">

Complete the router's `<material_change_name_review>` before applying any change.

</step>

<step name="repair">

For each finding row, repair every location it names and every other violation of the same catalog rule in the bundle, so the repair removes the defect class rather than one occurrence. Apply each requested change through the authoring rules the router loads. Preserve unaffected content, and keep every standard in its owning reference skill rather than copying it into the target.

</step>

<step name="exercise">

Invoke the repaired skill against representative input for every route, output, or failure behavior the repair touched. Confirm each selects its intended workflow, loads only its required references, and produces its declared output. Fix each observed failure before validation.

</step>

<step name="validate">

Run the target repository's canonical skill build and deterministic checks over the exercised bundle. Confirm every finding row's locations and same-rule instances are repaired, every bundled citation resolves, and the bundle violates no rule in either catalog. An edit made after validation returns to `exercise`.

</step>

<step name="return_bundle">

Return the bundle in the exact state validation passed, with one disposition per inventory row: `repaired` with the paths changed, or `unrepaired` with the reason.

</step>

</process>

<repair_anti_patterns>

| Anti-pattern         | Rejected behavior                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------------- |
| Single-site repair   | Fixing the named location while another violation of the same rule remains in the bundle             |
| Late exercise        | Editing the bundle after validation without validating the edit                                      |
| Invented rule        | Repairing toward a rule identifier no catalog carries                                                |
| Self-verdict         | Declaring the bundle approved, or judging it with an audit skill, inside this workflow               |
| Lexical batch rename | Renaming unlike skill types because their names share a token, suffix, or grammatical form           |
| Restated standards   | Copying `/skill-standards` or `/agent-prompt-standards` rules into the target skill or this workflow |

</repair_anti_patterns>

<success_criteria>

- Every inventory row carries a disposition, and every `repaired` row leaves no violation of its rule anywhere in the bundle.
- The returned bundle is the exact state that the exercise and the deterministic checks passed on.
- The bundle violates no rule in the `/skill-standards` or `/agent-prompt-standards` rule catalog.
- Every proposed rename has a complete classification row grounded in the declared naming form, vocabulary source, and relevant history.

</success_criteria>
