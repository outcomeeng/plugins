# Test Infrastructure Auditing

PROVIDES Python test-audit rules for test-infrastructure modules imported by tests
SO THAT Python test auditors
CAN catch severed coupling, generator laundering, pytest-fixture laundering, and fixture-file laundering outside the visible test file

## Assertions

### Compliance

- ALWAYS: Python test audits trace imports from `product_testing.harnesses.*`, `product_testing.generators.*`, and inert fixture path providers before approving an assertion — test-infrastructure modules participate in evidence quality ([audit])
- ALWAYS: Python test audits inspect `conftest.py` files that affect the test under review and verify they only import explicit pytest fixture callables from canonical `product_testing.harnesses.*` modules or register pytest metadata — `conftest.py` is not a home for fixture body code ([audit])
- ALWAYS: Python test audits reject local test-adjacent modules that carry harness, generator, pytest fixture, or fixture-file behavior outside the canonical `product_testing/` package — `spx/<node>/tests/` contains typed assertion files only ([audit])
- ALWAYS: audit of a generator checks whether it represents a variable input domain with meaningful variation, composition, or shrinkage — property-shaped examples do not satisfy property evidence ([audit])
- ALWAYS: audit of a generator rejects arbitrary literals, duplicated source vocabulary, and constant-only wrappers for source-owned singleton shapes — generator modules cannot launder values out of the test file ([audit])
- ALWAYS: audit of a harness checks setup paths for framework mocks, monkeypatches, network fakes, environment stubs, `sys.path` manipulation, and other replacement mechanisms that hide the behavior under test — indirect coupling still needs real behavior ([audit])
- ALWAYS: audit of an inert fixture checks that the fixture is a real-world payload whose complete shape matters to the assertion — isolated strings and numbers belong in source contracts or generators ([audit])
- ALWAYS: audit rejects imports from inert fixture files in executed Python tests — fixtures are inert file inputs read, copied, or passed by path, never sources of exports consumed by the test runner ([audit])
- ALWAYS: test-infrastructure findings identify the exact test-infrastructure file and the evidence property affected, such as source ownership, coupling, falsifiability, domain variation, oracle independence, cleanup safety, pytest discovery safety, or coverage — review output names the evidence failure, not only the artifact path ([audit])
- NEVER: approve a test because the test file itself has no literals or mocks when imported test-infrastructure modules contain the defect — evidence includes the full test-infrastructure chain ([audit])
