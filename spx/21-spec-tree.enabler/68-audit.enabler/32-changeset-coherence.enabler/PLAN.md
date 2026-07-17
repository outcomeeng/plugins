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
