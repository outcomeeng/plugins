# Evidence

PROVIDES the test evidence lifecycle — writing tests from spec assertions, auditing evidence quality, and managing quality gate scope
SO THAT all spec-tree projects
CAN verify that spec assertions are fulfilled by genuine test evidence rather than phantom green CI

## Assertions

### Compliance

- ALWAYS: check four evidence properties in order (coupling, falsifiability, alignment, coverage) — a test missing any property has zero evidentiary value ([review])
- ALWAYS: `/testing` is the single authority that selects an assertion's evidence mode — one of scenario, mapping, conformance, property, compliance — from the shape of the claim it proves ([review])
- NEVER: exclude specified nodes from linting — style is checked regardless of implementation existence ([review])
- NEVER: infer an evidence mode from the section a rule appears in — a MUST/NEVER rule under a `## Compliance` heading does not imply `compliance` evidence; the mode follows the claim's shape ([review])
