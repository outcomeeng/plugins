---
name: test-rust
description: ALWAYS invoke this skill when writing or fixing tests for Rust. NEVER write or repair Rust tests without this skill.
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

Invoke the `rust:rust-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `rust:rust-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Implement Rust tests after the `/test` router decides what to verify and at what level. This skill provides the Rust workflow and load order; reusable policy and examples live in `/rust-standards` and `/rust-test-standards`.
</objective>

<prerequisites>
The `/test` router, `/rust-standards`, and `/rust-test-standards` are pre-loaded above.

Before writing or revising tests, also check:

1. `spx/local/rust.md` at the repository root, if present
2. `spx/local/rust-tests.md` at the repository root, if present

</prerequisites>

<workflow>
1. Load the governing spec context before editing any co-located `spx/.../tests/` file.
2. Map each assertion to the assertion type and level chosen by `/test`.
3. Apply the `/test` source-contract-first gate: read the assertion, the existing or planned test, and the Rust code under test; state the production contract the evidence exercises.
4. If the source does not expose the enum, constructor, trait boundary, parser entry point, registry, schema, or observable behavior the assertion needs, fix the source contract before writing test predicates.
5. Use the `<router_mapping>` and examples in `/rust-test-standards` to choose the Rust implementation shape.
6. Keep test helpers, fixtures, and harnesses in the location prescribed by `/rust-test-standards` and repo-local overlays.
7. Run the repository's Rust validation commands before reporting the tests complete.

</workflow>

<router_mapping>
After running through `/test`, use the canonical mapping in `/rust-test-standards`:

| Router Decision       | Rust implementation summary                                              |
| --------------------- | ------------------------------------------------------------------------ |
| Stage 2 -> Level 1    | pure functions, temp dirs, hand-written trait impls                      |
| Stage 2 -> Level 2    | real binaries, local adapters, async runtimes, local services            |
| Stage 2 -> Level 3    | remote APIs, deployed workflows, browser automation, shared environments |
| Stage 3A              | direct pure-function tests                                               |
| Stage 3B              | extracted pure helper plus outer boundary evidence                       |
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
- `/rust-test-standards` `levels/level-1.md`
- `/rust-test-standards` `levels/level-2.md`
- `/rust-test-standards` `levels/level-3.md`

</reference_guides>

<success_criteria>
Rust test work is complete when:

- `/test` chose the assertion type and target level first
- the source-contract-first gate was applied before test predicates were written or repaired
- `/rust-standards` and `/rust-test-standards` were loaded before test code was written
- the test shape follows the canonical Rust test standard and repo-local overlays
- controlled implementations preserve coupling to the real seam
- property claims use property-based testing
- compile-time claims use compile-fail evidence
- repository validation passes or any unavailable validation tool is reported explicitly

</success_criteria>
