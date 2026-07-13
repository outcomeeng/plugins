---
name: test-python
description: >-
  ALWAYS invoke this skill when writing or fixing tests for Python.
  NEVER write or fix Python tests without this skill.
argument-hint: "[node-path]"
arguments: node_path
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Bash(python3 -m pytest:*), Bash(python3 -m ruff:*), Bash(python3 -m mypy:*)
---

<prerequisites>

Invoke the `python:python-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `python:python-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Read `spx/local/python.md` and `spx/local/python-tests.md` when they exist.

</prerequisites>

<objective>
Python test files that supply evidence for a spec-tree node's assertions.
</objective>

<mode_detection>
Determine the mode before editing:

Resolve `$node_path` from the optional argument. When it is empty, use the target node from the live `<SPEC_TREE_CONTEXT>` marker. Stop before reading or editing tests when neither source provides a governing node path.

| Mode  | Signal                                                                                           | Action                       |
| ----- | ------------------------------------------------------------------------------------------------ | ---------------------------- |
| Write | The node has no Python evidence file for the assertion                                           | Follow `<write_workflow>`    |
| Fix   | Merged `test-evidence-auditor` JSON has `overall: REJECTED` or a `FAIL` row with Python findings | Follow `<fix_workflow>`      |
| Split | The test requires source architecture changes first                                              | Change source contract first |

NEVER create a test workaround for code that lacks source-owned contracts, typed dependency boundaries, or observable behavior.
</mode_detection>

<verification_gates>

Before writing or repairing a Python test, require the generic `/test` `<evidence_design_gate>` result for every assertion. Stop when any clause lacks an exercised path, assertion-relevant observable, independent oracle, or passing-while-false mutation, or when a subpart trigger has an incomplete evidence-chain inventory.

After writing or repairing tests:

1. Run the repository-canonical focused test command for `$node_path/tests/` and record its exit status.
2. In Write mode, PASS only when the test fails for the expected missing implementation or assertion mismatch; collection, syntax, harness, or configuration failures are FAIL unless missing implementation is the declared RED condition.
3. In Fix mode, PASS only when every repaired assertion's clause matrix remains complete and the focused test reaches the RED or passing state required by the active TDD phase.
4. Run the repository-canonical lint and type commands for the changed scope. Any nonzero result is FAIL.
5. Proceed to reporting or evidence audit only when the matrix gate, focused test gate, lint gate, and type gate all pass.

</verification_gates>

<write_workflow>
Run this workflow for new Python tests:

1. Read the target node spec and applicable decisions through the spec-tree context already loaded for the work.
2. For each assertion, use `/test` to select the assertion type, execution level, and any Stage 5 exception.
3. Apply the source-contract-first gate in `<source_contract_gate>`: inspect the code under test and identify the production contract the test will exercise.
4. If the production contract does not expose the needed value, registry, constructor, schema, pure function, protocol, or collaborator boundary, update the code under test before writing the test.
5. Choose the canonical test filename: `test_<subject>.<evidence>.<level>[.<runner>].py`.
6. Put only typed assertion code in the spec node's `tests/` directory.
7. Keep variable and constant declarations, domain or assertion literals, numbers, vocabulary, case data, expected results, configuration, pytest fixture parameters, and property-generated parameters out of the executed test file. One-off descriptive test titles and diagnostic messages remain inline. Use the zero-parameter wrapper pattern from `/python-test-standards`: import and call one harness entrypoint in the assertion expression.
8. Import source-owned values from the owning module.
9. Keep variable input domains and Hypothesis-generated parameters inside `<package>_testing.generators.*` and the consuming harness entrypoint.
10. Import zero-parameter harness entrypoints from `<package>_testing.harnesses.*`; use `conftest.py` only for marker and hook registration, never fixture discovery imports.
11. Consume inert fixture files only by path, reading, or copying.
12. Run the node's canonical pytest command and the repository's lint/type commands.

</write_workflow>

<fix_workflow>
Run this workflow for rejected Python tests:

1. Read the rejection and reinvoke `/test` for every rejected assertion.
2. Rebuild the complete clause-evidence matrix from the governing assertion and source contracts: exercised path, observable result, independent oracle, and passing-while-false mutation for every clause.
3. If any cited test proves only a subpart, locate every linked test, harness, generator, fixture path provider, source contract, oracle, assertion-relevant implementation path, and `conftest.py` shim before editing.
4. Classify each finding and every same-class instance across that chain by evidence property: coupling, falsifiability, alignment, coverage, source ownership, domain variation, oracle independence, cleanup safety, or pytest discovery safety.
5. Apply the source-contract-first gate in `<source_contract_gate>` and fix source architecture before fixing test syntax when the finding exposes missing source contracts.
6. Replace every variable or constant binding with a direct assertion expression over source-owned exports, harness-owned configuration, variable generators, fixture-path providers, or justified eval case data.
7. Replace constant-only generators with direct source imports or meaningful variable domains.
8. Move resource setup, teardown, cleanup, and pytest fixture bodies into `<package>_testing.harnesses.*`.
9. Keep `<package>_testing/fixtures/` for inert files only.
10. Remove `tests/helpers`, `tests/support`, node-local test-infrastructure modules, and fixture body code from `conftest.py`.
11. Apply all class-level repairs together, then rerun the focused tests and repository-canonical Python validation commands once on the stabilized evidence.

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
Run the product's canonical test, lint, and type commands — the ones its `CLAUDE.md`, Justfile, Makefile, or package scripts document. Follow the active runtime's approval flow for the exact wrapper command; never infer approval from shell patterns in skill metadata. When the product ships no wrapper, fall back to the tools directly only when they are installed:

```bash
python3 -m pytest $node_path/tests/ -v
python3 -m ruff check $node_path/tests/
python3 -m mypy $node_path/tests/
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

</reporting>

<failure_modes>

**Failure 1: Repaired only the cited test expectation**

Claude changed the expectation named by an audit finding while another clause of the same assertion still had no source-owned case or mutation-sensitive observable. The next audit rejected a different subpart of the same evidence chain.

Why it failed: the repair treated one reported predicate as the defect instead of treating the finding as evidence that the complete assertion chain was untrusted.

How to avoid: rebuild the complete clause-evidence matrix and inspect every linked test, harness, generator, fixture, source contract, oracle, and `conftest.py` shim before editing.

**Failure 2: Moved protocol vocabulary into a harness**

Claude removed literals from the executed test by placing schema keys, CLI tokens, paths, producer identities, and expected projections in a harness. The test became visually thin while the harness still owned production truth.

Why it failed: relocating protocol vocabulary changed its file without restoring ownership to the production contract that defines it.

How to avoid: export protocol vocabulary and constructors from the owning production module. Harnesses own lifecycle, resource access, replay policy, and diagnostics only.

</failure_modes>

<success_criteria>
Python test work satisfies this skill when:

- Every changed test maps to a spec assertion and selected assertion type
- Test filenames encode evidence, level, and optional runner
- Tests introduce no variable or constant declarations, domain or assertion literals, numbers, vocabulary, case data, expected results, or configuration; one-off descriptive titles and diagnostics remain inline
- Generators represent meaningful variable domains
- Harnesses manage resource lifecycle and generated-case binding through zero-parameter entrypoints
- Inert fixtures are consumed only as files
- `conftest.py` contains marker or hook registration only
- No framework mock replaces the behavior under test
- The matrix gate, focused test gate, repository-canonical lint gate, and repository-canonical type gate all pass for the changed scope

</success_criteria>
