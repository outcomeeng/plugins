# Issues: Changeset coherence

## Decision-first ordering was reversed

Commit `681f12561982052dc2c6f6ab83cbfed9cb4eb6dc` created the following three artifacts together:

- `spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/15-review-unit-coherence.pdr.md`
- `spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/changeset-coherence.md`
- `spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/57-coherence-audit-orchestration.adr.md`

The mistake was treating the artifact taxonomy as a construction recipe. The phrase "semantic cohesion rather than a fixed size threshold" looked like user-observable behavior, so it was classified as a product decision. "Review-Unit Coherence" was introduced as the name of that supposed product model, "Changeset Coherence" remained the auditor capability name, and "Coherence Audit Orchestration" became the architecture name. The operator had named one changeset-coherence concern and had not established review-unit coherence as a separate product concept.

Creating the decision and spec in the same declaration commit reversed the truth hierarchy. A product decision is established before the spec it governs. The later diagnosis repeated the reversal by asking whether the PDR contained normative truth beyond the node spec and by treating the lower-layer spec as the test of whether the higher-layer decision belonged.

The decision-placement and naming ambiguity existed before authoring. `/decompose` assigns concept ownership and requires `/interview` when the boundary or decision placement is unsettled. That clarity gate was skipped, so the PDR type, the additional concept name, and the relationship between the PDR, spec, and ADR were authored without an operator-approved decision model.

The resulting node carries two names for one concern, a PDR and spec authored without decision-first ordering, and an ADR that cites the simultaneously introduced PDR as its governing product model.
