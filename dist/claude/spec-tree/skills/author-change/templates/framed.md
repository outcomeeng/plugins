---
title: "[Title naming the intended Output, at most 15 words]"
product: "[The one Product that owns the Output, or omit the value for a root spanning Products]"
maturity: Framed
lifecycle: Available
refined_from: []
blocked_by: []
parent: null
---

<!-- Use skill `spec-tree:change-standards`. Apply it for this Maturity. The closed schema permits exactly the seven keys above. refined_from lists the Changes this Change absorbed by a merge and stays [] for a Change that absorbed none. parent names the Parent Change in the same store, or null. blocked_by carries current blockers. Replace placeholders and remove every comment before audit. Keep the sections in the order below. Never paste received conversation input into the record. Never write attestation, accountable-person, priority, or overrule text. -->

## Intent

<!-- At most 60 words in all, labels included. A list inside a part stands in parentheses. -->

- **What:** [The decision or spec evolution, lower-layer reconciliation, or combination this Change achieves.]
- **Why:** [The established reason the work is worth doing: truth brought to a lower layer, an operator judgment, a prototype question, or an Output and the condition it moves.]
- **Observation:** [Optional: the observed state that gives rise to the Change. Remove this line when no observation exists.]
- **Evidence:** [The observable result by which anyone checks that the Output is achieved.]

## Governance

<!-- A Leaf lists every record that governs the Change. -->

- `spx/[path of the governing record]`: [in line, amended, or new]

## Governance mutations

<!-- One block for each amended or new record, in record order. A Parent carries no block. -->

`spx/[path of the amended or new record]` states:

- [slug]: [The decision in exact text.]

## Spec mutations

<!-- One block for each affected or intended Node, in execution order, providers first. A Parent carries no block. Use none for the malleability before of a Node the Change creates. -->

`spx/[full node path]`: [spec, verification, implementation, or none] -> [spec, verification, or implementation]

`[spec file name]` states:

- [The Node's assertion as it reads after the Change.]
