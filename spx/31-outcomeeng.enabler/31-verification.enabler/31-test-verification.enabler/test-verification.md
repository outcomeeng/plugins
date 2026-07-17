# Test Verification

PROVIDES Outcome Engineering governance for deterministic test evidence, test-infrastructure ownership, property-test reproducibility, and full-chain test-evidence audits
SO THAT methodology tests, plugin tests, runtime validation, and language-specific test standards
CAN prove spec assertions through source-coupled evidence without laundering domain truth through test files or helper modules

## Assertions

### Compliance

- ALWAYS: harness, generator, fixture, source-contract, and full-chain audit semantics derive from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([audit])
- ALWAYS: the executed test function or a callback lexically authored in the executed test file owns the predicate and every assertion-framework call that decides the verdict; a harness exposes context and observations without asserting or accepting an expected outcome on the test's behalf ([audit])
- ALWAYS: harnesses own resources, access, lifecycle, cleanup, diagnostics, property-run configuration, and controlled doubles outside the assertion boundary; generators own variable domains and independently construction-derived expectations; fixtures remain inert whole-payload inputs ([audit])
- ALWAYS: test-file declarations are judged by the choice they own rather than their syntax; parameters, destructuring bindings, and result aliases are valid when they merely name supplied values, while bindings that choose domain members, expected outcomes, protocol vocabulary, reusable cases, setup or lifecycle policy, runner settings, seeds, retries, or verdict rules move to the owning source contract, generator, fixture, harness, or eval case ([audit])
- ALWAYS: property-based tests run through spec-governed harnesses that own seed selection, run count, replay input, and failure diagnostics so a failing property run is reproducible from the reported evidence ([audit])
- ALWAYS: language-specific test standards derive their file-to-file guidance for harnesses, generators, fixtures, source contracts, and property-test replay from this node and cite the governing methodology decision by full path ([audit])
- ALWAYS: test-evidence audits inspect the executed test file and every imported or referenced test-infrastructure artifact before approving evidence, naming the exact artifact and evidence property affected by any finding ([audit])
- NEVER: a harness, generator, fixture, or shared test module calls assertions or decides an executed test's predicate — delegated assertions are relocated test logic ([audit])
- NEVER: the presence of a variable, constant, fixture parameter, property-generated parameter, destructuring binding, or result alias alone determines ownership or rejection ([audit])
