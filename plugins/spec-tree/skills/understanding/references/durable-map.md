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
- **Specified** — spec and tests exist, but the implementation doesn't. Tests are excluded from the quality gate via `spx/EXCLUDE`. See `references/excluded-nodes.md`.
- **Failing** — spec, tests, and implementation exist, but tests fail. The implementation is in violation.
- **Passing** — spec, tests, and implementation exist, and tests pass.

Specified and failing are normal states. Specified nodes have declarations and verification ready — the implementation will follow. Failing nodes have implementations in violation — the code will be reconciled. Neither is a problem to fix urgently.

</node_states>

<common_agent_mistakes>

| Agent impulse                               | Correct response                                                         |
| ------------------------------------------- | ------------------------------------------------------------------------ |
| "Task complete, closing story"              | Nothing to close. If tests pass, the node is passing.                    |
| "Moving to done"                            | There is no done. The spec stays where it is.                            |
| "Archiving completed work"                  | Do not archive. The spec is the permanent record.                        |
| "Setting status to complete"                | Do not set status. Run tests — passing = passing.                        |
| "This spec is outdated"                     | Either it's still true (keep it) or prune it.                            |
| "Creating a new ticket for X"               | Create or edit a spec. Specs are not tickets.                            |
| "Tests fail — module not found"             | Specified node. Add it to `spx/EXCLUDE`.                                 |
| "Excluding tests is cheating"               | Exclusion is declared intent, not cheating.                              |
| "Code doesn't do X, remove the assertion"   | The declaration governs. The code is in violation.                       |
| "Tests can't prove Y, mark it aspirational" | Write the test. The declaration defines what to prove.                   |
| "Rewrite specs to match what tests prove"   | Specs derive from PDRs. Tests derive from specs. Never reverse the flow. |
| "The implementation doesn't support Z yet"  | The spec leads. Use EXCLUDE if tests would fail. Code catches up.        |

</common_agent_mistakes>
