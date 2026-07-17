# Evidence

PROVIDES the test evidence lifecycle — writing tests from spec assertions, auditing evidence quality, and managing quality gate scope
SO THAT all spec-tree projects
CAN verify that spec assertions are fulfilled by genuine test evidence rather than phantom green CI

## Verification and assertion types

Every assertion is classified through three nested levels:

1. **Verdict mode** — how the verdict is produced: deterministic or agentic.
2. **Verification type** — test, evaluate, or audit, named by the tag the assertion carries (`[test]`, `[eval]`, `[audit]`). Selected by fallback: test when a deterministic test can verify the assertion, else evaluate when the producer emits a parseable structured verdict, else audit.
3. **Assertion type** — under the **test** verification type only, one of scenario, mapping, conformance, property, compliance, read from the assertion's quantifier. Evaluate and audit carry no assertion type.

`/test` (with `/test-{language}` binding the test file) is the single authority that selects the verification type and, under test, the assertion type. No decision record, template, section heading, or other skill selects either.

## Assertions

### Compliance

- ALWAYS: `/test` (with `/test-{language}`) is the single authority that selects an assertion's verification type and, under test, its assertion type — no other skill, decision record, template, or section heading selects either ([audit])
- ALWAYS: select the verification type by fallback — test when a deterministic test can verify the assertion, else evaluate when the producer emits a parseable structured verdict, else audit ([audit])
- ALWAYS: under the test verification type, select the assertion type from the assertion's quantifier — a universal (ALWAYS/NEVER/for-all) takes mapping, conformance, compliance, or property; an existential (one specific interaction) takes scenario ([audit])
- ALWAYS: check four evidence properties in order (coupling, falsifiability, alignment, coverage) — a test missing any property has zero evidentiary value ([audit])
- ALWAYS: `/test` and `/audit-tests` load one shared test-evidence standard for predicate ownership, semantic binding ownership, assertion-type case provenance, and oracle independence, so authored tests and audits apply identical rules ([audit])
- ALWAYS: the linked executed test alone owns behavioral predicates and assertion API calls; test infrastructure exposes observations and resources without encoding the expected verdict ([audit])
- NEVER: infer an assertion type from the section or heading a rule sits under — a MUST/NEVER rule under a `## Compliance` heading does not imply the compliance assertion type; the type follows the assertion's quantifier ([audit])
- NEVER: exclude specified nodes from linting — style is checked regardless of implementation existence ([audit])
