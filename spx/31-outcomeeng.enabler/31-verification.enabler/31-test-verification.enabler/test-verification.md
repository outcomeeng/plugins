# Test Verification

PROVIDES Outcome Engineering governance for deterministic test evidence, test-infrastructure ownership, property-test reproducibility, and full-chain test-evidence audits
SO THAT methodology tests, plugin tests, runtime validation, and language-specific test standards
CAN prove spec assertions through source-coupled evidence without laundering domain truth through test files or helper modules

## Assertions

### Compliance

- ALWAYS: harness, generator, fixture, source-contract, and full-chain audit semantics derive from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([audit])
- ALWAYS: executed test files contain assertion flow only; values, expected outputs, reusable cases, property-test settings, setup policy, and lifecycle policy live in source contracts, spec-governed harnesses, spec-governed generators, inert whole-payload fixtures, or curated eval cases when generation is wasteful and not tractable ([audit])
- ALWAYS: property-based tests run through spec-governed harnesses that own seed selection, run count, replay input, and failure diagnostics so a failing property run is reproducible from the reported evidence ([audit])
- ALWAYS: language-specific test standards derive their file-to-file guidance for harnesses, generators, fixtures, source contracts, and property-test replay from this node and cite the governing methodology decision by full path ([audit])
- ALWAYS: test-evidence approval requires inspection of the executed test file and every imported or referenced test-infrastructure artifact, with every finding naming the exact artifact and affected evidence property ([audit])
- ALWAYS: test design decomposes every assertion into independently falsifiable clauses and records, for each clause, the exercised path, observable result, independent oracle, and a mutation under which the clause is false; evidence is stable only when every clause has a failing mutation ([audit])
- ALWAYS: test authoring and repair require an assertion-to-evidence matrix that records every assertion's type, verification lane, linked evidence file, language-standard evidence form, type-specific obligations, coupling path, falsifying mutations, and assertion-relevant source branches; no assertion proceeds from a partial matrix ([audit])
- ALWAYS: evidence that proves only a subpart of an assertion remains unstable until a full-chain distrust pass covers every clause, linked test, harness, generator, fixture, source contract, oracle, and assertion-relevant implementation path; repair and audit gates accept only stable evidence ([audit])
- ALWAYS: rejected test evidence requires complete assertion-level evidence design and a same-class sweep; predicate changes accept only that complete design, and concrete findings require no operator input while the governing assertion and source contracts determine the repair ([audit])
- NEVER: a test file declaration, variable binding, fixture parameter, property-generated parameter, or renamed constant changes ownership; the audit still routes the owned value or configuration to the proper source, harness, generator, fixture, or eval case ([audit])
