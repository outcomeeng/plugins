# Test Infrastructure Auditing

PROVIDES TypeScript test-audit rules for test-infrastructure modules (harnesses, generators, inert fixtures) imported by tests
SO THAT TypeScript test auditors
CAN catch severed coupling, generator laundering, and fixture laundering outside the visible test file

## Assertions

### Compliance

- ALWAYS: TypeScript test audits trace imports from `@testing/harnesses/*`, `@testing/generators/*`, and `@testing/fixtures/*` before approving an assertion — test-infrastructure modules participate in evidence quality ([audit])
- ALWAYS: TypeScript test audits reject local test-adjacent modules that carry harness, generator, or fixture behavior outside the canonical `@testing/` path — `spx/<node>/tests/` contains typed assertion files only ([audit])
- ALWAYS: audit of a generator checks whether it represents a variable input domain with meaningful variation, composition, or shrinkage — property-shaped examples do not satisfy property evidence ([audit])
- ALWAYS: audit of a generator rejects arbitrary literals, duplicated source vocabulary, and constant-only wrappers for source-owned singleton shapes — generator modules cannot launder values out of the test file ([audit])
- ALWAYS: audit of a harness checks setup paths for framework mocks, network fakes, environment stubs, and other replacement mechanisms that hide the behavior under test — indirect coupling still needs real behavior ([audit])
- ALWAYS: TypeScript test audits reject an imported harness, generator, fixture, or controlled collaborator that itself calls `expect`, an assertion API, or a matcher, accepts an expected outcome, or returns a boolean verdict for the linked test's predicate — predicate leakage into infrastructure severs the predicate seam the executed test owns, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` ([audit])
- ALWAYS: audit of property-based test infrastructure checks that seed selection, run counts, replay diagnostics, and failure output live in a harness and that failures expose the seed needed for reproduction ([audit])
- ALWAYS: audit of a fixture checks that the fixture is a real-world payload whose complete shape matters to the assertion — isolated strings and numbers belong in source contracts or generators ([audit])
- ALWAYS: audit rejects imports from fixture modules in executed TypeScript tests — fixtures are inert file inputs read, copied, or passed by path, never sources of exports consumed by the test runner ([audit])
- ALWAYS: test-infrastructure findings identify the exact test-infrastructure file and the evidence property affected, such as source ownership, coupling, falsifiability, domain variation, oracle independence, cleanup safety, or coverage — review output names the evidence failure, not only the artifact path ([audit])
- NEVER: approve a test because the test file itself has no literals or mocks when imported test-infrastructure modules contain the defect — evidence includes the full test-infrastructure chain ([audit])
- ALWAYS: TypeScript test audits judge each executed-test binding by what it chooses — accepting a `const`, `let`, `var`, framework fixture parameter, or property-generated parameter that only renames an observation, source contract, generated value, harness handle, or fixture path, and rejecting one that chooses a case, expected result, configuration, setup policy, generator domain, fixture content, or verdict rule, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` ([audit])
