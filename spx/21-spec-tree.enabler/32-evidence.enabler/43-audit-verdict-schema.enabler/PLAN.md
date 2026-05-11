# PLAN — schema support for testability step and source-file findings

> **Format note (post-flip context):** `spx/15-audit-verdict-format.pdr.md` flipped from XML to JSON in commit `dd03033`. The schema's document type changes accordingly — from XSD 1.1 (`audit-verdict.xsd`) to JSON Schema (`audit-verdict.schema.json` or equivalent). The planned extensions below — adding a `testability` Gate 1 step value, and allowing source-targeted findings via a `<source_file>` / `source_file` field — carry over to the JSON Schema form; only the file extension and the validator (jsonschema/Pydantic/ajv instead of xmllint/lxml) change. The carrier+payload work in [`spx/21-spec-tree.enabler/65-auditing.enabler/PLAN.md`](../../65-auditing.enabler/PLAN.md) lands the JSON Schema artifact; that work and this plan converge.

## Why

Test audit is gaining a new Gate 1 step (`testability`) that can emit findings against source files rather than test files. Current `audit-verdict.xsd` enumerates Gate 1 step values and assumes per-assertion findings target test files via `<test_file>`. Both need to change.

## Scope

1. **Enum extension.**
   - Add `testability` to the Gate 1 `<step>` enum. Existing values: `challenge, scope, evidence, mocks, oracle, harness_chain, coupling, falsifiability, alignment, coverage`. New value goes before `coupling` in the workflow; enum order in the schema does not need to match workflow order.

2. **Source-file findings — decide the shape.**
   - Option A: add optional `<source_file>` alongside `<test_file>` on a Gate 1 finding. Test-targeted findings fill `<test_file>`; source-targeted findings fill `<source_file>`; allow both when a finding spans.
   - Option B: rename `<test_file>` to `<target_file>` and let the step dictate interpretation. Breaking schema change.
   - Option C: scope by step. Testability findings carry only `<source_file>`. Other Gate 1 findings carry only `<test_file>`. Enforced by XSD 1.1 assert or post-schema coherence check.
   - Default: Option A. Least disruptive, explicit about the file's role, lets a single finding reference both when the code refactor must happen alongside the test change.

3. **Fixtures and coherence rule.**
   - Add a fixture demonstrating a `testability`-step finding against a source file.
   - Add a coherence rule: if step is `testability`, `<source_file>` must be present.

## Out of scope

- The audit skill's use of the schema (lives in `32-test-auditing.enabler/`).
- Gate 0 and Gate 2 changes.

## Done when

- `references/audit-verdict.xsd` accepts `testability` and the new file element.
- Fixtures in `references/fixtures/` cover pass and fail cases for both enum and structural checks.
- `tests/test_audit_verdict_schema.unit.py` exercises the new scenarios.
- `spx validation audit-verdict` validates real verdicts containing the new step.

## Origin

Conversation on 2026-04-24. Testability as a pre-coupling check emerged from the observation that most code is not testable by the time tests are written — the audit has to be able to reject the source, which needs schema support.
