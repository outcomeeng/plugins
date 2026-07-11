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
- ALWAYS: test-evidence audits inspect the executed test file and every imported or referenced test-infrastructure artifact before approving evidence, naming the exact artifact and evidence property affected by any finding ([audit])
- ALWAYS: test design decomposes every assertion into independently falsifiable clauses and records, for each clause, the exercised path, observable result, independent oracle, and a mutation under which the clause is false; evidence is stable only when every clause has a failing mutation ([audit])
- ALWAYS: evidence that proves only a subpart of an assertion triggers a full-chain distrust pass over every clause, linked test, harness, generator, fixture, source contract, oracle, and assertion-relevant implementation path before any repair or audit rerun ([audit])
- ALWAYS: repairing rejected test evidence repeats the complete assertion-level evidence design and same-class sweep before changing predicates; a concrete audit rejection does not require operator input while the governing assertion and source contracts determine a repair ([audit])
- NEVER: a test file declaration, variable binding, fixture parameter, property-generated parameter, or renamed constant changes ownership; the audit still routes the owned value or configuration to the proper source, harness, generator, fixture, or eval case ([audit])
