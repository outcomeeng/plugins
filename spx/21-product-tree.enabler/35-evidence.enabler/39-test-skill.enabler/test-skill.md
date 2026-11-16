---
id: 01a0ebba-5f63-709a-9097-ebfebf5123f6
malleability: spec
---

# Test Skill

PROVIDES generic deterministic-test routing, assertion typing, execution-level selection, evidence integrity checks, and shared test workflow ceremony before language-specific expression
SO THAT `/verify`, language test skills, and test-evidence auditors
CAN construct and judge test evidence from one methodology without duplicating routing policy across languages

## Assertions

### Audit: routing and ownership

- property-real-boundary: ALWAYS: generic test guidance separates generated property evidence over product-owned variation from finite real-boundary evidence, keeps filesystem, Git, and full CLI work outside each generated case when it only supplies wiring, and preserves `l1` classification for cheap local boundary checks
- generic-owns-decisions: ALWAYS: the generic test specialist owns test assertion typing, execution-level selection, source-contract and oracle gates, evidence-property checks, exception classification, naming policy, and evidence-summary ceremony
- shared-standard: ALWAYS: test authoring and test auditing consume one independently loadable standard for coupling, falsifiability, alignment, coverage, source ownership, domain variation, oracle independence, and controlled implementations
- design-record-first: ALWAYS: test authoring stops before evidence implementation until the shared standard's assertion-design record names the assertion quantifier, observable seam, case provenance, oracle owner, rejected production mutation, and resulting failure observation; moving a value preserves its provenance
- no-language-repeat: NEVER: a language-specific test specialist owns or repeats a generic test decision

### Audit: authoring round

- foreground-commands: ALWAYS: a load-gated command `/test` runs executes in the foreground, and `/test` reports its result only after every such command has exited
- language-skill-first: ALWAYS: before its first write, a test-authoring round loads the language test skill of each language in which it creates or changes a test file, in a repair round as in a new scaffold, so that the language's standards bind every edit; a language with no installed test skill is reported with the result
- source-owner-repair: ALWAYS: when `/test` repairs a source-ownership finding, it exports the value from its production owner and replaces every spelling of that value in the node's linked tests, harnesses and generators, not only the cited line
- literal-sweep: ALWAYS: before its first audit, `/test` sweeps the evidence it authored for every literal spelling of a source-owned value and replaces each with the production owner's export
- specified-node: ALWAYS: when a Node's implementation is absent, `/test` reports its failing tests as the expected result that leaves the Node Specified, and prescribes no skip marker, conditional import, or file that keeps those tests from a runner

### Audit: assertion form

- assertion-form: ALWAYS: `/test` writes each Assertion it types under the group heading that names its assertion type, `Test.Scenario`, `Test.Conformance`, `Test.Property`, or `Test.Compliance`, or as its own `Test.Mapping:` subsection, opening the row with its slug and carrying no tag
- evidence-link: ALWAYS: once `/test` writes a test file for an Assertion, the Assertion's slug links that file, and the assertion type in the file's name matches the type the Assertion's heading names
- test-work-selection: ALWAYS: `/test` takes a spec's test work from the rows under its `Test.` headings and the slugs its invocation supplies, and reads no `[test]` tag
- decision-rule-form: ALWAYS: for a decision target, `/test` places each test rule under the group heading, or in the `Test.Mapping:` subsection, that names its assertion type, and writes no assertion-type tag and no evidence link
