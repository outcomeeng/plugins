---
name: test-python
description: >-
  ALWAYS invoke this skill when writing or fixing tests for Python.
  NEVER write or fix Python tests without this skill.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

Invoke the `python:python-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `python:python-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Python test files that supply evidence for a spec-tree node's assertions.
</objective>

<evidence_design_gate>
Before reading or mutating an executed Python test file for authoring or repair, require the complete packet emitted by foundational `/test` for every assertion in scope.

Proceed only when:

- packet `status` is `PROCEED`;
- `mutation_allowed` is `true`;
- every row records quantifier and domain, independent oracle, pass-while-false condition, execution level, source-contract needs, harness needs, generator needs, fixture status, and property replay needs;
- every local artifact reference is a product-root-relative Markdown link whose target matches its declared role;
- every governed source contract, harness, generator, or fixture pairs its exact governing spec or full decision-record link with its implementation link when implementation exists;
- every fixture row is `none` or carries the scoped operator decision returned by `/test`.

When the packet is absent or stopped, return control to `/test` with `RUN_TEST_EVIDENCE_GATE` and make no file mutation. When a fixture decision is pending, return `REQUEST_FIXTURE_APPROVAL`; `/test` owns the structured operator question, so this Python skill never repeats or replaces that approval workflow. When planned infrastructure or a source contract has no implementation, preserve the governing link and absent status and stop until its TDD flow supplies the implementation.

Preserve the packet and fixture decision unchanged in the test-evidence-auditor handoff. They provide design context and never proof; the auditor reconstructs the evidence design independently.
</evidence_design_gate>

<mode_detection>
Determine the mode before editing:

| Mode  | Signal                                                  | Action                       |
| ----- | ------------------------------------------------------- | ---------------------------- |
| Write | The node has no Python evidence file for the assertion  | Follow `<write_workflow>`    |
| Fix   | `/audit-python-tests` rejected existing Python evidence | Follow `<fix_workflow>`      |
| Split | The test requires source architecture changes first     | Change source contract first |

NEVER create a test workaround for code that lacks source-owned contracts, typed dependency boundaries, or observable behavior.
</mode_detection>

<write_workflow>
Run this workflow for new Python tests:

1. Read the target node spec and applicable decisions through the spec-tree context already loaded for the work.
2. Apply `<evidence_design_gate>` to the packet returned by `/test`. Stop before mutation when any row does not permit proceeding.
3. Apply the source-contract-first gate in `<source_contract_gate>`: inspect the code under test and identify the production contract the test will exercise.
4. If the production contract does not expose the needed value, registry, constructor, schema, pure function, protocol, or collaborator boundary, update the code under test before writing the test.
5. Choose the canonical test filename: `test_<subject>.<evidence>.<level>[.<runner>].py`.
6. Put only typed assertion code in the spec node's `tests/` directory.
7. Keep literals, numbers, vocabulary, case data, expected results, configuration, pytest fixture parameters, and property-generated parameters out of the executed test file. Convenience aliases may derive solely from imported source contracts, generators, harnesses, fixture-path providers, or justified eval case data.
8. Import source-owned values from the owning module.
9. Import variable input domains from `product_testing.generators.*`.
10. Import harness entrypoints from `product_testing.harnesses.*`; rely on `conftest.py` only for explicit pytest discovery imports.
11. Consume inert fixture files only by path, reading, or copying.
12. Preserve every governing and implementation Markdown link from the packet in the audit handoff; an import or implementation path never substitutes for its governing spec or decision link.
13. Run the node's canonical pytest command and the repository's lint/type commands.

</write_workflow>

<fix_workflow>
Run this workflow for rejected Python tests:

1. Read the rejection and locate every cited test, harness, generator, fixture path provider, and `conftest.py` shim.
2. Re-run `/test` for the rejected assertion and apply `<evidence_design_gate>` before changing the test or its infrastructure; preserve the replacement packet for the next audit handoff.
3. Classify each finding by evidence property: reference validity, coupling, falsifiability, alignment, coverage, source ownership, domain variation, oracle independence, fixture suitability, replayability, cleanup safety, or pytest discovery safety.
4. Apply the source-contract-first gate in `<source_contract_gate>` and fix source architecture before fixing test syntax when the finding exposes missing source contracts.
5. Replace bindings that introduce data, expected outputs, configuration, vocabulary, case choices, or policy with source-owned exports, harness-owned configuration, variable generators, fixture-path providers, or justified eval case data. Preserve convenience aliases derived solely from those imported owners.
6. Replace constant-only generators with direct source imports or meaningful variable domains.
7. Move resource setup, teardown, cleanup, and pytest fixture bodies into `product_testing.harnesses.*`.
8. Keep `product_testing.fixtures/` for inert files only.
9. Remove `tests/helpers`, `tests/support`, node-local test-infrastructure modules, and fixture body code from `conftest.py`.
10. Rerun the focused tests and repository-canonical Python validation commands.

</fix_workflow>

<source_contract_gate>
Before writing or repairing a test, answer these checks from the code under test:

- Does the source own every protocol value, status, route, command name, registry key, schema field, or public vocabulary item that the test needs?
- Does the source expose pure functions, constructors, dataclasses, enums, schemas, protocols, or typed collaborators that make the behavior observable?
- Does every side effect cross an injected boundary when the assertion needs to inspect behavior without performing the real side effect?
- Does the expected output derive from the generated input, an independent oracle, or a source outside the module under test?

If any answer is no, fix the source contract first. Do not hide the missing contract in a test constant, fixture file, or generator wrapper.
</source_contract_gate>

<verification>
Run the product's canonical test, lint, and type commands — the ones its `AGENTS.md`, Justfile, Makefile, or package scripts document. When the product ships no wrapper, fall back to the tools directly only when they are installed:

```bash
python3 -m pytest <node-path>/tests/ -v
python3 -m ruff check <node-path>/tests/
python3 -m mypy <node-path>/tests/
```

Report any tool the product lacks rather than silently skipping it.
</verification>

<reporting>
Report the evidence created or repaired with:

- Node path
- Test files changed
- Source contracts added or consumed
- Harnesses, generators, inert fixture files, and `conftest.py` shims touched
- Verification commands and outcomes
- Remaining rejection, if an audit gate still fails
- Foundational evidence-design packet and fixture decision passed to the audit handoff

</reporting>

<success_criteria>
Python test work satisfies this skill when:

- Every changed test maps to a spec assertion and selected assertion type
- Every changed test was preceded by a proceeding foundational evidence-design packet, and that packet plus any fixture decision is preserved unchanged for independent audit reconstruction
- Test filenames encode evidence, level, and optional runner
- Tests introduce no local literals, numbers, vocabulary, case data, expected results, or configuration; convenience aliases derive solely from source contracts, generators, harnesses, inert-fixture path providers, or eval case data
- Generators represent meaningful variable domains
- Harnesses manage resource lifecycle and pytest fixture body code
- Inert fixtures are consumed only as files
- `conftest.py` contains discovery or registration only
- No framework mock replaces the behavior under test
- Focused tests and repository-canonical validation pass or the remaining failure is reported with the blocking cause

</success_criteria>
