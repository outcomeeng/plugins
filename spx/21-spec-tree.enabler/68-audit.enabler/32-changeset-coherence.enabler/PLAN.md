# Plan: SPX verification-run persistence

The direct structured JSON verdict remains the auditor output until SPX exposes a compatible changeset-coherence audit payload and projection contract.

## Revisit gate

Resume persistence work when all conditions hold:

1. SPX follow-up session `2026-07-17_00-45-36` delivers a published changeset-coherence contract.
2. An `@outcomeeng/spx` release carrying the contract is published.
3. This repository's required SPX floor and CI pin advance to that published release.

## Work after the gate

- Replace the direct-only relay with one SPX verification run over the exact committed scope.
- Preserve `APPROVED`, `REJECTED`, and `UNKNOWN`, semantic clusters, findings, publication authorization, and the dependency-ordered review-unit sequence in the rendered projection.
- Add deterministic contract coverage and migrate the producer-coupled eval expectations without changing the semantic verdict model.

## Assertion count against the decomposition trigger

The Compliance section holds eleven assertions, above the guideline that a node carrying more than about seven assertions is a decomposition candidate. The node stays whole because its single enables statement covers every assertion and the assertions are tightly coupled: the verdict states, the cluster partition, the collapse ordering, the evidence boundaries, and the structured projection are one classification contract, and the eval suite scores them as one producer. Splitting them yields children whose assertions cannot be verified apart from each other.

The decomposition guideline's other trigger — a coordination note carrying structure intent — is this file, whose intent is the persistence migration above rather than a child-node boundary.

Re-evaluate when the node gains an assertion that does not belong to the classification contract, or when the persistence migration lands and the projection contract separates from the classification contract.

## Generated-source evidence from the committed declaration

`changeset-coherence.md` and the shipped `src/plugins/spec-tree/skills/audit-changeset-coherence/SKILL.md` require declared generated-source relationship evidence without naming `spx/local/generated-sources.toml` or citing `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`, which settles that declaration. Pending: resolve generated-source evidence from the declaration and add the citation — plugin-distribution work (skill edit, version bump, skill-audit gate) tracked with the other consumer migrations in `spx/31-outcomeeng.enabler/31-verification.enabler/PLAN.md`.
