---
name: test-rust
description: ALWAYS invoke this skill when writing or fixing tests for Rust. NEVER write or repair Rust tests without this skill.
argument-hint: "[node-path]"
arguments: node_path
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, Skill
---

{!% require_skill 'rust:rust-standards' %!}

{!% require_skill 'rust:rust-test-standards' %!}

{!% require_skill 'spec-tree:test' %!}

<objective>
Rust tests for what the `/test` router selected, at the chosen level.
</objective>

<prerequisites>
The `/test` router, `/rust-standards`, and `/rust-test-standards` are pre-loaded above.

Before writing or revising tests, also check:

1. `spx/local/rust.md` at the repository root, if present
2. `spx/local/rust-tests.md` at the repository root, if present

</prerequisites>

<mode_detection>

Resolve `$node_path` from the optional argument. When it is empty, use the target node from the live `<SPEC_TREE_CONTEXT>` marker.

| Mode  | Signal                                                                                         | Action                                         |
| ----- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Write | The assertion has no Rust evidence file                                                        | Follow `<workflow>`                            |
| Fix   | Merged `test-evidence-auditor` JSON has `overall: REJECTED` or a `FAIL` row with Rust findings | Follow `<fix_workflow>`                        |
| Split | The source contract cannot expose the asserted behavior                                        | Fix the source contract before test predicates |

</mode_detection>

<verification_gates>

Before writing or repairing Rust evidence, require the generic `/test` `<evidence_design_gate>` result for every assertion. Stop when any clause lacks an exercised path, assertion-relevant observable, independent oracle, or passing-while-false mutation, or when a subpart trigger has an incomplete evidence-chain inventory.

After writing or repairing tests:

1. Run the repository-canonical focused Rust test command for `$node_path/tests/` and record its exit status.
2. In Write mode, PASS only when the test fails for the expected missing implementation or assertion mismatch; compilation, harness, workspace, or configuration failures are FAIL unless missing implementation is the declared RED condition.
3. In Fix mode, PASS only when every repaired assertion's clause matrix remains complete and the focused test reaches the RED or passing state required by the active TDD phase.
4. Run the repository-canonical Rust formatting, lint, and type/compile commands for the changed scope. Any nonzero result is FAIL.
5. Proceed to reporting or evidence audit only when the matrix gate, focused test gate, formatting gate, lint gate, and compile gate all pass.

</verification_gates>

<workflow>
1. Load the governing spec context before editing any co-located `spx/.../tests/` file.
2. Map each assertion to the assertion type and level chosen by `/test`.
3. Apply the `/test` source-contract-first gate: read the assertion, the existing or planned test, and the Rust code under test; state the production contract the evidence exercises.
4. If the source does not expose the enum, constructor, trait boundary, parser entry point, registry, schema, or observable behavior the assertion needs, fix the source contract before writing test predicates.
5. Use the `<router_mapping>` and examples in `/rust-test-standards` to choose the Rust implementation shape.
6. Do not declare `const`, `static`, `let`, framework fixture parameters, or property-generated parameters in executed test files; source contracts, `<package>-testing` harnesses, generators, inert fixtures, or eval case data own the values those bindings would hold.
7. Keep test infrastructure — harnesses, generators, and inert fixtures — in the location prescribed by `/rust-test-standards` and repo-local overlays.
8. Run the repository's Rust validation commands before reporting the tests complete.

</workflow>

<fix_workflow>

1. Read the merged `test-evidence-auditor` JSON and the Rust findings appended to its gate rows.
2. Reinvoke `/test` for every affected assertion and rebuild the complete clause-evidence matrix from the governing assertion and source contracts.
3. If any cited test proves only a subpart, inspect every linked test, `<package>-testing` harness, generator, inert fixture, source contract, oracle, and assertion-relevant implementation path before editing.
4. Classify every finding and same-class instance across that chain by coupling, falsifiability, alignment, coverage, source ownership, domain variation, oracle independence, cleanup safety, or workspace-boundary safety.
5. Fix source architecture before test syntax when the finding exposes a missing enum, constructor, trait boundary, parser entry point, registry, schema, or observable behavior.
6. Apply every class-level repair together, then run `<verification_gates>` once on the stabilized evidence before redispatch.

</fix_workflow>

<router_mapping>
After running through `/test`, use the canonical mapping in `/rust-test-standards`:

| Router Decision       | Rust implementation summary                                              |
| --------------------- | ------------------------------------------------------------------------ |
| Stage 2 -> Level 1    | pure functions, temp dirs, hand-written trait impls                      |
| Stage 2 -> Level 2    | real binaries, local adapters, async runtimes, local services            |
| Stage 2 -> Level 3    | remote APIs, deployed workflows, browser automation, shared environments |
| Stage 3A              | direct pure-function tests                                               |
| Stage 3B              | extracted pure function plus outer boundary evidence                     |
| Stage 5 exceptions    | controlled implementations that preserve the real seam                   |
| compile-time contract | compile-fail evidence                                                    |
| universal invariant   | property-based evidence                                                  |

</router_mapping>

<reference_guides>
All Rust test examples are owned by `/rust-test-standards`:

- `/rust-test-standards` `<level_1_patterns>`
- `/rust-test-standards` `<property_and_compile_time_patterns>`
- `/rust-test-standards` `<level_2_patterns>`
- `/rust-test-standards` `<level_3_patterns>`
- `/rust-test-standards` Level 1 local deterministic guidance
- `/rust-test-standards` Level 2 local infrastructure guidance
- `/rust-test-standards` Level 3 remote credentialed guidance

</reference_guides>

<success_criteria>
Rust test work is complete when:

- every assertion has a complete `/test` clause-evidence matrix and the evidence-design gate passes
- every subpart trigger has a complete full-chain inventory
- `/test` chose the assertion type and target level first
- the source-contract-first gate was applied before test predicates were written or repaired
- `/rust-standards` and `/rust-test-standards` were loaded before test code was written
- the test shape follows the canonical Rust test standard and repo-local overlays
- executed test files declare no `const`, `static`, `let`, fixture parameters, or property-generated parameters
- controlled implementations preserve coupling to the real seam
- property claims use property-based testing
- compile-time claims use compile-fail evidence
- the focused Rust test gate and repository-canonical formatting, lint, and compile gates all pass
- in Fix mode, every merged audit finding and same-class instance maps to a completed class-level repair

</success_criteria>

<failure_modes>

**Failure: Patched one Rust finding and redispatched**

Claude changed the cited assertion while adjacent clauses and `<package>-testing` infrastructure retained the same evidence defect. The next audit rejected another instance and the apply loop lost its autonomous repair boundary.

Why it failed: Claude treated a finding as a single predicate repair instead of evidence that the assertion's full chain and same-class instances were untrusted.

How to avoid: Reinvoke `/test` after the first merged audit failure, rebuild the complete assertion matrix, inspect the full evidence chain, apply every same-class repair together, then run `<verification_gates>` once before redispatch.

</failure_modes>
