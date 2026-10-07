---
title: "[Title naming the intended Output]"
product: "[Exactly one configured Product]"
maturity: Proposed
lifecycle: Available
refined_from: []
blocked_by: []
---

<!-- Use skill `spec-tree:change-standards`. Apply it for the selected Maturity. The closed schema permits exactly the six keys above. A root keeps refined_from: []; a successor carries every immutable predecessor identity. blocked_by carries current blockers. Replace placeholders and remove every comment before audit. Keep the sections in the order below and remove each section the Maturity does not yet require; at Proposed, ## Decisions may hold the open questions. Never paste received conversation input into the record. Never write attestation, accountable-person, priority, or overrule text. -->

## Intent

- **What:** [The decision or spec evolution, lower-layer reconciliation, or combination this Change achieves.]
- **Why:** [The established reason the work is worth doing: truth brought to a lower layer, an operator judgment, a prototype question, or an Output and the condition it moves.]
- **Observation:** [Optional: the observed state that gives rise to the Change. Remove this line when no observation exists.]
- **Evidence:** [The observable result by which anyone checks that the Output is achieved.]

## Nodes

[At Framed or later: one row per affected or intended Node. A target malleability that differs from the Node's declared malleability also names the declared value. From Executable, add every other Node the changeset touches and state each Node's required state.]

| Node                   | Target malleability                       | Required state                                   |
| ---------------------- | ----------------------------------------- | ------------------------------------------------ |
| `spx/[full node path]` | `[spec, verification, or implementation]` | [From Executable: the state the Change requires] |

## Assertion operations

[At Framed or later: each addition, amendment, or removal of an assertion or decision rule, by owning Node or decision record and exact target.]

## Decisions

[At Proposed: each known question that can change the intended Output, unanswered. From Framed: each such question with its answer, and each consequential Decision for the changeset from Executable.]

## Slice

[From Sliced: the one repository, the one vertical slice, and its observable check.]

## Activities

[At Executable: the ordered execution plan. Each Activity names one result on one Node and the round that produces it.]

- [ ] [Meaningful next result with its Node, the round that produces it, and its dependency.]

<!-- Keep verification runs, command logs, cost estimates, resource accounting, and session narrative outside the Change. -->
