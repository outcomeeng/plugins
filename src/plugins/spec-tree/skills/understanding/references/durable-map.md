<overview>

The Spec Tree is a **durable map** — a permanent, declarative record of what the product does. Specs are not work items. They are not tickets. They do not move through a pipeline.

**Specs declare. Tests derive from specs. Code derives from tests. When layers disagree, the lower layer is in violation.**

</overview>

<truth_hierarchy>

The Spec Tree has four layers. Each layer depends on the one above it.

```text
PDR/ADR  →  Spec  →  Test  →  Code
governs     declares   verifies   complies
```

- **PDRs/ADRs** govern what the product does and how it is built.
- **Specs** declare product truth — assertions that describe the product's output.
- **Tests** verify that assertions hold — they are the executable form of the declaration.
- **Code** complies with tests — it exists to pass them.

When any two layers disagree, the lower layer is in violation. Reconcile by changing the lower layer, never by weakening the higher one.

This holds even when the code is perfectly implemented. When a PDR changes based on customer feedback, specs update, then tests update, then code updates. During that process, code is in violation. That is normal — the declaration leads, the implementation follows.

</truth_hierarchy>

<future_product_truth>

PDRs, ADRs, product specs, and ancestor specs may declare product truth before specs, tests, or code fully implement it. That is normal. A higher-level declaration creates downstream work; it does not need to be weakened to match current implementation.

When evaluating a higher-level artifact that leads implementation:

1. Preserve the declaration when the product or architecture model is coherent.
2. Identify the first lower-level specs that must absorb the declaration.
3. Distinguish declaration validity from implementation completeness.
4. Treat lower-layer mismatch as downstream work unless the PR claims the lower layer is already passing for that assertion.
5. Use node-local `PLAN.md` for concrete implementation steps that remain when tests or code are not part of the slice; a change that only aligns already-implemented truth records no plan.
6. Use node-local `ISSUES.md` for known defects, contradictions, or unresolved gaps.
7. Use `spx/EXCLUDE` only for nodes whose specs and tests exist while implementation is absent. Never use exclusion to make a PDR, ADR, product spec, or ancestor spec safe.

A current implementation shape is evidence about what code does now. It is not evidence that the higher-level declaration must describe the same shape.

</future_product_truth>

<decision_to_spec_alignment>

When a PR changes a higher-level artifact, the PR must also align the first affected lower-level specs so the declaration has an immediate path down the tree.

Minimum same-PR alignment contract:

- Product spec, PDR, or ADR change: update every directly affected child or target spec assertion that first receives the new truth.
- Ancestor spec change: update descendant specs only when the changed assertion constrains them.
- When concrete downstream implementation remains after the lower specs are aligned — tests or code this slice does not carry — add or update `PLAN.md` at the first affected lower node with the next implementation step and the higher-level artifact that created it. A change that only aligns already-implemented truth records no plan.
- `ISSUES.md` records known defects or contradictions. `PLAN.md` records pending node work.
- Do not leave a higher-level declaration floating above the tree with no lower spec or node-local plan that carries the same understanding forward.

This alignment is about declarations and coordination, not forced implementation. The first PR that declares new higher-level truth does not need to write every test or all code, but it must show where the truth enters the lower tree and where remaining work resumes.

</decision_to_spec_alignment>

<mental_model>

| Backlog thinking  | Declarative thinking         |
| ----------------- | ---------------------------- |
| Create ticket     | Declare spec                 |
| Close ticket      | Tests pass (node is passing) |
| Archive done work | Nothing moves — specs stay   |
| Assign status     | Derive state from tests      |
| Sprint velocity   | Passing rate                 |
| Groom backlog     | Prune tree                   |

</mental_model>

<declarations>

When you write a spec, you make a **declaration** — an authoritative statement of what the product does. The implementation either conforms or is in violation.

When you write tests for that spec, the declaration becomes **verifiable**. Tests are the executable form of the declaration.

When tests pass, the node is **passing**. The implementation conforms to the declaration.

When you edit a passing spec, tests may start failing. The implementation is now in violation of the new declaration. Reconcile by updating tests and code — not by reverting the spec.

When you remove a spec, you **prune** — deciding this branch no longer serves the product.

</declarations>

<atemporal_voice>

Specs state product truth. They never narrate history, never reference time, never describe a journey.

**Temporal markers to eliminate:**

| Temporal (wrong)                  | Atemporal (correct)           |
| --------------------------------- | ----------------------------- |
| "We discovered that X"            | "X ensures Y"                 |
| "X has accumulated without Y"     | "Y prevents Z"                |
| "We need to address"              | "[Product] provides"          |
| "Currently, the system"           | "[Product] [does thing]"      |
| "After investigating, we decided" | "[Decision] governs [scope]"  |
| "This was introduced because"     | "[Feature] enables [outcome]" |
| "Over time, X became"             | "X is [state]"                |

**Test:** Read any sentence aloud. If it would sound wrong after the work is done, it's temporal.

**Why it matters:** Temporal language rots. "We currently need X" becomes false the moment X is delivered. Atemporal language is either true about the product or should be removed.

</atemporal_voice>

<prohibited_operations>

These operations do not exist in the Spec Tree:

- **Close** a spec — Specs declare product truth. Truth isn't closed.
- **Move** a spec to "done" — There is no done. The spec stays where it is.
- **Archive** a spec — If it's true, it stays. If it's no longer true, prune it.
- **Assign status** — Status is derived from tests, not set by a human or agent.
- **Mark as complete** — Completion is proven by tests passing.
- **Weaken a spec** to match code — The spec declares. The code complies.

</prohibited_operations>

<node_states>

A node's state is derived from its spec and tests:

- **Declared** — spec exists, no tests. The declaration stands, but nothing verifies it yet.
- **Specified** — spec and tests exist, but the implementation doesn't. The node is listed in `spx/EXCLUDE`; the `spx` CLI skips it when running `spx test passing`. See `references/excluded-nodes.md`.
- **Failing** — spec, tests, and implementation exist, but tests fail. The implementation is in violation.
- **Passing** — spec, tests, and implementation exist, and tests pass.

Specified and failing are normal states. Specified nodes have declarations and verification ready — the implementation will follow. Failing nodes have implementations in violation — the code will be reconciled. Neither is a problem to fix urgently.

</node_states>

<common_agent_mistakes>

| Agent impulse                               | Correct response                                                              |
| ------------------------------------------- | ----------------------------------------------------------------------------- |
| "Task complete, closing story"              | Nothing to close. If tests pass, the node is passing.                         |
| "Moving to done"                            | There is no done. The spec stays where it is.                                 |
| "Archiving completed work"                  | Do not archive. The spec is the permanent record.                             |
| "Setting status to complete"                | Do not set status. Run tests — passing = passing.                             |
| "This spec is outdated"                     | Either it's still true (keep it) or prune it.                                 |
| "Creating a new ticket for X"               | Create or edit a spec. Specs are not tickets.                                 |
| "Tests fail — module not found"             | Specified node. Add it to `spx/EXCLUDE`.                                      |
| "Excluding tests is cheating"               | Exclusion is declared intent, not cheating.                                   |
| "Code doesn't do X, remove the assertion"   | The declaration governs. The code is in violation.                            |
| "Tests can't prove Y, mark it aspirational" | Write the test. The declaration defines what to prove.                        |
| "Rewrite specs to match what tests prove"   | Specs derive from PDRs. Tests derive from specs. Never reverse the flow.      |
| "The implementation doesn't support Z yet"  | The spec leads. Use EXCLUDE if tests would fail. Code catches up.             |
| "The decision is ahead of implementation"   | Align the first affected lower specs and record pending node work in PLAN.md. |

</common_agent_mistakes>

<failure_modes>

**Failure 1: An agent shaped a PDR to current implementation**

What happened: The agent reviewed a PDR that declared a cleaner product model than the current code and argued that the model should collapse to the current implementation shape.

Why it failed: The agent treated implementation incompleteness as evidence against the decision. Spec Tree truth flows down; a PDR can lead code and create downstream work.

How to avoid: When a decision is ahead of implementation, preserve the product truth, identify the first affected lower specs, and name the follow-on work. Challenge incoherent product taxonomy, wrong artifact placement, missing affected-spec alignment, or a PR that falsely claims lower-layer passing evidence.

**Failure 2: An agent treated missing implementation as evidence against product truth**

What happened: The agent saw that code could not express a new decision cleanly and treated the decision as over-modeled.

Why it failed: Current code shape is a lower-layer fact. It can expose implementation work, but it does not decide product truth.

How to avoid: Separate "is the declaration coherent?" from "which lower layers must catch up?" A coherent higher-level declaration stays; lower specs, tests, and code align beneath it.

**Failure 3: An agent changed a higher-level artifact without aligning lower specs**

What happened: The agent authored or edited a product spec, ADR, PDR, or ancestor spec and left the new truth only in that higher-level file.

Why it failed: Future work lost the understanding that produced the decision. The next session saw a high-level declaration with no first affected spec or node-local plan to continue from.

How to avoid: In the same PR, update the first affected lower specs. When tests or code remain pending, add `PLAN.md` at the first affected lower node with the next implementation step and the governing higher-level artifact.

**Failure 4: An agent used `spx/EXCLUDE` as a conceptual escape hatch**

What happened: The agent suggested excluding a lower node to handle a mismatch between decision truth and current implementation.

Why it failed: `spx/EXCLUDE` scopes specified tests out of the quality gate when specs and tests exist but implementation is absent. It does not resolve product-model disagreement and does not permit lower layers to contradict decisions.

How to avoid: Ask which layer owns the truth. If the PDR, ADR, product spec, or ancestor spec is coherent, lower layers catch up. Use `spx/EXCLUDE` only when there are actual node tests that would fail because implementation is absent.

</failure_modes>
