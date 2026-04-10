<overview>

When looking at a node's scope, ask: **"Is this one coherent thing, or does it contain multiple independent concerns?"**

If it contains multiple concerns, decompose into child nodes. Each child is either an enabler (shared infrastructure) or an outcome (hypothesis + assertions).

</overview>

<enabler_vs_outcome>

The distinction is about **certainty**, not visibility or user-facing-ness.

Both enablers and outcomes have assertions and tests. Both specify outputs. The question is: **do you know whether this output achieves the desired effect?**

**Enabler:** The output is known. Context loading walks the tree deterministically. A parser transforms input to output according to a grammar. A validation pipeline checks fields against a schema. You can specify exactly what these things do and there's no question about whether they'll work — the specification IS the answer.

**Outcome:** The output is a hypothesis — a bet. A landing page converts visitors — but *which* landing page design maximizes conversion? You don't know. The three-part hypothesis exists because you're making a bet: this output will produce this behavior change, contributing to this business impact. You might be wrong.

### Litmus test

Ask two questions about the node:

1. **Could the majority of assertions change while the goal stays the same?** Yes → **Outcome.** The assertions are a bet. If the landing page doesn't convert, you redesign it — different assertions, same outcome hypothesis. The hypothesis is stable; the output is experimental.

2. **Is the goal statement a behavior change you could be *wrong* about, or a capability you're guaranteeing?** If you could be wrong → **Outcome.** If you're guaranteeing a capability whose output is fully determined → **Enabler.** This catches the ambiguous case: a node whose assertions are mostly stable but whose goal is framed as a user behavior change. If the goal is "increase conversion," you could be wrong about whether this output achieves it. If the goal is "validate frontmatter fields," you're guaranteeing a capability — there's nothing to be wrong about.

### The forcing question

Try to write it as an enabler first. PROVIDES X SO THAT Y CAN Z. If you find yourself weakening the PROVIDES statement to accommodate assertions that don't follow from it, or adding a hedge ("WE BELIEVE..."), the node is an outcome. Use an outcome only when you *cannot* write it as an enabler because the right output is uncertain.

If the forcing question still leaves you uncertain, **default to enabler.** Most nodes in a spec tree are enablers. Outcomes are rare — they exist where genuine product uncertainty lives. Don't inflate enablers into outcomes by forcing a hypothesis.

### Common mistake

Treating "user-facing" as the criterion. A CLI command users invoke directly can still be an enabler if its behavior is fully determined. A background process can be an outcome if the right internal design is a genuine bet about user behavior.

### Decomposing outcomes

When a parent node is an outcome and you are decomposing it, not every child is an outcome. Apply the forcing question to each child. If it can be written as PROVIDES X SO THAT Y CAN Z, it's an enabler. A child is an outcome only if it has its own genuine uncertainty — a separate bet about which output achieves a desired behavior change. If the child exists to serve the parent outcome (by providing identity, storage, lifecycle, or any internal capability) and its output is fully determined, it is an **enabler**.

This means a typical complex feature has **one outcome at the top** and everything below it is enablers. The outcome is the product bet ("agents adopt CLI handoffs instead of manual file editing"). The enablers are the machinery that makes the bet testable ("session identity," "atomic claiming," "CLI surface"). Do not inflate internal decomposition into fake outcomes.

### Decomposing enablers

When a parent node is an enabler and you are decomposing it, **children are always enablers** (or decision records). An enabler decomposes into more infrastructure, never into bets. See `node-types.md` `<nesting_rules>` for the full constraint.

If you find a child under an enabler that seems to need an outcome hypothesis, one of two things is wrong:

- The parent should be an outcome (it carries genuine uncertainty), or
- The child's output is actually fully determined and should be written as an enabler

To resolve: apply the forcing question to the parent. If the parent cannot be written as PROVIDES X SO THAT Y CAN Z without forcing it, retype the parent as an outcome.

</enabler_vs_outcome>

<when_to_decompose>

Decompose a node when:

- It has more than ~7 assertions across all types (scenarios, mappings, conformance, properties, compliance) — the spec is doing too much
- Its deterministic context payload exceeds an agent's reliable working set
- It contains independent concerns that could be validated separately
- Two assertions in different parts of the spec have no relationship to each other

Do NOT decompose when:

- A single coherent hypothesis covers all assertions
- The assertions are tightly coupled and meaningless in isolation
- Decomposition would create nodes with only 1-2 trivial assertions

</when_to_decompose>

<depth>

The tree has no fixed number of levels. A simple product might have:

```text
spx/
├── product.product.md
└── 21-core.outcome/
```

A complex product might nest 4-5 levels deep. Depth emerges from the product's actual complexity, not from a prescribed hierarchy.

</depth>

<children_heuristic>

At any directory level, aim for at most ~7 child nodes. This is not a hard limit — it's a signal:

- More than 7 children → consider grouping related children under a parent outcome or enabler
- Fewer than 3 children → consider whether the parent node is necessary

The sparse integer ordering formula `i_k = 10 + floor(k * 89 / (N+1))` for N=7 produces the canonical sequence 21, 32, 43, 54, 65, 76, 87.

</children_heuristic>

<shared_enabler_extraction>

Extract an enabler when:

- Two or more sibling nodes share a dependency
- The shared piece is infrastructure, not user-facing value
- Removing the shared piece would break multiple siblings

Place the enabler at a **lower index** than the nodes that depend on it:

```text
NN-shared-infra.enabler/       # Lower index
NN+k-depends-on-it.outcome/    # Higher index, depends on enabler
NN+k-also-depends.outcome/     # Also depends on enabler
```

</shared_enabler_extraction>

<cross_cutting_assertions>

When a behavior spans multiple child nodes, the assertion belongs in the **lowest common ancestor**:

- The ancestor's spec captures cross-cutting behavior
- Child nodes handle their local concerns
- If an ancestor accumulates too many cross-cutting assertions, extract a shared enabler at a lower index

</cross_cutting_assertions>

<growth_patterns>

**Starting small:** A new tree starts with a product file and a handful of nodes. Structure emerges as the product grows.

```text
spx/
├── product.product.md
├── 21-core-infra.enabler/
└── 43-first-feature.outcome/
```

**Horizontal growth:** Adding a new independent concern at the same level.

```text
spx/
├── product.product.md
├── 21-core-infra.enabler/
├── 43-first-feature.outcome/
└── 54-second-feature.outcome/     # New sibling
```

**Vertical growth:** Decomposing an existing node into children.

```text
43-first-feature.outcome/
├── first-feature.md
├── 21-shared-setup.enabler/       # Extracted enabler
├── 32-sub-behavior-a.outcome/     # Decomposed from parent
└── 43-sub-behavior-b.outcome/     # Decomposed from parent
```

**Restructuring:** When a child grows into its own complex subtree, the tree absorbs this naturally. No renumbering of siblings. The parent's index stays the same; only its internal structure changes.

</growth_patterns>
