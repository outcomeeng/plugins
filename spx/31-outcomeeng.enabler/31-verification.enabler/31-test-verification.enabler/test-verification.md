# Test Verification

PROVIDES Outcome Engineering governance for deterministic test evidence, test-infrastructure ownership, property-test reproducibility, and full-chain test-evidence audits
SO THAT methodology tests, plugin tests, runtime validation, and language-specific test standards
CAN prove spec assertions through source-coupled evidence without laundering domain truth through test files or helper modules

## Assertions

### Compliance

- ALWAYS: harness, generator, fixture, source-contract, and full-chain audit semantics derive from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([audit])
- ALWAYS: the linked executed test owns every behavioral predicate and assertion API call; harnesses establish context, execute real behavior, and expose observations or resource handles without accepting expectations, returning verdicts, or calling assertion APIs ([audit])
- ALWAYS: judge test-file bindings by semantic choice — observation and handle aliases are valid when they introduce no data or policy, while values, expected outputs, reusable cases, property-test settings, setup policy, lifecycle policy, and verdict rules live in source contracts, spec-governed harnesses, spec-governed generators, inert whole-payload fixtures, or curated eval cases when generation is wasteful and not tractable ([audit])
- ALWAYS: property-based tests run through spec-governed harnesses that own seed selection, run count, replay input, and failure diagnostics so a failing property run is reproducible from the reported evidence ([audit])
- ALWAYS: a language-specific test-standard spec node cites this node and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` by full path and declares only its language delta — the assertion API, binding forms, generator libraries, test-infrastructure home, and runner specifics for that language — never restating the language-neutral seam rules those two artifacts already own ([audit])
- ALWAYS: test-evidence audits inspect the executed test file and every imported or referenced test-infrastructure artifact before approving evidence, naming the exact artifact and evidence property affected by any finding ([audit])
- ALWAYS: scenario, mapping, property, conformance, and compliance evidence use assertion-type-appropriate case provenance and an oracle independent of the implementation path under test; predicate inversion changes only the linked test and production mutation makes the evidence fail ([audit])
- NEVER: a harness, generator, fixture, controlled implementation, or recording collaborator encodes the linked test's predicate through an expected-value parameter, boolean verdict, assertion call, matcher, or verdict-shaped helper ([audit])
