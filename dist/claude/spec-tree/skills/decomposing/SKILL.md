---
name: decomposing
description: ALWAYS invoke this skill when breaking down, splitting, scoping, composing, or structuring spec tree nodes. NEVER decompose specs without this skill.
argument-hint: <node-address|spx/>
allowed-tools: Read, Glob, Grep, Write, Edit
---

<objective>

Compose Spec Tree structure from a target node address, durable spec content, and node-local coordination notes. Handles top-level product-root composition (`spx/`) and child decomposition for existing nodes. Determines whether source material is complete, identifies concern boundaries, assigns enabler/outcome types, records ordering evidence, assigns sparse indices, redistributes assertions, and validates structural quality.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `/understanding` first.

Accept exactly one target:

- `spx/` — compose top-level children from the product root after bootstrapping creates the product spec and root guide.
- `{path-to-node}` — decompose or restructure children under an existing node.

Read before composing:

- `${CLAUDE_SKILL_DIR}/../understanding/references/node-types.md` — enabler/outcome structure and nesting rules
- `${CLAUDE_SKILL_DIR}/../understanding/references/what-goes-where.md` — artifact content taxonomy and the mandatory test-infrastructure tree shape (`<test_infrastructure>`)
- `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/enabler-name.md`
- `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/outcome-name.md`
- `/interviewing` — questioning methodology when the clarity gate finds incomplete or ambiguous composition input

</quick_start>

<workflow>

<step name="load_context">

**Step 1: Load tree context**

If the target is `spx/`:

1. Read the product spec and product-level ADRs/PDRs.
2. Read `spx/CLAUDE.md` if present.
3. Read `spx/PLAN.md` and `spx/ISSUES.md` if present.
4. Enumerate existing top-level children.
5. The test-infrastructure baseline is mandatory, not discretionary. Per `what-goes-where.md` `<test_infrastructure>`, every tree has a top-level enabler with slug `infrastructure`, an enabler child with slug `testing`, and grandchildren `generators`, `fixtures`, `harnesses`. Compose this baseline when it is absent; use the normative slugs exactly — do not invent alternatives such as `test-infrastructure` or `test-support`.

If the target is a node address:

1. Accept only the target node address as structural input. The address must be the full path from `spx/`; never accept a bare node name or numeric prefix as sufficient.
2. If the request includes proposed child names, indices, or dependency order, preserve those details as intent in the target node's `PLAN.md` or `ISSUES.md`; do not treat them as structure.
3. Check for a matching `<SPEC_TREE_CONTEXT>` marker. If absent, invoke `/contextualizing`.
4. Read the context manifest, target spec, existing children, and target `PLAN.md` or `ISSUES.md`.

For both target modes, note root product scope, ancestor constraints, current assertions, existing siblings/children, and any known issues before proposing structure.

</step>

<step name="assess_need">

**Step 2: Assess whether composition is needed**

For `spx/`, composition is needed when the product spec or root coordination notes name product scope that has no top-level children yet.

For a node target, decompose when at least one trigger applies:

| Trigger              | Threshold                                              |
| -------------------- | ------------------------------------------------------ |
| Assertion count      | More than ~7 across all types                          |
| Context payload      | Exceeds a reliable working set                         |
| Independent concerns | Contains assertions with no relationship to each other |
| Separate validation  | Parts could be validated independently                 |
| Explicit issue       | `PLAN.md` or `ISSUES.md` requests structure work       |

Do not decompose when a single coherent hypothesis or enables statement covers all assertions, assertions are tightly coupled and meaningless in isolation, or decomposition would create children with only 1-2 trivial assertions.

</step>

<step name="clarity_gate">

**Step 3: Verify composition input completeness**

Before proposing child nodes, verify that product/root context, target spec, existing children/siblings, `PLAN.md`, and `ISSUES.md` are complete enough to build the structure model.

Use this coverage map:

```text
Coverage: Scope Boundary | Delivery Substrate | Evidence Strategy | Architecture | Enabler/Outcome Type | Ordering Evidence | Index Budget | Refactor/Issue Handling
```

Each area is complete when:

- **Scope Boundary** — included and excluded concerns are named, and the aggregate concern stays coherent.
- **Delivery Substrate** — infrastructure, runtime APIs, data sources, packaging, commands, validation surfaces, and safety boundaries needed to deliver the behavior are named or explicitly deferred.
- **Evidence Strategy** — each concern has a verification type: automated test, review, validation command, workflow behavior, or a documented reason evidence stays deferred.
- **Architecture** — architectural choices that govern the structure are captured by ADRs or an explicit open issue.
- **Enabler/Outcome Type** — each candidate can be written as a stable enabler or has genuine outcome uncertainty.
- **Ordering Evidence** — ordered candidates have a concrete reason one must precede another, or the candidates are unordered relative to each other.
- **Index Budget** — full-vs-partial composition horizon is known.
- **Refactor/Issue Handling** — sibling refactors, duplicate nodes, stale coordination notes, and known issues have a destination.

If any area is incomplete or doubtful, invoke `/interviewing` before continuing. Use the coverage map above as the calling skill's domain-specific coverage areas. Ask one structured question at a time and continue until every area is resolved or recorded as an explicit issue.

</step>

<step name="identify_concerns">

**Step 4: Identify concerns**

Group assertions, product scope items, and coordination-note intent into coherent concerns. A concern is a set of behavior, infrastructure, or policy that:

- Shares a common subject
- Would be validated together
- Would be meaningful as a stable child node
- Would not be clearer as a single assertion inside another child

Use these seam-finding heuristics:

- Different data domains, runtime surfaces, commands, or validation mechanisms can indicate separate concerns.
- Setup, packaging, state, credentials, safety, or workflow substrate can indicate enabler concerns.
- Behavior slices can be valid vertical slices when each slice has its own testable contract and later slices extend or depend on earlier contracts.
- Implementation layers alone are not concerns unless the user-visible or spec-visible contract can be validated independently.
- Assertions that span multiple children stay in the parent as cross-cutting assertions.

Present concern groupings to the user before writing files.

</step>

<step name="assign_types">

**Step 5: Assign node types**

Apply these rules to each concern:

| Condition                                                                                    | Node type |
| -------------------------------------------------------------------------------------------- | --------- |
| Parent is an enabler and the child is a node                                                 | Enabler   |
| Output is fully determined by specification and assertions grow by addition                  | Enabler   |
| Concern exists to provide runtime, data, validation, workflow, packaging, state, or safety   | Enabler   |
| Goal is a behavior-change bet and most assertions could change while the goal remains stable | Outcome   |
| Child carries its own genuine uncertainty about which output achieves the desired behavior   | Outcome   |

Use an outcome only when the forcing question fails: "Can this be written as PROVIDES X SO THAT Y CAN Z with stable assertions?" If yes, make it an enabler. When unclear after the clarity gate and interview, default to enabler.

</step>

<step name="extract_shared_enablers">

**Step 6: Extract shared enablers**

Before assigning indices, check whether two or more proposed children require the same substrate:

- Runtime API, data source, generated artifact, persisted state, or packaging surface
- Validation rule, command surface, safety boundary, credential model, or evidence harness
- Shared policy or invariant needed by multiple children

Extract the shared concern as an enabler when removing it would break multiple children. Keep single-consumer infrastructure inside the consuming child.

</step>

<step name="ordering_evidence">

**Step 7: Build the ordering-evidence matrix**

Before assigning indices, record every proposed ordering edge:

| Field                     | Required content                                                                                                 |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Predecessor               | Candidate child or decision that must be earlier                                                                 |
| Ordering basis            | Provider/consumer, logical prerequisite, vertical slice, shared substrate, feature extension, ADR/PDR constraint |
| Constraining contribution | Concrete service, contract, invariant, state, artifact, validation surface, or delivered slice                   |
| Successor                 | Candidate child constrained by the predecessor                                                                   |
| Required by               | Successor assertion, workflow step, verification type, architecture invariant, or extension goal                 |
| Consequence if absent     | What becomes impossible, invalid, unverifiable, or incoherent without the predecessor                            |
| Disposition               | Ordered dependency, same-index/unordered, or open issue                                                          |

Use different sibling indices only when the matrix contains concrete ordering evidence. Valid evidence includes provider/consumer service flow, logical prerequisites, vertical-slice construction dependencies, shared substrate, and feature-extension dependencies.

Roadmap priority, chronology, theme grouping, and explanation order do not create ordering evidence by themselves.

Use full paths from `spx/` for existing nodes, ADRs, and PDRs in the matrix. For new candidate children before the final index exists, include the full parent path plus candidate slug so the reference can be resolved after assignment.

</step>

<step name="assign_indices">

**Step 8: Assign sparse integer indices**

Use sparse indices to encode the ordering-evidence matrix:

1. Choose the horizon:
   - Full composition of all known child concerns → use the full [10, 99] range.
   - First slice of a larger known area → use the first half or first quarter and record the reserved horizon in `PLAN.md`.
2. Count child nodes in the chosen horizon.
3. Distribute ordered groups with `i_k = 10 + floor(k * 89 / (N + 1))`, adjusted to the selected horizon.
4. Assign a higher index only when the ordering-evidence matrix proves the predecessor constrains the successor.
5. Assign the same index, or leave siblings unordered relative to each other, when no ordering evidence exists.

Files and directories share one numeric namespace within a parent. Numeric prefixes are sibling-unique only; always use full paths from `spx/` in references. Never refer to an ADR or PDR by bare filename because any directory can contain the same numeric prefix and slug.

</step>

<step name="redistribute_assertions">

**Step 9: Redistribute assertions**

For node targets, move assertions from the parent spec into children:

- Each assertion goes to the child whose concern it specifies.
- Cross-cutting assertions stay in the parent.
- Assertions that fit two children are probably cross-cutting.
- Test links move with their assertions and must point to the correct child `tests/` location.

Count assertions before and after redistribution. The child assertions plus remaining parent assertions must equal the original assertion count.

For `spx/`, write top-level children from product scope and root coordination-note intent. Product-level assertions stay in the product spec unless they specify only one child concern.

</step>

<step name="write_specs">

**Step 10: Write child specs**

For each child node:

1. Create `{index}-{slug}.{enabler|outcome}/`.
2. Create `{slug}.md`.
3. Use the enabler or outcome template from `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/`.
4. Add redistributed assertions or placeholder review assertions only when the child is intentionally declared without test evidence yet.

Do not create an empty `tests/` directory at composition — a node has no tests yet, git does not track empty directories, and the `tests/` directory materializes when `/testing` or `/applying` writes the first test file.

Revise the parent spec so it summarizes the child structure without narrating the refactor. Remove moved assertions and keep cross-cutting assertions.

</step>

<step name="validate">

**Step 11: Validate composition quality**

Check each criterion:

- [ ] Composition need assessed and not forced
- [ ] Clarity gate complete, or `/interviewing` used to resolve gaps
- [ ] Delivery substrate and evidence strategy accounted for
- [ ] Concern groupings presented before writing files
- [ ] No child has only 1-2 trivial assertions
- [ ] No child exceeds ~7 assertions without a recursive-decomposition issue
- [ ] Shared enablers have at least two dependent children
- [ ] Ordering-evidence matrix recorded before index assignment
- [ ] Every different-index sibling relationship has ordering evidence
- [ ] Roadmap, chronology, theme grouping, and explanation order are not encoded as dependencies by themselves
- [ ] Index horizon selected; partial compositions reserve remaining space in `PLAN.md`
- [ ] Children collectively cover the parent or product scope
- [ ] Assertions are not lost during redistribution
- [ ] Spec files use atemporal voice
- [ ] Directory names follow `{NN}-{slug}.{enabler|outcome}`
- [ ] Spec files are `{slug}.md`
- [ ] Every node, ADR, and PDR reference uses a full path from `spx/`

</step>

</workflow>

<failure_modes>

**Failure 1: Over-decomposed a coherent node**

Claude decomposed an outcome with tightly coupled assertions into children that could not be validated independently. The child specs looked tidy but each one required the others to mean anything.

How to avoid: Before decomposing, ask whether each child can be validated on its own contract. If every test requires all proposed children, keep the node whole.

**Failure 2: Encoded roadmap order as dependency order**

Claude converted a roadmap list into sequential sparse indices. The order felt natural to explain, but no later child depended on an earlier contract, substrate, or slice.

How to avoid: Record ordering evidence before assigning indices. If the only reason is priority, chronology, theme, or explanation order, keep the siblings same-index or unordered.

**Failure 3: Missed vertical-slice construction**

Claude flattened two slices into same-index siblings because there was no provider/consumer service. The second slice extended the first slice's command contract and test harness, so context loading later missed the prerequisite slice.

How to avoid: Treat vertical-slice construction and feature-extension prerequisites as ordering evidence when the successor depends on a predecessor's delivered contract.

**Failure 4: Created enabler with one dependent**

Claude extracted a helper as a shared enabler even though only one child consumed it. The new node added indirection without shared structure.

How to avoid: Extract an enabler only when two or more children depend on it. Keep single-consumer infrastructure inside the consuming child.

**Failure 5: Lost assertions during redistribution**

Claude moved parent assertions into children and dropped one cross-cutting assertion because it fit no single child.

How to avoid: Count assertions before and after. Assertions that span children remain in the parent.

**Failure 6: Wrote bare node or decision references**

Claude wrote `32-parser.enabler` or `15-build.adr.md` in a decomposition plan. Another directory used the same numeric prefix, so the reference could not be resolved. Full paths from `spx/` are mandatory for every existing node, ADR, and PDR.

How to avoid: When recording an ordering-evidence matrix, assertion move, issue, or PLAN.md note, write `spx/.../32-parser.enabler` and `spx/.../15-build.adr.md`. Before a new child has a final index, write the full parent path and candidate slug.

</failure_modes>

<anti_patterns>

**Pre-shaped child lists.** User-provided child names or indices are intent, not structure. Build the model from the target spec and coordination notes.

**Implementation-layer decomposition.** Children named only "frontend," "backend," or "database" are usually layers, not independently validated concerns.

**Outcome inflation.** Use outcomes only for genuine uncertainty. Stable, specified outputs are enablers even when users see them.

**Narrative ordering.** A list that is easy to explain in order is not automatically a dependency chain.

**Skipping product-root composition.** Bootstrapping creates the product root; `/decomposing spx/` composes top-level children.

**Bare references.** A node name, ADR filename, PDR filename, or numeric prefix without the full `spx/` path is not a reference. It is an ambiguous label.

</anti_patterns>

<success_criteria>

Decomposition is complete when:

- [ ] Target is either `spx/` or a valid node address
- [ ] Context loaded from product/root, target spec if any, existing tree, and coordination notes
- [ ] Composition need assessed
- [ ] Clarity gate completed or `/interviewing` used
- [ ] Concern boundaries and node types assigned
- [ ] Shared enablers extracted only for multi-child dependencies
- [ ] Ordering-evidence matrix recorded
- [ ] Sparse indices assigned from ordering evidence and selected horizon
- [ ] Assertions redistributed without loss
- [ ] Parent or product spec revised without temporal narration
- [ ] Child specs written from templates
- [ ] Full `spx/` paths used for every node, ADR, and PDR reference
- [ ] Validation checklist passes

</success_criteria>
