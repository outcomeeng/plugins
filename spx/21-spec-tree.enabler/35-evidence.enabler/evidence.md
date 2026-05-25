# Evidence

PROVIDES the test evidence lifecycle — writing tests from spec assertions, auditing evidence quality, and managing quality gate scope
SO THAT all spec-tree projects
CAN verify that spec assertions are fulfilled by genuine test evidence rather than phantom green CI

## Assertions

### Compliance

- ALWAYS: check four evidence properties in order (coupling, falsifiability, alignment, coverage) — a test missing any property has zero evidentiary value ([review])
- NEVER: exclude specified nodes from linting — style is checked regardless of implementation existence ([review])
