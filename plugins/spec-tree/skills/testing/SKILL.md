---
name: testing
description: >-
  ALWAYS invoke this skill before writing tests or when learning the testing approach.
  NEVER write tests without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit
---

<objective>
Write tests driven by spec-tree assertions. This skill is a superset of the standalone testing methodology — it incorporates the full 5-stage router, 5 factors, and 7 exceptions, and adds spec-tree-specific concerns: assertion extraction, evidence gap analysis, test scaffold generation, and deterministic context loading from the tree.

</objective>

<quick_start>

**PREREQUISITE**: Read the methodology reference before writing any test:

- `${SKILL_DIR}/references/methodology.md` — 5-stage router, 5 factors, 7 exceptions, test double taxonomy

Then follow the spec-tree workflow below.

</quick_start>

<spec_tree_workflow>

<step name="load_context">

**Step 1: Load tree context**

Check for `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers. If absent, invoke `/understanding` and `/contextualizing` first.

This loads:

- The target spec node and its assertions
- Ancestor ADRs/PDRs that constrain the testing approach
- Lower-index sibling specs that provide context

</step>

<step name="extract_assertions">

**Step 2: Extract assertions from the spec**

Parse the target spec node. Extract all typed assertions and their test links:

| Type            | Pattern in spec                                    | Test strategy   |
| --------------- | -------------------------------------------------- | --------------- |
| **Scenario**    | `Given ... when ... then ... ([test](...))`        | Example-based   |
| **Mapping**     | `{input} maps to {output} ([test](...))`           | Parameterized   |
| **Conformance** | `{output} conforms to {standard} ([test](...))`    | Tool validation |
| **Property**    | `{invariant} holds for all {domain} ([test](...))` | Property-based  |
| **Compliance**  | `ALWAYS/NEVER: {rule} ([review]/[test](...))`      | Review or test  |

Record each assertion with:

- Assertion text
- Assertion type
- Test link (if present) — path and whether it resolves
- Test link status: exists / missing / stale

</step>

<step name="analyze_gaps">

**Step 3: Analyze evidence gaps**

For each assertion:

| Status            | Condition                               | Action                                     |
| ----------------- | --------------------------------------- | ------------------------------------------ |
| **Covered**       | Test link exists and resolves to a file | Verify in Step 4                           |
| **Missing link**  | No `([test](...))` in the assertion     | Must add test link                         |
| **Broken link**   | Link present but file doesn't exist     | Must create test file                      |
| **No assertions** | Spec has no typed assertions            | Spec needs work first — do not write tests |

Report the evidence gap summary before proceeding.

</step>

<step name="route_methodology">

**Step 4: Route each assertion through the methodology**

For each assertion that needs a test, apply the 5-stage router from `${SKILL_DIR}/references/methodology.md`:

1. **Stage 1** — What evidence does this assertion demand?
2. **Stage 2** — At what level does that evidence live? (Use 5 factors. Respect ADRs/PDRs loaded from tree context.)
3. **Stages 3–5** — If Level 1: classify the code, check real system viability, match exception if needed.

Document the routing decision for each assertion.

</step>

<step name="generate_scaffolds">

**Step 5: Generate test scaffolds**

For each assertion needing a new test:

1. Determine test pattern from assertion type (Step 2 table).
2. Determine test level from methodology routing (Step 4).
3. Create test file in the spec node's `tests/` directory.
4. Name the file using level suffix: `test_{slug}_unit.py`, `test_{slug}_integration.py`, etc.
5. Scaffold the test structure based on assertion type and language-specific patterns.

Delegate language-specific patterns to `/testing-python` or `/testing-typescript`.

**Potential nodes:** If the implementation module doesn't exist yet, test files will fail on import. This is expected — the test is a contract defining what WILL be tested. Add the node's path to `spx/POTENTIAL` and run the project's sync command so the quality gate excludes these tests. Remove the entry when implementation begins. See `${SKILL_DIR}/../understanding/references/potential-nodes.md`.

</step>

<step name="update_links">

**Step 6: Update spec assertion links**

After creating test files, update the spec to add `([test](tests/{filename}))` links for each new assertion-test pair. Every assertion must link to at least one test file.

</step>

<step name="report">

**Step 7: Report evidence summary**

Report which assertions have tests, which don't, which are stale:

```markdown
| # | Assertion | Type     | Level | Test File | Status  |
| - | --------- | -------- | ----- | --------- | ------- |
| 1 | {text}    | Scenario | 1     | {file}    | Covered |
| 2 | {text}    | Property | 1     | —         | Missing |
```

</step>

</spec_tree_workflow>

<cross_cutting_assertions>

When an assertion lives in an ancestor node (cross-cutting), determine where the test evidence should go:

- If the assertion is about behavior that a specific child node implements, the test belongs in that child's `tests/` directory.
- If the assertion spans multiple children, the test belongs in the ancestor's `tests/` directory at a higher level.
- If an ancestor accumulates too many cross-cutting assertions, flag it — the tree may need an extracted shared enabler at a lower index.

</cross_cutting_assertions>

<success_criteria>

Testing is complete when:

- [ ] Tree context loaded (foundation markers present)
- [ ] All assertions extracted from spec with types identified
- [ ] Evidence gaps analyzed and reported
- [ ] Each assertion routed through 5-stage methodology
- [ ] Test scaffolds created for missing assertions
- [ ] Spec assertion links updated to point to test files
- [ ] Evidence summary reported
- [ ] No test doubles without matching exception case (documented in comments)
- [ ] Property-based tests present for parsers, serializers, math operations, complex algorithms

</success_criteria>
