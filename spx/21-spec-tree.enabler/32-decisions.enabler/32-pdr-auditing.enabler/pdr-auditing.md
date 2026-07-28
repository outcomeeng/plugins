# PDR Auditing

PROVIDES an audit methodology verifying PDRs declare well-formed, observable product decisions
SO THAT all spec-tree projects
CAN eliminate malformed product decisions before they accumulate

## PDR Evidence Model

The audit answers one question: **is this a well-formed, observable product decision?**

Evidence requires five properties checked in order:

1. **Content classification** — every statement is about observable product behavior for the product's declared audience, not architecture or implementation
2. **Property quality** — product properties are user-observable and falsifiable
3. **Tag validity** — each verification rule carries a tag valid for its subsection, and a `### Testing` rule's assertion type fits the claim's quantifier
4. **Atemporal voice** — the PDR states product truth, not history
5. **Consistency** — the PDR does not contradict the product spec or ancestor PDRs

A PDR that fails any property is not a well-formed product decision.

## Content Classification Model

The `/audit-pdr` skill in the spec-tree plugin classifies every statement in the PDR:

| Content type                       | Belongs in     | Finding if in PDR                        |
| ---------------------------------- | -------------- | ---------------------------------------- |
| Observable product behavior        | PDR            | Correct                                  |
| Observable non-functional property | PDR (property) | Correct                                  |
| Technology choice                  | ADR            | REJECT — architecture content            |
| Implementation approach            | ADR or code    | REJECT — implementation content          |
| Data structure or schema           | ADR            | REJECT — architecture content            |
| Performance implementation         | ADR            | REJECT (but performance guarantee = PDR) |

The distinction: "Sessions expire after 1 hour" is product behavior (PDR). "Sessions use JWT with 1-hour TTL" is architecture (ADR). "The session table has a TTL column" is implementation (code).

"Observable" is grounded in the product document the audit loads, not a fixed end-user-application assumption. The product document declares the product's audience and the interaction surfaces through which that audience operates the product; content classification reads that declaration and judges each statement against it. When the audience operates the product through a command-line interface, a filesystem layout, a version-control topology, or another infrastructure surface, the CLI, filesystem, and version-control state that audience directly observes or operates is observable product behavior and belongs in the PDR. The architecture line falls at what the audience never operates: the internal algorithm by which a tool reaches an observable result, the data structures it holds in memory, the schema it persists, and the libraries or frameworks it depends on. A repository-layout decision a developer inspects on disk is product behavior; the in-memory cache the layout detector keys by path is architecture — even though both belong to the same tooling product.

## Assertions

### Scenarios

- Given a PDR containing architecture content ("use JWT tokens", "store in PostgreSQL"), when audited by `/audit-pdr`, then the verdict is REJECT with finding category "architecture-content" ([eval](evals/structure/eval.toml))
- Given a PDR for a product whose product document declares its audience operates the product through a command-line, filesystem, or version-control surface, and whose statements describe the CLI, filesystem, or version-control state that audience observes, when audited by `/audit-pdr`, then content classification passes and the statements are not rejected as architecture ([eval](evals/structure/eval.toml))
- Given a PDR whose statements describe a tool's internal algorithm, in-memory data structure, persisted schema, or library choice that the declared audience never operates, when audited by `/audit-pdr`, then the verdict is REJECT with finding category "architecture-content" even for a tooling product ([eval](evals/structure/eval.toml))
- Given a PDR with product properties that are not user-observable ("database uses row-level locking"), when audited, then the verdict is REJECT with finding category "non-observable-property" ([eval](evals/structure/eval.toml))
- Given a PDR with temporal language in any section, when audited, then the verdict is REJECT with finding category "temporal-language" ([eval](evals/voice/eval.toml))
- Given a PDR whose `### Testing` rule carries a bare mechanism tag, a tag disagreeing with its subsection, no tag, or more than one tag, when audited, then the verdict is REJECT with finding category "invalid-tag" ([eval](evals/tag-validity/eval.toml))
- Given a PDR whose `### Testing` rule tags a universal claim (ALWAYS/NEVER) as `scenario`, when audited, then the verdict is REJECT with finding category "assertion-type-mismatch" ([eval](evals/tag-validity/eval.toml))
- Given a PDR that contradicts the product spec or an ancestor PDR, when audited, then the verdict is REJECT with finding category "consistency-violation" ([eval](evals/structure/eval.toml))
- Given a PDR where all five properties hold, when audited, then the verdict is APPROVED ([eval](evals/structure/eval.toml))

### Compliance

- ALWAYS: classify every PDR statement into at least the six content types defined in the Content Classification Model — product behavior, observable non-functional property, technology choice, implementation approach, data structure, performance implementation ([audit])
- ALWAYS: ground "observable" in the product document's declared audience and interaction surfaces rather than a fixed end-user-application assumption — a statement is product behavior when that audience observes or operates it, so an audience that operates the product through a command-line, filesystem, or version-control surface makes those mechanics product behavior, while the internal algorithm, in-memory data structure, persisted schema, and library choices that audience never operates remain architecture ([audit])
- ALWAYS: invoke `/contextualize` on the PDR's location before any audit phase ([audit])
- ALWAYS: check content classification as the first audit phase — a PDR full of architecture content fails regardless of other properties ([audit])
- ALWAYS: verify product properties are observable from the user's perspective, not from the implementation's perspective ([audit])
- ALWAYS: verify each `### Testing` rule's assertion type fits the claim's quantifier per the `/test` router — a universal is never `scenario`; reject a type the router would not produce, without relitigating a choice the router leaves open ([audit])
- ALWAYS: compare the PDR against the product spec and ancestor PDRs; a contradiction with either is a consistency violation ([audit])
- NEVER: approve temporal language in any section — Decision, Rationale, Product properties, Verification all state product truth ([audit])
