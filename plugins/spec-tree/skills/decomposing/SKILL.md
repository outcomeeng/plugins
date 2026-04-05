---
name: decomposing
description: >-
  ALWAYS invoke this skill when breaking down, splitting, scoping, or structuring spec tree nodes.
  NEVER decompose specs without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit
---

<objective>

Decompose an existing Spec Tree node into child nodes when it contains multiple independent concerns. Determines enabler vs outcome for each child, applies sparse integer ordering, redistributes assertions, and validates decomposition quality.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `/understanding` first.

Read the reference material from the understanding skill (`${CLAUDE_SKILL_DIR}/../understanding/`) before decomposing:

- `${CLAUDE_SKILL_DIR}/../understanding/references/decomposition-semantics.md` — when to decompose, enabler vs outcome, depth, shared enabler extraction
- `${CLAUDE_SKILL_DIR}/../understanding/references/ordering-rules.md` — sparse integer ordering, insertion, fractional indexing
- `${CLAUDE_SKILL_DIR}/../understanding/references/node-types.md` — enabler and outcome structure, directory layout

Then follow the workflow below.

</quick_start>

<workflow>

<step name="load_context">

**Step 1: Load tree context**

Check for `<SPEC_TREE_CONTEXT>` marker matching the target node. If absent, invoke `/contextualizing`.

Read the target node's spec file. Note:

- Current hypothesis (outcome) or enables statement (enabler)
- All assertions, grouped by type (scenario, mapping, conformance, property, compliance)
- Total assertion count
- Any existing child nodes

</step>

<step name="assess_need">

**Step 2: Assess whether decomposition is needed**

Apply the triggers from `decomposition-semantics.md`:

| Trigger              | Threshold                                              |
| -------------------- | ------------------------------------------------------ |
| Assertion count      | More than ~7 across all types                          |
| Context payload      | Exceeds an agent's reliable working set                |
| Independent concerns | Contains assertions with no relationship to each other |
| Separate validation  | Parts could be validated independently                 |

**Do NOT decompose if:**

- A single coherent hypothesis covers all assertions
- Assertions are tightly coupled and meaningless in isolation
- Decomposition would create children with only 1–2 trivial assertions

If decomposition is not warranted, say so and stop. Do not force structure.

</step>

<step name="identify_concerns">

**Step 3: Identify independent concerns**

This is the creative step. Read through the assertions and group them by concern — a concern is a coherent set of assertions that:

- Share a common subject (the same subsystem, behavior, or capability)
- Would be validated together
- Would be meaningless if split further

For each group, draft a one-line summary of what that concern is about.

**Seam-finding heuristics:**

- Assertions about different data types or domains → separate concerns
- Assertions about different user-facing behaviors → separate concerns
- Assertions about setup/infrastructure vs behavior → enabler vs outcome
- Assertions that could fail independently → separate concerns
- Assertions connected by "and" in the parent hypothesis → candidate split points

Present the concern groupings to the user before proceeding.

</step>

<step name="extract_enablers">

**Step 4: Extract shared enablers**

Before assigning outcome nodes, check: do any concern groups share infrastructure?

Per `decomposition-semantics.md` → `shared_enabler_extraction`:

- Two or more groups share a dependency → extract as enabler
- The shared piece is infrastructure, not user-facing value
- Removing it would break multiple siblings

Enablers get **lower indices** than the outcomes that depend on them.

</step>

<step name="assign_types">

**Step 5: Assign node types**

For each concern group, apply the decision table from `decomposition-semantics.md`:

| Question                                                             | If yes  |
| -------------------------------------------------------------------- | ------- |
| Does it deliver user-facing value (directly or indirectly)?          | Outcome |
| Does it exist only to serve other nodes?                             | Enabler |
| Would you remove it if all its dependents were retired?              | Enabler |
| Can you express a three-part hypothesis (output → outcome → impact)? | Outcome |

When unclear, default to **outcome**.

</step>

<step name="assign_indices">

**Step 6: Assign sparse integer indices**

Apply ordering rules from `ordering-rules.md`:

1. Count the total number of children (N).
2. Apply the distribution formula: `i_k = 10 + floor(k * 89 / (N + 1))`
3. Enablers that other nodes depend on get lower indices.
4. Independent outcomes can share the same index.
5. A node that depends on another gets a higher index.

**Dependency encoding:**

- Lower index constrains higher index (and its descendants)
- Same index = independent of each other
- ADRs/PDRs at lower indices constrain all higher siblings

</step>

<step name="redistribute_assertions">

**Step 7: Redistribute assertions**

Move assertions from the parent spec into the correct child nodes:

- Each assertion goes to the child whose concern it belongs to
- **Cross-cutting assertions stay in the parent** — these span multiple children
- If an assertion could go in either of two children, it's probably cross-cutting

Per `decomposition-semantics.md` → `cross_cutting_assertions`: if the parent accumulates too many cross-cutting assertions, extract a shared enabler at a lower index.

Update test links in assertions to reflect the new `tests/` location in each child.

</step>

<step name="write_specs">

**Step 8: Write child specs**

For each child node:

1. Create the directory: `{index}-{slug}.{enabler|outcome}/`
2. Create the spec file: `{slug}.md`
3. Create the `tests/` directory
4. Write the spec content:

**For outcomes:** Use the outcome template from `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/outcome-name.md`. Write the three-part hypothesis:

- **Output** — what the software does (tested by assertions)
- **Outcome** — measurable change in user behavior
- **Impact** — business value

**For enablers:** Use the enabler template from `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/enabler-name.md`. Write the enables statement.

5. Add assertions redistributed from the parent.

**Revise the parent spec:** The parent's hypothesis may need to become a summary of its children. Remove assertions that moved to children. Keep only cross-cutting assertions.

</step>

<step name="validate">

**Step 9: Validate decomposition quality**

Check each criterion:

- [ ] No child has only 1–2 trivial assertions (too granular)
- [ ] No child exceeds ~7 assertions (recursive decomposition signal)
- [ ] Every enabler has at least two dependents (not orphaned)
- [ ] Cross-cutting assertions in parent are minimal
- [ ] Children collectively cover the parent's scope (nothing lost)
- [ ] Enablers have lower indices than their dependents
- [ ] Independent nodes share the same index or have no ordering relationship
- [ ] Spec files use atemporal voice (no temporal language)
- [ ] Directory names follow `{NN}-{slug}.{enabler|outcome}` convention
- [ ] Spec files are `{slug}.md` (no type suffix, no numeric prefix)

If a child exceeds ~7 assertions, flag it for recursive decomposition — but do not decompose recursively in the same invocation without user confirmation.

</step>

</workflow>

<failure_modes>

**Failure 1: Over-decomposed a coherent node**

Agent decomposed an outcome with 5 tightly coupled assertions into 3 children. Each child ended up with 1–2 assertions that made no sense in isolation. The assertions were about phases of a single user workflow (initiate → process → confirm) and could only be validated together. The decomposition created structure without value.

How to avoid: Before decomposing, ask: "Can any of these children be validated independently?" If the answer is no — if testing one child requires setting up the others — the node is cohesive and should stay whole.

**Failure 2: Lost assertions during redistribution**

Agent moved 8 assertions from a parent into 3 children but only accounted for 7. One cross-cutting assertion about error handling spanned multiple children and was dropped because it didn't cleanly fit any single child. The parent spec was rewritten without it.

How to avoid: Before writing child specs, count the parent's assertions. After writing all children, count the total across children plus remaining parent assertions. These counts must match. Assertions that don't fit a single child are cross-cutting — they stay in the parent.

**Failure 3: Created enabler with single dependent**

Agent extracted a "database schema" enabler that only one sibling depended on. This violated the 2+ dependent rule and created unnecessary indirection — an extra node, an extra spec file, an extra directory, all wrapping what should have been internal to the outcome.

How to avoid: Before extracting an enabler, enumerate which siblings depend on it. If the count is 1, the infrastructure belongs inside that outcome, not as a separate enabler.

**Failure 4: Temporal language in child specs inherited from parent**

Agent decomposed a parent whose hypothesis read: "We believe that improving the search experience will increase conversion." The child specs inherited temporal fragments: "Improves the search experience by adding filters" (narrates an improvement journey). The atemporal version: "Search results support filtering by date, type, and status."

How to avoid: Decomposition is an opportunity to fix temporal language, not propagate it. When redistributing content from parent to children, apply the read-aloud test to every sentence in every child spec.

**Failure 5: Decomposed by implementation layer**

Agent split an outcome into "frontend," "backend," and "database" children. These are implementation layers, not independent concerns. The frontend child's assertions couldn't be validated without the backend, and vice versa. Users don't care about layers — they care about behaviors.

How to avoid: Name each candidate child by the user-facing behavior it delivers, not by the technical component. If you can't describe what user value a child delivers without referencing another child, the split is wrong.

</failure_modes>

<anti_patterns>

**Decomposing by implementation layer.** Don't create children like "frontend," "backend," "database." Decompose by user-facing concern or shared infrastructure.

**Forcing three levels.** The old capability/feature/story hierarchy is gone. Depth emerges from actual complexity. A node with 4 clear assertions doesn't need children.

**Creating enablers for everything.** Enablers exist only when two or more siblings share a dependency. A single-use piece of infrastructure is not an enabler — it belongs inside the outcome that uses it.

**Losing assertions during redistribution.** Every parent assertion must end up in exactly one child or remain as a cross-cutting assertion in the parent. Diff the before/after to verify.

**Renumbering siblings.** When decomposing one node, do not renumber its siblings. The parent's index stays the same; only its internal structure changes.

</anti_patterns>

<success_criteria>

Decomposition is complete when:

- [ ] Decomposition need assessed (not forced)
- [ ] Concerns identified and presented to user
- [ ] Enablers extracted where shared infrastructure exists
- [ ] Each child has correct node type (enabler or outcome)
- [ ] Sparse integer indices assigned following ordering rules
- [ ] All assertions redistributed (none lost, cross-cutting in parent)
- [ ] Child specs written using templates from `${CLAUDE_SKILL_DIR}/../understanding/templates/`
- [ ] Parent spec revised to reflect decomposition
- [ ] Validation checklist passes

</success_criteria>
