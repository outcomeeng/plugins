---
name: decompose
description: ALWAYS invoke this skill when breaking down, splitting, scoping, composing, or structuring spec tree nodes. NEVER decompose specs without this skill.
argument-hint: <node-address|spx/>
allowed-tools: Read, Glob, Grep, Write, Edit, {{! tool('use_skill') !}}, Bash(spx validation markdown:*), Bash(spx spec status --format json:*)
---

<objective>

Spec Tree structure composed from settled product truth — each concept placed under the correct owner, classified by the ordered kind procedure, indexed from its prerequisites, and validated by the product's declared commands.

</objective>

<quick_start>

Require a live `<SPEC_TREE_FOUNDATION>` marker; invoke `/understand` when absent.

Accept exactly one target from `$ARGUMENTS`:

- `spx/` composes top-level children beneath the product root.
- A canonical full `spx/...` node address composes children beneath that node.

Stop before product-content access when the argument is absent, malformed, or contains more than one target. State the two accepted forms.

Invoke `/contextualize` for the target node. For `spx/`, contextualize the product root. Read the conditional resources exposed by `/understand` when their decision is reached:

- `kind-decision` for ordered kind tests and structural scorecards
- `product-domain-shapes` for aggregate, product, and implementation-layer distinctions
- the selected output-kind or variant template before writing a spec
- `grammar` before assigning a fractional index or validating a node address

</quick_start>

<workflow>

<step name="load_context">

**Step 1: Load authoritative context**

From the live context manifest, read the product and ancestor contracts, target spec, governing decisions, sibling contracts, existing children, and node-local `ISSUES.md` files. A 3.x-authored tree may also carry `PLAN.md`; read it as a fallible note and never as structural authority.

Treat proposed child names, kinds, indices, and dependency order as intent to test against product truth. Keep pending work in the governing Change. Never create or update `PLAN.md`.

For `spx/`, derive top-level concepts from the product boundary and decisions. A product spec names scope and product-owned terms; it never enumerates children.

</step>

<step name="assess_trigger">

**Step 2: Establish the countable trigger**

Decompose when either condition holds:

1. The target contains two or more distinct concepts, present or foreseen.
2. The target carries too many assertions for one coherent node.

Count concepts by semantic ownership and lifecycle, not by implementation layer, command count, evidence mechanism, or presentation order. Keep one coherent concept whole. When no trigger holds, report that the node remains one concept and make no structural change.

When the context payload is unreliable because one dimension is overloaded, identify the distinct concepts within that dimension and apply the same trigger. When product truth and operator intent leave a boundary unresolved, invoke `/interview` with that exact boundary before continuing.

</step>

<step name="resolve_decisions">

**Step 3: Resolve decision ownership**

Before `/author` writes an ADR or PDR, resolve its owning directory whenever decomposition affects concept ownership, node identity, parent/child boundaries, or context reach.

Place the record in the node whose subtree it governs. Use a PDR for observable product behavior and an ADR for architecture users cannot observe. A root decision governs every subtree; broad reach alone never makes a decision root-owned. If no existing node owns the concept, settle the structure first and author the record afterwards.

</step>

<step name="identify_concepts">

**Step 4: Identify semantic owners**

Group assertions and settled scope into concepts that share one subject and lifecycle. A child must own a meaningful contract; implementation-only partitions and one-line wrappers are not concepts.

- Keep class-wide rules and assertions on the parent.
- Move behavior-specific assertions to the child that owns their meaning.
- Extract a provider when two or more semantic owners share behavior, or when the behavior has its own lifecycle and verification contract.
- Keep single-consumer mechanics with the consumer unless those mechanics independently satisfy a kind test and lifecycle boundary.
- When an aggregate owns shared vocabulary, rules, routing, or cross-child assertions and the first concrete behavior has its own contract, retain the aggregate parent and create the concrete child.

When unresolved boundaries remain, invoke `/interview`. When the evidence settles them, continue without a confirmation pause.

</step>

<step name="classify_kinds">

**Step 5: Classify every node**

Apply the `kind-decision` tests in this exact order; the first test that holds fixes the kind:

```text
product -> variant -> substrate -> surface -> interface -> domain -> capability
```

Then apply the live containment table:

- A product admits every output kind; only a product admits another product.
- An output node admits its own kind, every more-foundational output kind, and variants.
- A variant admits what its parent admits except another variant.
- A provider is never more outward than its consumer under `substrate < capability < domain < interface < surface`; a variant takes its parent's place.

Use the selected kind's canonical opening. The `FOR` and `TO` slots name consumption context or external audience, never a consumer node. Openings carry no paths.

Record one classification result per candidate: first passing test, rejected earlier tests, containment check, opening, and provider/consumer kind-order check. Invoke `/interview` when the tests do not settle a candidate from loaded truth.

</step>

<step name="assign_indices">

**Step 6: Assign indices from prerequisites**

Nodes and decisions share one sibling index space. Check kind order before index assignment, then ask only what each candidate depends on.

For every candidate:

1. Name each prerequisite by its full `spx/...` path.
2. State the provider contract, logical prerequisite, vertical-slice contract, shared substrate, feature extension, or decision constraint consumed.
3. State what becomes impossible, invalid, or unverifiable without it.
4. Place the candidate above every prerequisite it names.
5. Check that every lower-index decision whose scope reaches the candidate is intended to govern it.

Numeric separation alone establishes no dependency. Independent siblings may use the same or different indices. Reuse an existing peer index only when it satisfies the candidate's prerequisites and decision scope; the next free number is never a default. Same-index peers cannot supply prerequisites to each other. Use a fractional insert when the prerequisite interval has no suitable integer, following the `grammar` reference.

Reject roadmap priority, chronology, theme grouping, explanation order, and reserved future space as index evidence.

</step>

<step name="redistribute_assertions">

**Step 7: Redistribute declarations**

For a node target, record each assertion's destination before editing:

- the child that owns its meaning;
- the parent when the assertion states the class contract; or
- a blocking ambiguity resolved through `/interview`.

Move each path-bearing evidence link with its assertion and resolve it relative to the new node. Keep cross-child rules on the parent without naming the children. Count assertions before and after; the remaining parent assertions plus all child assertions must equal the original count.

For `spx/`, create child contracts from product scope and decisions. Leave the product spec as product scope; never add assertions or child enumeration to it.

</step>

<step name="write_structure">

**Step 8: Write the 4.0 node form**

For each child:

1. Create `{index}-{slug}.{kind}/` using the assigned two-digit or fractional index.
2. Create `{slug}.spec.md` from the selected `/understand` template.
3. Generate a unique UUIDv7 `id` in front matter.
4. Declare `malleability` on every output node; omit it only when the intended floor is `implementation`.
5. Write the canonical kind opening and the redistributed assertions in atemporal voice.

Never hand-write `spx.status.json`; the projector owns it. Never create an empty evidence directory. Never list children in the parent spec. A provider operating on a 3.x-authored tree may parse `.enabler`, `.outcome`, `{slug}.md`, and prior `PLAN.md` inputs; new structure follows the repository's declared methodology, and a toolchain unable to admit that grammar is a lower-layer blocker recorded in the governing Change.

</step>

<step name="validate">

**Step 9: Run command-backed validation**

Read the product's exact `author` and `verify` commands from its complete root guide. After every mutation batch:

1. Invoke `/wait-for-load` and wait for `ready: true`.
2. Run the product's declared author command unchanged to rebuild or regenerate derived artifacts.
3. Invoke `/wait-for-load` again and run `spx validation markdown` unchanged.
4. Invoke `/wait-for-load` again and run `spx spec status --format json` unchanged.
5. Invoke `/wait-for-load` before each remaining product verify command and run it unchanged.

Stop on the first nonzero result. Report the exact command and output; never claim a composed tree is valid from a checklist alone.

After the commands pass, confirm:

- every child has one semantic owner and a countable reason to exist;
- every kind result follows the ordered procedure and containment table;
- every provider/consumer pair respects kind order;
- every named prerequisite precedes its consumer with a falsifiable reason;
- every decision has the intended subtree reach;
- assertion counts and evidence links are conserved;
- every new node uses the 4.0 directory, spec, front-matter, and opening grammar;
- every node, ADR, and PDR reference is a full path from `spx/`;
- pending work is carried by the governing Change, never `PLAN.md`.

</step>

</workflow>

<failure_modes>

**A coherent node was split into implementation layers.**

Claude created children that could not be specified or verified independently. Count concepts by semantic ownership and lifecycle; keep implementation partitions inside the concept they serve.

**A desired label bypassed the ordered kind procedure.**

Claude selected a plausible kind from the candidate's name, then rationalized it. Apply the tests in order and record the first passing test plus the earlier rejections.

**Roadmap order became index order.**

Claude assigned increasing indices because one slice was planned earlier. Index only from the candidate's own prerequisites and name the consequence of removing each prerequisite.

**The next sparse slot became a default.**

Claude placed a new child after the highest existing index without checking prerequisites or decision scope. Reuse a peer index only when it fits; otherwise derive an integer or fractional position from the actual constraints.

**Assertions disappeared during redistribution.**

Claude moved child-specific assertions and dropped a class-wide assertion with no single child owner. Record every destination first and prove count conservation after the move.

**A note dictated structure.**

Claude treated proposed children in `PLAN.md` or `ISSUES.md` as an approved tree. Reconcile notes against product truth and settled intent; keep pending work in the Change.

**Decision placement was deferred to authoring.**

Claude asked `/author` to place a decision while decomposition still left its semantic owner unsettled. Resolve the owner and subtree boundary first.

**A checklist replaced deterministic validation.**

Claude reported success after inspecting the files while the product's author and verify commands had not run. Execute every declared command and stop on any nonzero result.

</failure_modes>

<success_criteria>

- The target is `spx/` or one canonical full node address, with complete live context.
- A countable trigger justifies every split.
- Each concept has one semantic owner and one kind selected by the ordered procedure.
- Containment, openings, and provider/consumer kind order conform to the live foundation.
- Every decision owner is settled before `/author` writes the record.
- Every index follows the candidate's prerequisites and decision scope; no slot is guessed.
- Assertions and evidence links are conserved under the owning nodes.
- New nodes use `{index}-{slug}.{kind}/{slug}.spec.md`, UUIDv7 identity, and declared output malleability.
- Parent and product specs enumerate no children, and pending work appears in the governing Change rather than `PLAN.md`.
- The product's author and verify commands, `spx validation markdown`, and `spx spec status --format json` all pass.

</success_criteria>
