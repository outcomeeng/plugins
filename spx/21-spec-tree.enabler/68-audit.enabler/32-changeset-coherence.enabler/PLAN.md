# Plan: Changeset Coherence

## Assertion count against the decomposition trigger

The Compliance section holds eleven assertions, above the guideline that a node carrying more than about seven assertions is a decomposition candidate. The node stays whole because its single enables statement covers every assertion and the assertions are tightly coupled: the terminal statuses, the cluster partition, the collapse ordering, the evidence boundaries, and the sealed audit run that records them are one classification contract, and the eval suite scores them as one producer. Splitting them yields children whose assertions cannot be verified apart from each other.

The decomposition guideline's other trigger — a coordination note carrying structure intent — does not apply: this file carries no child-node boundary.

Re-evaluate when the node gains an assertion that does not belong to the classification contract, or when the run-recording contract separates from the classification contract.

## Generated-source evidence from the committed declaration

`changeset-coherence.md` and the shipped `src/plugins/spec-tree/skills/audit-changeset-coherence/SKILL.md` require declared generated-source relationship evidence without naming `spx/local/generated-sources.toml` or citing `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`, which settles that declaration. Pending: resolve generated-source evidence from the declaration and add the citation — plugin-distribution work (skill edit, version bump, skill-audit gate) tracked with the other consumer migrations in `spx/31-outcomeeng.enabler/31-verification.enabler/PLAN.md`.
