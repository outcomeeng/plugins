# PDR Auditing

WE BELIEVE THAT an audit methodology verifying PDRs establish enforceable product constraints that flow into spec assertions
WILL eliminate unenforceable product decisions (compliance rules that no spec references) across all spec-tree projects
CONTRIBUTING TO product decisions that actually govern behavior rather than existing as aspirational documents

## PDR Evidence Model

The audit answers one question: **does this PDR establish product constraints that are actually enforced downstream?**

Evidence requires six properties checked in order:

1. **Content classification** — every statement is about observable product behavior, not architecture or implementation
2. **Invariant quality** — product invariants are user-observable and falsifiable
3. **Compliance quality** — MUST/NEVER rules are verifiable by product review or automated test
4. **Atemporal voice** — the PDR states product truth, not history
5. **Consistency** — the PDR does not contradict the product spec or ancestor PDRs
6. **Downstream flow** — compliance rules land in spec assertions somewhere in the governed subtree

A PDR missing any property is a declaration that nothing enforces — the product equivalent of a tautological test.

## Content Classification Model

The `/auditing-product-decisions` skill in the spec-tree plugin classifies every statement in the PDR:

| Content type                | Belongs in      | Finding if in PDR                        |
| --------------------------- | --------------- | ---------------------------------------- |
| Observable product behavior | PDR             | Correct                                  |
| User-facing guarantee       | PDR (invariant) | Correct                                  |
| Technology choice           | ADR             | REJECT — architecture content            |
| Implementation approach     | ADR or code     | REJECT — implementation content          |
| Data structure or schema    | ADR             | REJECT — architecture content            |
| Performance implementation  | ADR             | REJECT (but performance guarantee = PDR) |

The distinction: "Sessions expire after 1 hour" is product behavior (PDR). "Sessions use JWT with 1-hour TTL" is architecture (ADR). "The session table has a TTL column" is implementation (code).

## Downstream Flow Model

For each compliance rule in the PDR, the auditor searches the governed subtree for spec assertions that reference or implement the rule.

A compliance rule with no downstream assertion is an unenforced declaration — the PDR says the product must behave a certain way, but no spec asserts it and no test verifies it.

The auditor reports the flow status for each rule:

```text
PDR compliance rule: "MUST: all pages load in under 2 seconds"
Downstream: spx/.../21-performance.outcome assertions reference this PDR ✓

PDR compliance rule: "NEVER: expose internal IDs in URLs"
Downstream: no spec assertion references this rule ✗ — unenforced
```

## Assertions

### Scenarios

- Given a PDR containing architecture content ("use JWT tokens", "store in PostgreSQL"), when audited by `/auditing-product-decisions`, then the verdict is REJECT with finding category "architecture content" ([test](tests/pdr-auditing.unit.test.ts))
- Given a PDR with product invariants that are not user-observable ("database uses row-level locking"), when audited, then the verdict is REJECT with finding category "non-observable invariant" ([test](tests/pdr-auditing.unit.test.ts))
- Given a PDR with compliance rules that no spec in the governed subtree references, when audited, then the verdict is REJECT with finding category "unenforced rule" ([test](tests/pdr-auditing.unit.test.ts))
- Given a PDR with temporal language in any section, when audited, then the verdict is REJECT with finding category "temporal voice" ([test](tests/pdr-auditing.unit.test.ts))
- Given a PDR that contradicts the product spec or an ancestor PDR, when audited, then the verdict is REJECT with finding category "consistency violation" ([test](tests/pdr-auditing.unit.test.ts))
- Given a PDR where all six properties hold, when audited, then the verdict is APPROVED ([test](tests/pdr-auditing.unit.test.ts))

### Properties

- The audit methodology classifies PDR content into at least the six content types defined in the Content Classification Model — product behavior, user-facing guarantee, technology choice, implementation approach, data structure, performance implementation ([test](tests/pdr-auditing.unit.test.ts))

### Conformance

- The `/auditing-product-decisions` skill invokes `/contextualizing` on the PDR's location before any audit phase ([test](tests/pdr-auditing.unit.test.ts))

### Compliance

- ALWAYS: check content classification as the first audit phase — a PDR full of architecture content fails regardless of other properties ([review])
- ALWAYS: search the governed subtree for spec assertions referencing each compliance rule — unenforced rules are the PDR equivalent of tautological tests ([review])
- ALWAYS: verify product invariants are observable from the user's perspective, not from the implementation's perspective ([review])
- NEVER: approve a PDR whose compliance rules have zero downstream assertions — a declaration that nothing enforces is not a product decision ([review])
- NEVER: approve temporal language in any section — Context, Decision, Rationale, Trade-offs, Compliance all state product truth ([review])
