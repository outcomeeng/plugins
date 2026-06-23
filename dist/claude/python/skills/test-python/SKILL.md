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
Python test files that supply evidence for a spec-tree node's assertions — written fresh, or repaired against rejected evidence.
</objective>

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
2. For each assertion, use `/test` to select the assertion type, execution level, and any Stage 5 exception.
3. Apply the source-contract-first gate in `<source_contract_gate>`: inspect the code under test and identify the production contract the test will exercise.
4. If the production contract does not expose the needed value, registry, constructor, schema, pure function, protocol, or collaborator boundary, update the code under test before writing the test.
5. Choose the canonical test filename: `test_<subject>.<evidence>.<level>[.<runner>].py`.
6. Put only typed assertion code in the spec node's `tests/` directory.
7. Import source-owned values from the owning module.
8. Import variable input domains from `product_testing.generators.*`.
9. Import harness entrypoints from `product_testing.harnesses.*`; rely on `conftest.py` only for explicit pytest discovery imports.
10. Consume inert fixture files only by path, reading, or copying.
11. Run the node's canonical pytest command and the repository's lint/type commands.

</write_workflow>

<fix_workflow>
Run this workflow for rejected Python tests:

1. Read the rejection and locate every cited test, harness, generator, fixture path provider, and `conftest.py` shim.
2. Classify each finding by evidence property: coupling, falsifiability, alignment, coverage, source ownership, domain variation, oracle independence, cleanup safety, or pytest discovery safety.
3. Apply the source-contract-first gate in `<source_contract_gate>` and fix source architecture before fixing test syntax when the finding exposes missing source contracts.
4. Replace test-owned constants with source-owned exports or variable generators.
5. Replace constant-only generators with direct source imports or meaningful variable domains.
6. Move resource setup, teardown, cleanup, and pytest fixture bodies into `product_testing.harnesses.*`.
7. Keep `product_testing.fixtures/` for inert files only.
8. Remove `tests/helpers`, `tests/support`, node-local helper modules, and fixture body code from `conftest.py`.
9. Rerun the focused tests and repository-canonical Python validation commands.

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
Run the product's canonical test, lint, and type commands — the ones its `CLAUDE.md` / `AGENTS.md`, Justfile, Makefile, or package scripts document. When the product ships no wrapper, fall back to the tools directly only when they are installed:

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

</reporting>

<success_criteria>
Python test work satisfies this skill when:

- Every changed test maps to a spec assertion and selected assertion type
- Test filenames encode evidence, level, and optional runner
- Tests import source-owned values instead of defining local constants
- Generators represent meaningful variable domains
- Harnesses manage resource lifecycle and pytest fixture body code
- Inert fixtures are consumed only as files
- `conftest.py` contains discovery or registration only
- No framework mock replaces the behavior under test
- Focused tests and repository-canonical validation pass or the remaining failure is reported with the blocking cause

</success_criteria>
