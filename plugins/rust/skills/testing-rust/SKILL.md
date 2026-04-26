---
name: testing-rust
description: ALWAYS invoke this skill when writing or fixing tests for Rust. NEVER write or repair Rust tests without this skill.
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust/SKILL.md" || echo "standardizing-rust not found — invoke rust:standardizing-rust manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust-tests/SKILL.md" || echo "standardizing-rust-tests not found — invoke rust:standardizing-rust-tests manually"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/testing/SKILL.md" || echo "testing not found — invoke spec-tree:testing manually"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. `rust:standardizing-rust`
2. `rust:standardizing-rust-tests`
3. `spec-tree:testing`

</codex_fallback>

<objective>
Implement Rust tests after the `/testing` router decides what to verify and at what level. This skill provides the Rust workflow and load order; reusable policy and examples live in `/standardizing-rust` and `/standardizing-rust-tests`.
</objective>

<prerequisites>
The `/testing` router, `/standardizing-rust`, and `/standardizing-rust-tests` are pre-loaded above.

Before writing or revising tests, also check:

1. `spx/local/rust.md` at the repository root, if present
2. `spx/local/rust-tests.md` at the repository root, if present

</prerequisites>

<workflow>
1. Load the governing spec context before editing any co-located `spx/.../tests/` file.
2. Map each assertion to the evidence type and level chosen by `/testing`.
3. Use the `<router_mapping>` and examples in `/standardizing-rust-tests` to choose the Rust implementation shape.
4. Keep test helpers, fixtures, and harnesses in the location prescribed by `/standardizing-rust-tests` and repo-local overlays.
5. Run the repository's Rust validation commands before reporting the tests complete.

</workflow>

<router_mapping>
After running through `/testing`, use the canonical mapping in `/standardizing-rust-tests`:

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
All Rust test examples are owned by `/standardizing-rust-tests`:

- `/standardizing-rust-tests` `<level_1_patterns>`
- `/standardizing-rust-tests` `<property_and_compile_time_patterns>`
- `/standardizing-rust-tests` `<level_2_patterns>`
- `/standardizing-rust-tests` `<level_3_patterns>`
- `/standardizing-rust-tests` `levels/level-1.md`
- `/standardizing-rust-tests` `levels/level-2.md`
- `/standardizing-rust-tests` `levels/level-3.md`

</reference_guides>

<success_criteria>
Rust test work is complete when:

- `/testing` chose the evidence mode and target level first
- `/standardizing-rust` and `/standardizing-rust-tests` were loaded before test code was written
- the test shape follows the canonical Rust test standard and repo-local overlays
- controlled implementations preserve coupling to the real seam
- property claims use property-based testing
- compile-time claims use compile-fail evidence
- repository validation passes or any unavailable validation tool is reported explicitly

</success_criteria>
