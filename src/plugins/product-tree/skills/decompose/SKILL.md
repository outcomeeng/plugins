---
name: decompose
description: ALWAYS invoke this skill when breaking down, splitting, scoping, composing, or structuring Product Tree nodes. NEVER decompose specs without this skill.
argument-hint: <node-address|spx/>
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(spx validation markdown:*), Bash(spx spec status:*), {{! tool('use_skill') !}}
---

<objective>

Product Tree structure under a target node address, composed from durable spec content and node-local coordination notes.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<PRODUCT_TREE_FOUNDATION>` marker. If absent, use skill `product-tree:understand` first.

**Target:** `$ARGUMENTS`

Accept exactly one target from `$ARGUMENTS`:

- `spx/` — compose top-level children from the product root after bootstrapping creates the product document and root guide.
- `{path-to-node}` — decompose or restructure children under an existing node.

If `$ARGUMENTS` is empty, stop before reading or writing product files. State that this skill requires exactly one target and give the two accepted forms above.

If `$ARGUMENTS` carries anything beside the target, stop before reading or writing product files. The target is this skill's only input; every index is its output.

Read the conditional operational sources below before composing. Use the live inline foundation for node and ordering rules:

- Live `/understand` `<identity_and_kinds>` — the seven kinds, their order, and containment — and the `kind-decision.md` reference that section names for the ordered kind tests and the structural scorecards
- Live `/understand` `<ordering_model>` — the context-loading meaning of an index and the inverse assignment rule
- Live `/understand` `<artifact_placement>` — artifact taxonomy, test-infrastructure governance, and placement rules
- `/understand` product-domain-shapes classifier and examples
- `/understand` output-kind and variant spec templates under `templates/nodes/`
- `/interview` — questioning methodology when the clarity gate finds incomplete or ambiguous composition input

</quick_start>

<workflow>

<step name="load_context">

**Step 1: Load tree context**

A live `<PRODUCT_TREE_CONTEXT target="...">` marker whose target is exactly `$ARGUMENTS` — `spx/` or the full node path — is this step's input. When the live conversation carries none, use skill `product-tree:contextualize` with that target before any other read; a marker for another target, or one quoted from a compaction summary, is none.

Read from the manifest the marker carries:

1. The product document and every product-level ADR and PDR.
2. `{{! file('root_guide') !}}` when present.
3. `spx/ISSUES.md` when present, and a prior-form `spx/PLAN.md` a 3.x-authored tree still carries.
4. For a node target, the target spec, its decision records, its coordination notes, and its existing children.
5. The existing siblings at the target level — for `spx/`, the top-level nodes — with the index each carries.

Test infrastructure is mandatory to govern when it exists, but its spec placement follows normal composition. Per `/understand` `references/artifact-placement.md` `<test_artifact_boundaries>`, harnesses, generators, and fixtures are infrastructure governed by naturally placed spec nodes. Compose an `infrastructure`, `test`, `generators`, `fixtures`, or `harnesses` node only when product/root context or coordination notes identify that concern as a real product boundary. Never fabricate a top-level category subtree solely because test infrastructure exists, and never invent anti-term categories such as `test-support`.

Note root product scope, ancestor constraints, current assertions, existing siblings and children, and any known issues before proposing structure.

</step>

<step name="assess_need">

**Step 2: Assess whether composition is needed**

For `spx/`, composition is needed when the product document or root coordination notes name product scope that has no top-level children yet.

For a node target, decompose when at least one trigger applies:

| Trigger              | Threshold                                                     |
| -------------------- | ------------------------------------------------------------- |
| Assertion count      | More than ~7 across all types                                 |
| Context payload      | Exceeds a reliable working set                                |
| Independent concerns | Contains assertions with no relationship to each other        |
| Separate validation  | Parts could be validated independently                        |
| Explicit issue       | `ISSUES.md` or a prior-form `PLAN.md` requests structure work |
| Placement            | A node needs an index among the target's children             |

Placement holds for either target form: a node needs an index among the target's children, whether it is moved under the target or new. A placement run takes Step 3 for the Kind, Ordering Evidence, and Index Budget areas, skips Steps 4, 6, and 9, writes the Step 7 rows for the candidate and the target's children, and reads the candidate's index from the matrix in Step 8. A new candidate takes its kind in Step 5 and its directory in Step 10. A candidate that exists elsewhere in the tree keeps its kind and goes from Step 8 to Step 11; Step 10 creates no directory or spec for it, because it keeps its own directory when it moves.

Classify the target with the product-domain-shapes reference before deciding whether to split it:

- **One coherent concern**: keep the target whole when one hypothesis or enables statement covers all assertions, assertions are tightly coupled, or proposed children would carry only 1-2 trivial assertions.
- **Aggregate domain plus first concrete behavior**: create both parent and child from the first slice when the aggregate owns shared policy, vocabulary, scope, routing, coordination, or cross-child assertions and the concrete behavior owns an independently validated contract.
- **Implementation layer**: translate code-shaped names back to product dimensions before proposing nodes.
- **Unsettled boundary**: use skill `product-tree:interview` with the unresolved boundary as the current coverage area.

</step>

<step name="clarity_gate">

**Step 3: Verify composition input completeness**

Before proposing child nodes, verify that product/root context, target spec, existing children/siblings, `ISSUES.md`, and a prior-form `PLAN.md` are complete enough to build the structure model.

Use this coverage map:

```text
Coverage: Scope Boundary | Decision Placement | Delivery Substrate | Evidence Strategy | Architecture | Kind | Ordering Evidence | Index Budget | Refactor/Issue Handling
```

Each area is complete when:

- **Scope Boundary** — included and excluded concerns are named, and the aggregate concern stays coherent.
- **Decision Placement** — requested ADR/PDR locations are resolved to an owning directory when placement depends on concept ownership, stale node naming, node splitting, parent/child boundaries, or context-loading reach.
- **Delivery Substrate** — infrastructure, runtime APIs, data sources, packaging, commands, validation surfaces, and safety boundaries needed to deliver the behavior are named or explicitly deferred.
- **Evidence Strategy** — each concern has a verification type: automated test, review, validation command, workflow behavior, or a documented reason evidence stays deferred.
- **Architecture** — architectural choices that govern the structure are captured by ADRs or an explicit open issue.
- **Kind** — Step 5 can fix each candidate's kind in the form the tree carries.
- **Ordering Evidence** — ordered candidates have a concrete reason one must precede another, or the candidates are unordered relative to each other.
- **Index Budget** — full-vs-partial composition horizon is known.
- **Refactor/Issue Handling** — sibling refactors, duplicate nodes, stale coordination notes, and known issues have a destination.

If any area is incomplete or doubtful, use skill `product-tree:interview` before continuing. Use the coverage map above as the calling skill's domain-specific coverage areas. Ask one structured question at a time and continue until every area is resolved or recorded as an explicit issue.

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
- Setup, packaging, state, credentials, safety, or workflow substrate can indicate provider concerns.
- Behavior slices can be valid vertical slices when each slice has its own testable contract and later slices extend or depend on earlier contracts.
- Apply the product-domain-shapes reference when the input mixes an aggregate domain with its first concrete behavior.
- Implementation layers alone are not concerns unless the user-visible or spec-visible contract can be validated independently.
- Assertions that span multiple children stay in the parent as cross-cutting assertions.

When later sibling slices are named, implied by the product vocabulary, or recorded as reserved horizon, keep the aggregate as the parent boundary and place the concrete behavior in a child. Keep cross-slice assertions on the parent and child-specific assertions on the child. Record the deferred siblings and the reserved horizon as a Proposed Change. Use skill `product-tree:author-change`.

Present concern groupings to the user before writing files.

</step>

<step name="assign_types">

**Step 5: Assign node kinds**

The tree's form is the one its existing nodes carry; a tree with no node yet takes the form the `methodology.version` in `spx.config.yaml` declares.

In a tree that carries the kind suffixes, classify each concern by the ordered kind procedure of the live `/understand` `<identity_and_kinds>` and the `kind-decision.md` tests it names — product, variant, substrate, surface, interface, domain, capability — where the first test that holds fixes the kind. The target admits the kind under the containment that section states, or the concern belongs under another parent.

In a tree authored under a 3.x version, which carries `.enabler` and `.outcome` directories, apply these rules to each concern:

| Condition                                                                                    | Node type |
| -------------------------------------------------------------------------------------------- | --------- |
| Parent is an enabler and the child is a node                                                 | Enabler   |
| Output is fully determined by specification and assertions grow by addition                  | Enabler   |
| Concern exists to provide runtime, data, validation, workflow, packaging, state, or safety   | Enabler   |
| Goal is a behavior-change bet and most assertions could change while the goal remains stable | Outcome   |
| Child carries its own real uncertainty about which output achieves the desired behavior      | Outcome   |

Use an outcome only when the forcing question fails: "Can this be written as PROVIDES X SO THAT Y CAN Z with stable assertions?" If yes, make it an enabler. When unclear after the clarity gate and interview, default to enabler.

</step>

<step name="extract_shared_providers">

**Step 6: Extract shared providers**

Before assigning indices, check whether two or more proposed children require the same substrate:

- Runtime API, data source, generated artifact, persisted state, or packaging surface
- Validation rule, command surface, safety boundary, credential model, or evidence harness
- Shared policy or invariant needed by multiple children

Extract the shared concern as a provider node, its kind fixed in Step 5, when removing it would break multiple children. Keep single-consumer infrastructure inside the consuming child.

</step>

<step name="ordering_evidence">

**Step 7: Build the ordering-evidence matrix**

Before assigning indices, record one row per candidate child and per existing sibling:

| Field    | Required content                                                                                                                       |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Node     | Full path from `spx/`, or the parent path plus candidate slug                                                                          |
| Consumer | The consumer its value reaches: one the product document names, or the audience the product's surfaces name in their TO slot           |
| Value    | What that consumer receives, in the product's own terms; an inward kind's value reaches the consumer through the nodes that consume it |
| Requires | Every sibling whose contract the node needs to deliver that value                                                                      |

Every sibling in a node's Requires cell is its predecessor. Read the cell from the product document and the kinds, never from the node's spec alone: a node's spec rarely names the pipeline that delivers it, and that pipeline is required all the same. A node whose row names no consumer, or a value no consumer receives, is not a child of this parent.

Then record every proposed ordering edge:

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

**What an index encodes.** Index assignment follows live `/understand` `<index_semantics>`: a child placed above a sibling claims that sibling's contract as a prerequisite it consumes or falls within, an unrelated earlier contract supplies awareness and creates no dependency, and same-index siblings are independent peers. A different-index assignment is therefore a standing claim that the successor depends on the predecessor's contract — sound only when the matrix's Consequence-if-absent row names what becomes invalid without that predecessor.

**Existing siblings are not precedents.** When decomposing under a node that already holds children, an existing lower-index child is not a precedent that a new child sits above it, and the next sparse integer after the highest existing index is not the default slot. A new child takes the same index as an existing sibling — an independent peer — unless the matrix proves one constrains the other.

Use full paths from `spx/` for existing nodes, ADRs, and PDRs in the matrix. For new candidate children before the final index exists, include the full parent path plus candidate slug so the reference can be resolved after assignment.

**Direction comes from the Requires cell.** The predecessor of an edge is a node in the successor's Requires cell, and the Consequence-if-absent cell names the consumer who stops receiving the Value when that predecessor is removed. A sentence about which node builds, ships, collects, reads, or breaks the other decides no direction: a component change that breaks the pipeline delivering it says nothing about order, while the component's Requires cell names the pipeline first. An edge whose Consequence-if-absent cell names no consumer losing a Value is no edge.

**The matrix is a file.** Write the rows, the edges, and the disposition checkpoint to a file in the scratch directory the harness names for the session, under a file name unique to the agent and the target, and read it back. Step 8 reads every index from that file; an index assigned without it is a guessed slot. The run's result names that file's full path.

**Disposition checkpoint — mandatory before Step 8.** In the same file, state every proposed sibling pair explicitly as one of: ordered (name the matrix row proving the edge), same-index (independent peers, no edge), or unordered. Assign no index until every different-index pair names its proving matrix row; a pair with no row is same-index, never a guessed slot.

</step>

<step name="assign_indices">

**Step 8: Assign sparse integer indices**

Read every index from the matrix file Step 7 wrote. The horizon math below composes a set of new children from scratch. When adding a child beside existing siblings, skip the distribution math and read the child's index from its disposition-checkpoint rows against each existing sibling:

- It shares the index of a sibling the checkpoint marked its independent peer.
- It takes an index above a predecessor or below a successor only from a pair the matrix proved ordered. Existing siblings at different indices are already ordered relative to each other, so a child cannot be the independent peer of two of them at once.
- When the checkpoint names both an ordered predecessor and an ordered successor among the existing siblings, the child takes the midpoint of the band between their indices: the integer midpoint rounded down where an integer lies between them, a two-digit fractional insert at the midpoint, such as `20.50`, where none does, and one more two-digit segment, such as `20.00.50` between `20` and `20.01`, where no two-digit fraction lies between them either.
- NEVER: the next integer after an existing sibling's index is the index.

1. Choose the horizon:
   - Full composition of all known child concerns → use the full [10, 99] range.
   - First slice of a larger known area → use the first half or first quarter and record the reserved horizon in the Proposed Change Step 4 records.
2. Count child nodes in the chosen horizon.
3. Distribute ordered groups with `i_k = 10 + floor(k * 89 / (N + 1))`, adjusted to the selected horizon.
4. Assign a higher index only when the ordering-evidence matrix proves the predecessor constrains the successor — the higher index makes that predecessor constraining context for the successor in every later `/contextualize`.
5. Assign the same index — an independent peer — when no ordering evidence exists, including a new child added beside an existing sibling with no proven edge.

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

For `spx/`, write top-level children from product scope and root coordination-note intent. Product-level assertions stay in the product document unless they specify only one child concern.

</step>

<step name="write_specs">

**Step 10: Write child specs**

For each new child node, and never for a node that exists elsewhere in the tree:

1. Create `{index}-{slug}.{kind}/` in a tree that carries the kind suffixes, or `{index}-{slug}.{enabler|outcome}/` in a tree authored under a 3.x version.
2. Create `{slug}.spec.md`, or `{slug}.md` in a tree authored under a 3.x version.
3. Use the applicable canonical node template provided by `/understand`.
4. Add redistributed assertions or placeholder review assertions only when the child is intentionally declared without test evidence yet.

Do not create an empty `tests/` directory at composition — a node has no tests yet, git does not track empty directories, and the `tests/` directory materializes when `/verify` or `/apply` writes the first test file.

Revise the parent spec so it summarizes the child structure without narrating the refactor. Remove moved assertions and keep cross-cutting assertions.

</step>

<step name="validate">

**Step 11: Validate the composed tree**

Run the product's verify command for the spec lane against the written tree: `spx validation markdown` and `spx spec status --format json`, and every further command the root guide names for a spec-only change, which runs through per-call approval where the grants above omit it. A nonzero exit stops the run with the command, its exit code, and its failing output.

Check each criterion:

- [ ] Composition need assessed and not forced
- [ ] Clarity gate complete, or `/interview` used to resolve gaps
- [ ] Delivery substrate and evidence strategy accounted for
- [ ] Concern groupings presented before writing files
- [ ] No child has only 1-2 trivial assertions
- [ ] Any named aggregate boundary with an independently validated first concrete slice became parent plus child, with deferred siblings or reserved horizon recorded when known
- [ ] No child exceeds ~7 assertions without a recursive-decomposition issue
- [ ] Shared providers have at least two dependent children
- [ ] Ordering-evidence matrix and disposition checkpoint written to a scratch file and read back before index assignment, and the result names that file's full path
- [ ] No directory created for a candidate that exists elsewhere in the tree
- [ ] Every candidate child and existing sibling has a row naming its consumer, its value, and what it requires, and every edge's predecessor is in the successor's Requires cell
- [ ] Disposition checkpoint stated every sibling pair as ordered, same-index, or unordered before any index was assigned
- [ ] Every different-index sibling relationship has ordering evidence
- [ ] No new child placed at a higher index than an existing sibling without a matrix row proving the edge
- [ ] A child between an ordered predecessor and an ordered successor took the band's midpoint
- [ ] Roadmap, chronology, theme grouping, and explanation order are not encoded as dependencies by themselves
- [ ] Index horizon selected; partial compositions reserve remaining space in a Proposed Change
- [ ] Full compositions collectively cover the parent or product scope; partial compositions cover the selected first-slice horizon and record the remaining horizon in a Proposed Change
- [ ] Assertions are not lost during redistribution
- [ ] Spec files use atemporal voice
- [ ] Each new child's kind fixed by Step 5, and its directory name and spec file in the form the tree carries
- [ ] Every node, ADR, and PDR reference uses a full path from `spx/`
- [ ] The product's verify command for the spec lane passed on the written tree

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

How to avoid: Extract a provider only when two or more children depend on it. Keep single-consumer infrastructure inside the consuming child.

**Failure 5: Lost assertions during redistribution**

Claude moved parent assertions into children and dropped one cross-cutting assertion because it fit no single child.

How to avoid: Count assertions before and after. Assertions that span children remain in the parent.

**Failure 6: Wrote bare node or decision references**

Claude wrote `32-parser.enabler` or `15-build.adr.md` in a decomposition plan. Another directory used the same numeric prefix, so the reference could not be resolved. Full paths from `spx/` are mandatory for every existing node, ADR, and PDR.

How to avoid: When recording an ordering-evidence matrix, assertion move, issue, or Change, write `spx/.../32-parser.enabler` and `spx/.../15-build.adr.md`. Before a new child has a final index, write the full parent path and candidate slug.

**Failure 7: Took the next sparse slot after an existing sibling**

Claude decomposed under a node that already held `spx/.../21-journal.enabler`, proposed a new sibling, and assigned it `32` — the next sparse slot — with no ordering-evidence row. The higher index silently made journal constraining context for the new child in every later `/contextualize`, encoding a dependency no evidence proved. Claude treated the existing sibling's index as a precedent and the next sparse integer as the natural choice; the operator had to name the missing ordering reference before Claude saw that the index was context-loading semantics, not an index-budget slot.

How to avoid: Run the disposition checkpoint before assigning any index. Treat a new child as an independent peer at the same index as an existing sibling unless the matrix proves one constrains the other — an existing lower-index sibling is never a precedent for the next slot.

**Failure 8: Collapsed the first concrete slice into the aggregate**

Claude created only a parent domain node when the request named an aggregate domain plus its first concrete behavior. The parent then carried behavior-specific assertions, so adding the next behavior would require splitting the parent later and moving assertions that were specific from the start.

How to avoid: When the aggregate owns shared scope or cross-child policy and the concrete behavior has its own validation contract, create both parent and child immediately. Put shared assertions on the parent, behavior-specific assertions on the child, and record the deferred sibling horizon as a Proposed Change when the later slices are known.

**Failure 9: Left decision placement to authoring while ownership was unsettled**

Claude asked `/author` to place exactly one PDR even though the concept crossed plausible owners and raised node identity questions. Authoring proposed a path from reach, then the operator had to ask whether decomposition had run.

How to avoid: treat ADR/PDR placement as decomposition work when the location depends on concept ownership, node renaming, node splitting, parent/child boundaries, or context-loading reach. Return the owning directory and scope boundary first; `/author` writes the decision record only after that structure is settled.

**Failure 10: Took the direction of a dependency from a verb**

Claude placed a shipped component's node against the node that delivers it to consumers three times from three sentences — the pipeline collects the component, a change in the component breaks the pipeline, the component has no value without the pipeline — reading each verb as a direction, then searched the component's spec for the pipeline's name, found none, and called the two independent. The node moved twice before the operator reset it.

How to avoid: Fill the node's row first — consumer, value, and what it requires to deliver that value. The pipeline that delivers a component is in its Requires cell whether or not its spec names it; a verb decides no direction, and a spec's silence proves no independence.

**Failure 11: Invoked the skill with the index already chosen**

Claude invoked `/decompose spx/` with a candidate index in the argument, wrote no matrix, and moved the node to that index. The argument carried the answer, so every step confirmed it instead of deriving one.

How to avoid: `<quick_start>` stops on an argument that carries more than the target.

</failure_modes>

<anti_patterns>

**Pre-shaped child lists.** Structure comes from the matrix. The argument carries the target alone, per `<quick_start>`.

**Implementation-layer decomposition.** Children named only "frontend," "backend," or "database" are usually layers, not independently validated concerns.

**Outcome inflation.** In a tree authored under a 3.x version, use outcomes only for real uncertainty. Stable, specified outputs are enablers even when users see them.

**Narrative ordering.** A list that is easy to explain in order is not automatically a dependency chain.

**Skipping product-root composition.** Bootstrapping creates the product root; `/decompose spx/` composes top-level children.

**Bare references.** A node name, ADR filename, PDR filename, or numeric prefix without the full `spx/` path is not a reference. It is an ambiguous label.

</anti_patterns>

<success_criteria>

Decomposition is complete when:

- [ ] Target is either `spx/` or a valid node address, and the argument carried nothing else
- [ ] Context loaded through a live `<PRODUCT_TREE_CONTEXT>` marker for the exact target
- [ ] Composition need assessed
- [ ] Clarity gate completed or `/interview` used
- [ ] Concern boundaries and node kinds assigned in the form the tree carries
- [ ] Shared providers extracted only for multi-child dependencies
- [ ] Aggregate parent plus independently validated first concrete child preserved when the input named both levels
- [ ] Ordering-evidence matrix written to a scratch file, read back, and its full path named in the result, every node with its consumer, value, and Requires cell, and every edge's predecessor in the successor's Requires cell
- [ ] Disposition checkpoint stated before index assignment; no index guessed from an existing sibling's slot, and a child between an ordered predecessor and successor at the band's midpoint
- [ ] Sparse indices assigned from the matrix file and the selected horizon
- [ ] Assertions redistributed without loss
- [ ] Parent or product document revised without temporal narration
- [ ] Child specs written from templates for new children only
- [ ] Full `spx/` paths used for every node, ADR, and PDR reference
- [ ] The product's verify command for the spec lane passed on the written tree, and the checklist passes

</success_criteria>
