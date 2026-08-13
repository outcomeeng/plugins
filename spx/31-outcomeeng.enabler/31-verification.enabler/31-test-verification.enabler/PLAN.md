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

### The gap matrix this corrects

Per-assertion-type guidance already exists on three surfaces. Each row below names what that guidance answers and the one question it leaves open. A slice whose only output is a second rendering of an answered question is cancelled.

| Surface                                                                                                                                                             | Already answers                                                                                  | Open question                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md` `<assertion_type_litmus>`                                                                           | Required source and oracle per type, and the reject condition per type                           | Which artifacts each type permits or requires, and how that changes across execution levels |
| `src/plugins/python/skills/python-test-standards/SKILL.md` five-row case-source table; `src/plugins/rust/skills/rust-test-standards/SKILL.md` evidence-token tables | The per-type case source and the per-type testing shape in that language                         | The same artifact-permission question, and whether a language may narrow a neutral source   |
| `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` `## Evidence Chain`                                  | Source-and-oracle independence per type, and that infrastructure cannot upgrade an evidence type | Nothing per-type; this row is the authority the other two render                            |

Two further gaps are absences rather than under-specification.

**Run-configuration ownership has a list where it needs a rule.** The shared standard rejects test-file bindings that choose "property seeds, run counts, retries, timeouts, or replay policy" and "reusable setup, lifecycle, cleanup, or dependency policy" at every assertion type, and `15-test-infrastructure.pdr.md` states the same ownership generally. An enumeration does not tell an author where a concern it never listed belongs — port allocation, clock control, state reset between cases, teardown ordering. `test-verification.md:26` compounds this by declaring the ownership for property alone, so the spec layer under-declares what the shared standard already teaches.

**The first-test cost is named nowhere.** No surface across the shared standard, the three language standards, or this node says that the first test in a node pays for the harness every later test uses. The first test is the one with the least reason to build one and the most influence on what follows.

### The governing tests

Ownership is judged on the finished artifact by the checks the methodology already owns: semantic binding ownership, predicate inversion, oracle independence, and production mutation. Value disappearance across an extraction diff is one diagnostic clue that opens the question; it is not a rule and it decides nothing.

Two failures show why. A test that passes `input`, `actual`, and `expected` into `equivalent(input, actual, expected)` keeps every value at the call site while the helper chooses which fields matter and what tolerance applies — no value moved, the verdict did. And an author who writes `SAMPLE_CASES` at a production address together with the test that reads it launders with no extraction at all, because the defect is in the finished design and there is no before-state to diff.

Each artifact has its own valid transfer: a harness acquires execution policy, a generator acquires domain construction, a fixture acquires an inert whole payload, production acquires a real product contract, and the linked test retains the cases and the verdict its assertion type requires.

### Cross-assertion concerns versus the assertion's own

A value belongs to the harness when it survives both probes. Everything else belongs to the assertion and stays at the call site.

*Negation* — state the assertion's opposite. Does the value change? Thirty seconds is thirty seconds whether the operation must succeed or must fail.

*Transplant* — put the test in an unrelated product. Does the value change? Temporary-directory lifecycle is identical in a parser and in a payment gateway.

Neither probe stands alone. An input survives negation — same input, flipped expectation — so negation alone launders every case. A generic expected string such as `"timeout exceeded"` survives transplant, so transplant alone launders expectations.

Cross-assertion, by example: temporary-directory creation and removal, working directory, environment reset, clock control, seed, run count, shrink budget, timeout, deadline, subprocess launch and teardown, port allocation, output capture, state reset between cases, fixture-root resolution, teardown ordering.

The assertion's own, by example: the input, the expected output, the domain's boundaries, the oracle, the identity of the error.

The examples carry the harness conclusion by themselves. The only shape holding nothing from the left-hand list is a function called with values, returning a value, compared in place. Touch the filesystem, a process, the clock, the network, or randomness and the test has acquired a value the spec does not contain and the assertion cannot own — so a harness exists or those values are inlined.

### Target structure

The order is levels, then artifacts, then per-type sections that refer back to both. Artifacts carry the two probes above and the first-test cost. The per-type sections answer only the open questions in the gap matrix; they do not restate a source or oracle rule the litmus already carries.

Artifact permission is designed over the assertion-type × execution-level cross-product, because level changes the answer: an L1 scenario calls a pure function directly while an L3 scenario needs credential, isolation, and cleanup harnesses, and an L1 conformance claim can use a compile-fail harness where an L2 conformance claim exercises a real binary. Where a permission claim cannot be made without tier, the first slice states only the type invariants that hold at every level and defers the rest rather than asserting a permission the level contradicts.

Three file topologies are candidates, to be compared against the acceptance corpus below rather than chosen here: one document; a shared core routing to five typed references; five composed workflows. `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md:14` requires author and auditor to consume the same independently loadable standards source, which all three satisfy — it does not select among them. Compare loaded context, duplicated rules, routing branches, and drift behaviour.

### Proposals, pending their own decision records

Each item below is a proposal this note carries for coordination. None governs a spec, skill, or auditor until it is authored as an ADR or PDR, because a coordination note is stale-prone and holds no authority.

- **The journaled test design binds observable contracts.** It fixes the quantifier, each case's provenance, oracle independence, execution level, the resource guarantees, and the falsifying mutations. Naming, ordering, and structure are free only where they demonstrably preserve discovery, case identity, isolation, lifecycle, and verdict behaviour — in pytest a parameter name selects a fixture, case order can expose shared state, and test names drive collection, so none of the three is free by category.
- **`design-tests` is not a new concern.** `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler/test-skill.md:11` already assigns `/test` assertion typing, execution-level selection, source-contract and oracle gates, exception classification, and naming policy. What is missing is isolation, a durable journaled artifact, and an auditor that consumes it. The agent is `test-designer` in actor form, distinct from the skill it implements.
- **A language-neutral acceptance corpus proves the structure, and Python is the first rendering.** The corpus carries valid and invalid cases across all five assertion types, three execution levels, each artifact category, direct-authorship laundering, extraction laundering, public-API ownership, and oracle coupling. Python renders first because it has the tests subtree and no laundering sites to repair simultaneously; it cannot prove detection boundaries by itself, so Rust supplies the negative cases before any structure is called settled.
- **Tier is deferred.** The per-type sections state evidence shape; tier arrives when the CLI projects the frontmatter field and lands in spec-audit, which decides whether a node's declared assertion set is adequate. `audit-tests` needs no change for it — that audit is assertion-driven and never asks whether more assertions should exist. Execution level is available today and is designed for now, per the cross-product above.

### Structural questions routed to `/decompose`, not chosen here

- **Rust has no tests subtree.** Only `spx/43-rust.enabler` exists, so the per-type sections have no node to attach to. `spx/43-rust.enabler/PLAN.md` already anticipates this decomposition.
- **Where `design-tests` is governed.** It sits beside `/test` under `spx/21-spec-tree.enabler/35-evidence.enabler/`, and whether it is a new child or an assertion on `39-test-skill.enabler` depends on whether it composes `/test` or replaces part of it. `evidence.md:15` forbids an evidence specialist calling back into its router, so the composition direction is a constraint on that choice, not a free one.
- **Which channel carries a design run.** `spx journal --type` is opaque and `--type design` needs no CLI change, but `spx/21-spec-tree.enabler/16-verification.enabler` frames the channel as carrying verification kinds and a design is not a verification. Either the channel's declared scope widens to run kinds, of which verification kinds are a subset, or a sibling channel exists.

### Work, in dependency order

Each item names what it touches. None is sliced into a PR yet.

1. **The cross-assertion rule and the first-test cost, language-neutral.** `test-verification.md:26` states run-configuration ownership for property alone; it takes the two probes so the ownership binds at every assertion type, and gains the first-test cost. The ownership discriminator, the audit procedure for an absent caller, and the Python delta shrink landed in this changeset.
2. **The acceptance corpus.** The valid and invalid cases the gap matrix's open questions must decide, authored language-neutral before any structure is chosen, so the three candidate topologies are compared against the same subject. Precondition for item 3. Landed as `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`: the per-type × level permission semantics with the 54-case corpus as normative examples, the neutral execution-level semantics (lifted from the two language execution-level-guidance nodes, which shrink to deltas), the canonical filename model (lifted from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`, whose subject stays infrastructure), the per-language filename-instantiation obligation as a language delta, and the expression-only narrowing rule. Rust's filename instantiation and per-type deltas wait on item 6's `/decompose`.
3. **The shared standard restructured.** `src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md` takes the levels-artifacts-types order and answers only the open questions the gap matrix names, leaving the existing `<assertion_type_litmus>` rows as the source-and-oracle authority. Governed by `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler`.
4. **`audit-tests` Step 3a ordering.** The ownership table rejected hand-picked data and expected outputs unconditionally while the per-assertion-type litmus ran two steps later, so a scenario assertion carrying the spec's own interactions was rejected on that path. The litmus now resolves case-shaped values before the data rows and the REJECT row is scoped to data the assertion type does not assign to the test; this landed in this changeset.
5. **Python as first rendering.** The corpus rendered in Python and per-type content in `python-test-standards` carrying only Python expression; spec deltas in `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/`, whose four concern children are cross-cutting and survive alongside the new axis.
6. **Rust, which supplies the negative cases.** `/decompose` for the tests subtree, then per-type content, then the Rust source-laundering delta that `spx/43-rust.enabler/PLAN.md` records. The four `code-rust/references/test-patterns.md` laundering sites, the `assert_cmd` verdict-API sites, and the hardcoded command names were repaired in this changeset.
7. **TypeScript.** Per-type content plus the twenty inventoried predicate-seam sites and the TypeScript source-laundering delta, both already recorded in `spx/43-typescript.enabler/25-typescript-standards.enabler/PLAN.md`.
8. **`design-tests` and `test-designer`.** After the standard exists and after the proposals above are authored as decision records, because the design conforms to both. Then `audit-tests` consumes the sealed design and judges implementation conformance to the bound observable contracts.

### Constraints that bound every slice

No shipped skill depends on an unpublished `spx` capability. Author and auditor consume one loadable standard. Routing stays acyclic. Every changed skill surface passes the typed skill auditor in an isolated context. Each touched plugin bumps once per branch. Generated trees are rebuilt, never hand-edited.

## Decomposition disposition — the superset is a deliberate single node

`test-verification.md` carries roughly 24 Compliance assertions, well past the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md:ALWAYS:1`. This is the intended shape, not carried-forward duplication: the node is the single language-neutral **superset** of the test-evidence seam rules, and every language test-standard node cites it and declares only its language delta. Decomposing the superset into per-concern child nodes would re-fragment the exact union the design unifies, and language nodes would then cite a parent whose rules are spread across children — reintroducing the cross-language drift the superset removes. The count is a consequence of consolidating three languages' rules into one owner, so the decomposition signal is dispositioned as accepted here rather than acted on.
