---
title: "[Title naming the intended Output, at most 15 words]"
product: "[The one owning Product, or omit the value for a root spanning Products]"
maturity: Executable
lifecycle: Available
refined_from: []
blocked_by: []
parent: null
---

<!-- Use skill `spec-tree:change-standards`. Apply it for this Maturity. The closed schema permits exactly the seven keys above. refined_from lists the Changes this Change absorbed by a merge and stays [] for a Change that absorbed none. parent names the Parent Change in the same store, or null. blocked_by carries current blockers. Replace placeholders and remove every comment before audit. Keep the sections in the order below. Never paste received conversation input into the record. Never write attestation, accountable-person, priority, or overrule text. -->

## Intent

- **What:** [The decision or spec evolution, lower-layer reconciliation, or combination this Change achieves. One to three sentences.]
- **Why:** [The established reason the work is worth doing: truth brought to a lower layer, an operator judgment, a prototype question, or an Output and the condition it moves. One to three sentences.]
- **Observation:** [Optional: the observed state that gives rise to the Change. Remove this line when no observation exists. One to three sentences.]
- **Evidence:** [The observable result by which anyone checks that the Output is achieved. One to three sentences.]

## Nodes

<!-- A Leaf carries Nodes; a Parent carries neither this section nor Assertion operations. -->

| Node                   | Malleability before                                                 | Malleability after                        | Required state                  |
| ---------------------- | ------------------------------------------------------------------- | ----------------------------------------- | ------------------------------- |
| `spx/[full node path]` | `[spec, verification, or implementation; empty for a created Node]` | `[spec, verification, or implementation]` | [The state the Change requires] |

## Assertion operations

[Each addition, amendment, or removal of an assertion or decision rule, by owning Node or decision record and exact target.]

## Decisions

<!-- At most 12 rows; each answer at most two sentences. -->

- [Each question that can change the intended Output? Its answer.]

## Mutations

<!-- Rows stand in execution order, providers first. -->

**Repository:** [The one repository.]

**Observable check:** [The one observable check of the slice.]

| Node                   | Transition                  | Results and producers                                                                                                         |
| ---------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `spx/[full node path]` | [add, modify, or implement] | [Each result the merge composition selects for the Node, with its producer; the audit of each decision record the Node owns.] |

## Artifacts

<!-- Leave this section empty until a round returns audited content. Then the revision adds one link per Node the Change adds, modifies, or implements, pinned to the commit that holds the content so it resolves in every execution environment. A new decision's content links the comment that holds it on the Change's issue until it merges. Remove this comment before audit. -->
