# PLAN — test-auditing methodology additions

## Why

Current `/auditing-tests` workflow does not state the test-literal rule concretely, offers no positive pattern for agents to follow, and lacks a testability gate. Agents evade laundering detection by relocating literals into camelCase constant bags that escape existing casing-focused checks. Most code arriving for audit is not testable by the time tests are written, and the audit has no way to reject the source rather than the test.

## Scope

1. **Literal rule — state at gate, coupling, falsifiability, and rejection criteria.**
   - Numbers: only `-1, 0, 1, 2` allowed as bare literals. Any other number must come from a library/platform origin, a production-owned constant object, or a generator (fast-check / faker / hypothesis / harness function that produces values at call time).
   - Strings: only `""` and strings inside descriptive callsites (test title, `expect` message arg) allowed as bare literals. Any other string comes from the same three sources.
   - Fixtures are not a valid source. Static-literal fixture files are laundering.

2. **Positive pattern — the maintainability story.**
   - Production defines a constant (ideally a typed constant object), uses it at least once internally, and exports it.
   - Test imports the same symbol. One definition, single point of change.
   - When the value originates in a library or platform API, both production and test import from that origin directly. Production does not re-export library constants.
   - Reference `/standardizing-typescript` and `/standardizing-python` for the language-specific HOW.

3. **Testability gate — new Gate 1 step before coupling.**
   - Question: can the spec assertion be verified given the shape of the source code?
   - Check for seams, injection points, observable boundaries.
   - Failure → finding against the source file, remediation "refactor production for testability," skip remaining evidence checks for this assertion.
   - This makes the "test audit" a legitimate home for source-targeted findings when the code is in violation of the assertion being verifiable.

4. **Coupling taxonomy — add `laundered indirect` as a distinct rejection category.**
   - Current taxonomy has six entries. Literal laundering through a test-support module is a distinct failure mode from `False` (false direct coupling). Add it and keep the property assertion's "at least six" wording honest.

## Out of scope

- ESLint rule implementation. Lives in `spx/43-typescript.enabler/`.
- Ruff / Python equivalent. Lives in `spx/43-python.enabler/`.
- Schema change for the new `testability` step and source-file findings. Lives in `spx/21-spec-tree.enabler/32-evidence.enabler/43-audit-verdict-schema.enabler/PLAN.md`.
- Authoring the constant-object guidance itself. Lives in the language enablers.

## Done when

- [x] `test-auditing.md` declares assertions for the literal rule, the positive pattern, the testability gate, and the extended coupling taxonomy.
- [ ] `tests/test_test_auditing.scenario.l1.py`, `tests/test_test_auditing.property.l1.py`, and `tests/test_test_auditing.conformance.l1.py` exercise at least one scenario per new assertion (laundered-indirect rejection, testability failure against source, library-origin positive case).
- [ ] `/auditing-tests/SKILL.md` workflow restates the literal rule at each of: quick_start, coupling step, falsifiability step, rejection criteria.
- [ ] Audit dry-run against a handful of existing test files in this repo produces the expected verdicts.

## Origin

Conversation on 2026-04-24 exploring how to detect the constant-bag evasion pattern discovered in a TypeScript project (camelCase literals in a test-support module imported by a single test file).
