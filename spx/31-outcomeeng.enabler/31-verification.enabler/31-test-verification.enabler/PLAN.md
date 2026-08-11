# Plan: extract assertion ownership and test methodology

The test-verification merge cycle separates governing assertion ownership from the methodology and language-specific surfaces that consume it.

## Decision and assertion ownership

PR #448 on `work/assertion-flow-governance` carries the governing assertion-flow and test-infrastructure declarations. Reconcile it with current source-owned test-data decisions and merge it before implementation guidance that depends on those declarations.

## Methodology consumption

PR #454 on `work/python-test-seam-standards` currently changes 95 paths across shared test methodology and Python, Rust, and TypeScript test guidance. Before publication, classify the authored source by semantic contract:

- Keep one PR when every authored change implements the same cross-language ownership rule and the remaining breadth is deterministic generated fan-out.
- Split independently mergeable language or architecture contracts when each has its own verification and rollback story.
- Keep the governing decision, first affected specs, shared methodology, language consumers, evidence, and generated trees together only when separating them would leave a lower layer inconsistent.

## Revisit condition

This plan is complete when PR #448 is merged and the PR #454 branch has either passed a current semantic-cohesion review as one contract or been replaced by dependency-ordered reviewable PRs whose node-local plans name the remaining work.

## Programme: per-evidence-type test standards

Complete picture, authored before slicing. Every slice below derives from it; none of it is sliced yet.

### The defect model this corrects

Four measured properties of the current surface, each verified against the files rather than inferred.

The seam rules are prohibitions on *place*. `test-verification.md` carries nine NEVER rules naming a forbidden location or shape against two ALWAYS rules stating where a value may legitimately come from. A prohibition on a place is satisfied by moving, so the methodology has accumulated one named variant per address — literal, generator, fixture, pytest-fixture, and now source laundering — while never stating the invariant they instance.

`:30` authorises the newest variant. It instructs that when a test cannot obtain a value "the source is improved before the test is accepted", and nothing defines what a source improvement is, so adding the value the test wants to the module under test is a compliant reading.

There is no per-assertion-type guidance. All three language test-standards skills partition by artifact category and execution level, and carry exactly one assertion-type section each, for property. Nothing states what evidence for a scenario, mapping, conformance, or compliance assertion looks like, so an author holding a scenario assertion finds only rules that point at infrastructure.

Run-configuration ownership is stated for property alone. `:25` opens "property-based tests run through spec-governed harnesses that own seed selection, run count, replay input"; timeouts, deadlines, and temporary-directory lifecycle have no owner rule at any assertion type. The first test in a node therefore has no harness to use, inlines its configuration, and sets the pattern every later test copies — a cost named nowhere in the tree.

### The invariant

**Extraction moves code, never choice.** An extraction is legitimate exactly when every value the moved code chose is supplied at the call site afterwards. A value that disappears from the test file during an extraction is a choice that moved, and that is laundering regardless of destination or intent.

This is the generative form the five named variants instance, and it applies at the moment of the action rather than as a property of a finished file. It is self-checkable: diff the test before and after an extraction and look for any case value that left. It also states the boundary the harness question needs — repeated setup is duplication at every assertion type including scenario and belongs in a harness, while the case values stay at the call site, duplicated from the spec.

### Target structure

One order, in the shared standard first and mirrored as language expression:

1. **Execution levels** — defined once.
2. **Artifacts** — harness, generator, fixture — defined once, with run configuration (seed, run count, timeout, deadline, temporary-directory lifecycle) named as a harness concern at every assertion type rather than property's alone, and with the first-test cost stated: the first test in a node pays for the harness every later test uses, and being first is not an exemption.
3. **One section per assertion type** — scenario, mapping, conformance, property, compliance — each referring back to levels and artifacts and stating which artifacts that type permits or requires. The permission matrix is genuine, not decoration: a conformance parser test needs whole-payload fixtures, a property test's domain is generated so a fixture collapses it to examples, and a mapping's domain is a source-owned enumeration so a fixture bag is laundering.

The scenario section carries both halves together, because separating them is how the defect arrives: the spec's exact interaction is duplicated into the test file and every scenario assertion carries its case, while repeated staging goes to a harness that receives those values and never holds them.

### Decisions taken

- **The journaled test design binds choices and frees expression.** It fixes the assertion type, execution level, each case's source, the oracle, and the artifacts used; the auditor rejects deviation from those without a re-run design. Naming, ordering, and structure stay free. This matches the defect distribution — every failure observed has been a choice, never an expression detail.
- **`design-tests` is not a new concern.** `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler/test-skill.md:11` already assigns `/test` assertion typing, execution-level selection, source-contract and oracle gates, exception classification, and naming policy — every choice the design binds. What is missing is isolation, a durable journaled artifact, and an auditor that consumes it. The agent is `test-designer` in actor form, distinct from the skill it implements.
- **Python is the reference implementation.** It is the only plugin with no delegated assertions and no laundering sites, and it already has the tests subtree the per-type sections attach to, so the structure can be judged without the noise of simultaneous repair. Rust and TypeScript follow a proven exemplar.
- **Sections, not five workflows.** The per-type content exists in no form today; as sections in the shared standard it reaches author and auditor at once, since `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md:14` requires both to consume one loadable standard that five workflows would have to reconstruct. Revisit when the sections exist and their routing cost is observable.
- **Tier is deferred entirely.** The per-type sections state evidence shape; tier arrives when the CLI projects the frontmatter field, and lands in spec-audit, which decides whether a node's declared assertion set is adequate. `audit-tests` needs no change for it — that audit is purely assertion-driven and never asks whether more assertions should exist.

### Structural questions routed to `/decompose`, not chosen here

- **Rust has no tests subtree.** Only `spx/43-rust.enabler` exists, so the per-type sections have no node to attach to. `spx/43-rust.enabler/PLAN.md` already anticipates this decomposition.
- **Where `design-tests` is governed.** It sits beside `/test` under `spx/21-spec-tree.enabler/35-evidence.enabler/`, and whether it is a new child or an assertion on `39-test-skill.enabler` depends on whether it composes `/test` or replaces part of it. `evidence.md:15` forbids an evidence specialist calling back into its router, so the composition direction is a constraint on that choice, not a free one.
- **Which channel carries a design run.** `spx journal --type` is opaque and `--type design` needs no CLI change, but `spx/21-spec-tree.enabler/16-verification.enabler` frames the channel as carrying verification kinds and a design is not a verification. Either the channel's declared scope widens to run kinds, of which verification kinds are a subset, or a sibling channel exists.

### Work, in dependency order

Each item names what it touches. None is sliced into a PR yet.

1. **The invariant and the configuration rule, language-neutral.** `test-verification.md` gains the extraction invariant and widens run-configuration ownership beyond property; `:30` gains a definition of what a source improvement is. The superset owns these; no language node restates them.
2. **The shared standard restructured.** `src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md` takes the three-part order and the per-type sections, including the first-test cost. Governed by `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler`.
3. **`audit-tests` Step 3a ordering.** Its ownership table rejects hand-picked data and expected outputs unconditionally, and the instruction to apply the per-assertion-type litmus follows the table. A correct hardcoded scenario is rejected on that path today. Independent of everything else and small.
4. **Python as reference.** Per-type sections in `python-test-standards` carrying only Python expression; spec deltas in `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/`, whose four concern children are cross-cutting and survive alongside the new axis.
5. **Rust.** `/decompose` for the tests subtree, then the per-type sections, then the four source-laundering sites in `code-rust/references/test-patterns.md` that the new rules govern, and the Rust delta for source laundering that `spx/43-rust.enabler/PLAN.md` already records.
6. **TypeScript.** Per-type sections plus the twenty inventoried predicate-seam sites and the TypeScript source-laundering delta, both already recorded in `spx/43-typescript.enabler/25-typescript-standards.enabler/PLAN.md`.
7. **`design-tests` and `test-designer`.** After the standard exists, because the design conforms to it. Then `audit-tests` consumes the sealed design and judges implementation conformance to the bound choices.

### Constraints that bound every slice

No shipped skill depends on an unpublished `spx` capability. Author and auditor consume one loadable standard. Routing stays acyclic. Every changed skill surface passes the typed skill auditor in an isolated context. Each touched plugin bumps once per branch. Generated trees are rebuilt, never hand-edited.

## Decomposition disposition — the superset is a deliberate single node

`test-verification.md` carries roughly 24 Compliance assertions, well past the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md:ALWAYS:1`. This is the intended shape, not carried-forward duplication: the node is the single language-neutral **superset** of the test-evidence seam rules, and every language test-standard node cites it and declares only its language delta. Decomposing the superset into per-concern child nodes would re-fragment the exact union the design unifies, and language nodes would then cite a parent whose rules are spread across children — reintroducing the cross-language drift the superset removes. The count is a consequence of consolidating three languages' rules into one owner, so the decomposition signal is dispositioned as accepted here rather than acted on.
