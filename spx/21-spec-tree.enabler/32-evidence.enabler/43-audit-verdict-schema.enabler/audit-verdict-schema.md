# Audit Verdict Schema

PROVIDES the shared XML schema that formalizes audit verdict documents
SO THAT audit-producing skills and the verdict-validating CLI subcommand
CAN agree on a single machine-checkable contract

The schema file lives at [references/audit-verdict.xsd](references/audit-verdict.xsd). The schema is the authority for verdict structure; every audit skill producing verdicts references this file, and the `spx` verdict-validation subcommand applies this file as the structural check. A golden well-formed example and a malformed-example fixture live in [references/fixtures/](references/fixtures/) and pair with the test assertions below.

## Responsibilities

Three layers of structural rule, split by who enforces each:

| Rule class                                                                                                     | Enforced by                           |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Element presence, element ordering, attribute presence, attribute-value enumerations, simple-type restrictions | `audit-verdict.xsd` at parse time     |
| Count attribute on a finding container matches the number of finding children                                  | `audit-verdict.xsd` (XSD 1.1 asserts) |
| Cross-gate coherence (e.g. verdict `APPROVED` requires every gate status to be `PASS`)                         | Post-schema validator code            |

XSD 1.1 is required for the count assertions. The schema declares `vc:minVersion="1.1"` and the validator uses an XSD 1.1 capable processor (lxml with the appropriate schema loader).

## Structural summary

The schema constrains the following shape:

- `<audit_verdict>` root with `<header>` and `<gates>` children
- `<header>` with `<spec_node>`, `<verdict>` (`APPROVED` or `REJECT`), `<timestamp>` (ISO 8601)
- `<gates>` containing exactly three `<gate>` elements with `id` attributes `0`, `1`, `2`
- Each `<gate>` has `status` attribute (`PASS` / `FAIL` / `SKIPPED`) and, when `SKIPPED`, a non-empty `<skipped_reason>`
- Gate-specific content:
  - Gate 0 (`deterministic`): `<findings count="N">` with `<finding>` children carrying `<file>`, `<line>`, `<check_id>`, `<message>`
  - Gate 1 (`assertion`): `<assertions>` with `<assertion>` children carrying `<spec_file>`, `<assertion_text>`, `<assertion_type>`, `<test_file>`, per-assertion `<verdict>`, and optional step-scoped findings
  - Gate 2 (`architectural`): `<patterns>` with `<pattern>` children carrying a descriptive pattern name, at least two `<occurrence>` entries, and an `<extraction_target>`

Distinct element names per gate (`<findings>` vs `<assertions>` vs `<patterns>`) avoid polymorphic-content discrimination in the schema and make the document self-describing.

## Assertions

### Scenarios

- Given a well-formed verdict conforming to the schema, when validated against `references/audit-verdict.xsd`, then validation succeeds ([test](tests/test_audit_verdict_schema.unit.py))
- Given a verdict missing the `<header>` element, when validated, then validation fails with an error naming `header` ([test](tests/test_audit_verdict_schema.unit.py))
- Given a verdict with two `<gate>` children instead of three, when validated, then validation fails ([test](tests/test_audit_verdict_schema.unit.py))
- Given a gate with `status="SKIPPED"` and no `<skipped_reason>`, when validated, then validation fails ([test](tests/test_audit_verdict_schema.unit.py))
- Given a gate 0 `<findings count="3">` containing two `<finding>` children, when validated, then validation fails with a count-mismatch error ([test](tests/test_audit_verdict_schema.unit.py))
- Given a gate 2 `<pattern>` with a single `<occurrence>` child, when validated, then validation fails because patterns require at least two occurrences ([test](tests/test_audit_verdict_schema.unit.py))
- Given a verdict with `<verdict>APPROVED</verdict>` and any `<gate status="FAIL">`, when validated by the post-schema coherence check, then validation fails ([test](tests/test_audit_verdict_schema.unit.py))

### Mappings

- `<gate status>` accepts exactly `PASS`, `FAIL`, `SKIPPED` — any other value fails validation ([test](tests/test_audit_verdict_schema.unit.py))
- `<verdict>` element content accepts exactly `APPROVED`, `REJECT` — any other value fails validation ([test](tests/test_audit_verdict_schema.unit.py))
- `<assertion_type>` accepts exactly `Scenario`, `Mapping`, `Conformance`, `Property`, `Compliance` — any other value fails validation ([test](tests/test_audit_verdict_schema.unit.py))
- Gate 1 finding `<step>` accepts exactly `challenge`, `scope`, `evidence`, `mocks`, `oracle`, `harness_chain`, `coupling`, `falsifiability`, `alignment`, `coverage` — any other value fails validation ([test](tests/test_audit_verdict_schema.unit.py))

### Conformance

- The schema file at `references/audit-verdict.xsd` conforms to the W3C XML Schema 1.1 Structures specification ([test](tests/test_audit_verdict_schema.unit.py))

### Compliance

- ALWAYS: the schema file is the single source of truth for verdict structure — audit skills reference this schema rather than copying or paraphrasing it ([review])
- ALWAYS: structural rules expressible in XSD live in the schema file; cross-gate coherence rules that XSD 1.1 cannot express live in the validator code — the schema is the contract, the validator is its runtime ([review])
- NEVER: schema changes happen without corresponding updates to every audit skill producing verdicts under this schema — breaking the schema without updating producers silently breaks downstream audits ([review])
- NEVER: a verdict emitted by any audit skill contains elements or attributes not declared in the schema — unknown extensions defeat the deterministic-contract property ([review])
