# Audit Tests

PROVIDES an audit methodology for deciding whether tests supply behavior-coupled evidence for spec assertions
SO THAT artifact-type test auditors across delivery plugins and language surfaces
CAN reject phantom evidence while preserving the ownership boundary between executed tests and test infrastructure

## Audit Model

The audit checks testability before evidence quality. Source code that hides assertion-relevant behavior behind opaque internals cannot be evidenced by any test. A testability finding targets the source; coupling, falsifiability, alignment, and coverage findings target the test or the imported infrastructure artifact that weakens the evidence.

When testability passes, the audit checks four evidence properties in order:

1. **Coupling** — the test exercises the codebase behavior directly, through a harness, or through a legitimate transitive surface.
2. **Falsifiability** — a concrete breaking change to the implementation causes the test to fail.
3. **Alignment** — the test verifies the spec assertion rather than adjacent behavior.
4. **Coverage** — reading the call path shows execution reaches the assertion-relevant behavior.

A test missing any property has zero evidentiary value.

## Coupling Boundaries

Direct and legitimate harness-mediated coupling proceed to falsifiability. A test has no acceptable coupling when it imports only its framework, imports a module without exercising the assertion-relevant path, replaces the asserted behavior with a mock or fake, or reads authored prose and asserts on that text. Controlled doubles remain valid for dependencies outside the behavior the assertion claims to verify.

Coverage is established by reading the test against the behavior path. Deterministic coverage measurement belongs to the caller and CI under `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`; an agentic evidence audit does not rerun the project test or coverage command.

## Value Ownership and Assertion Placement

A test launders coupling when it chooses source-owned protocol vocabulary, a domain member, or an expected outcome locally and then asserts against that choice as though the source owned it. Literal syntax is one signal. Universal sentinels, descriptive callsites, and transient aliases for supplied or observed values choose no domain or evidence policy by themselves.

Source contracts own protocol vocabulary and domain truth. Generators own variable domains and expected values independently derived from generated construction. Fixtures remain inert whole-payload inputs. Harnesses own resources, access, lifecycle, diagnostics, property-run configuration, and controlled doubles outside the assertion boundary.

The executed test function or a callback lexically authored in the executed test file owns the predicate and every assertion-framework call that decides the verdict. A harness may establish context, invoke real behavior, return observations, or pass observations into the test-owned callback. A harness that calls assertion APIs, accepts expected outcomes, or otherwise decides the verdict contains relocated test logic.

Declarations are audited by the semantic choice they make. A framework fixture parameter, property-generated parameter, destructuring binding, or result alias is valid when it merely names a supplied value. A binding that chooses domain data, expected outcomes, protocol vocabulary, reusable cases, setup or lifecycle policy, runner settings, seeds, retries, or verdict rules belongs in the corresponding source contract, generator, fixture, harness, or curated eval case.

## Assertions

### Compliance

- ALWAYS: test-evidence audits derive test-infrastructure category semantics and ownership boundaries from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([audit])
- ALWAYS: check testability before coupling and target an untestable-source finding at the source artifact ([audit])
- ALWAYS: inspect the executed test and every imported or referenced harness, generator, fixture, and production artifact before approving evidence ([audit])
- ALWAYS: establish falsifiability by naming a concrete implementation mutation that makes the test fail and establish coverage by tracing the assertion-relevant call path ([audit])
- ALWAYS: trace each executed-test binding to the semantic choice it owns, permitting transient parameters and result aliases while routing domain, oracle, vocabulary, reusable-case, lifecycle, setup, and runner-policy choices to their proper owner ([audit])
- ALWAYS: require the executed test function or a callback lexically authored in the executed test file to own the predicate and every assertion-framework call; reject harness-delegated assertion flow as relocated test logic ([audit])
- ALWAYS: reject tests with no codebase coupling, tests that replace the asserted behavior, and tests whose evidence reads authored prose rather than executable behavior ([audit])
- ALWAYS: findings name the exact source, test, or infrastructure artifact and the affected evidence property ([audit])
- NEVER: reject a variable, constant, fixture parameter, property-generated parameter, destructuring binding, or result alias solely because the declaration appears in an executed test file ([audit])
- NEVER: accept static-literal fixture modules, constant-only generators, or harness-owned expected outcomes as valid origins for domain truth ([audit])
- NEVER: run deterministic tests, coverage, validation, or eval commands inside the agentic test-evidence audit ([audit])
