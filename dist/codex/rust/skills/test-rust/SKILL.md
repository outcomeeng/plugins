---
name: test-rust
description: ALWAYS invoke this skill when writing or fixing tests for Rust. NEVER write or repair Rust tests without this skill.
argument-hint: "[node-path]"
arguments: node_path
allowed-tools: Read, Glob, Grep, Write, Edit, Skill
---

<objective>
Rust tests for what the `/test` router selected, at the chosen level.
</objective>

<prerequisites>
Invoke the `rust:rust-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `rust:rust-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke every prerequisite declaration above and proceed only after `/test`, `/rust-standards`, and `/rust-test-standards` load successfully.

Before writing or revising tests, also check:

1. `spx/local/rust.md` at the repository root, if present
2. `spx/local/rust-tests.md` at the repository root, if present

</prerequisites>

<mode_detection>

Resolve `$node_path` from the optional argument. When it is empty, use the target node from the live `<SPEC_TREE_CONTEXT>` marker. Stop before reading or editing tests when neither source provides a governing node path.

| Mode  | Signal                                                                                         | Action                                         |
| ----- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Write | The assertion has no Rust evidence file                                                        | Follow `<workflow>`                            |
| Fix   | Merged `test-evidence-auditor` JSON has `overall: REJECTED` or a `FAIL` row with Rust findings | Follow `<fix_workflow>`                        |
| Split | The source contract cannot expose the asserted behavior                                        | Fix the source contract before test predicates |

</mode_detection>

<verification_gates>

Before writing or repairing Rust evidence, require the generic `/test` `<evidence_design_gate>` result for every assertion. Stop when any clause lacks an exercised path, assertion-relevant observable, independent oracle, or passing-while-false mutation, or when a subpart trigger has an incomplete evidence-chain inventory.

Read the canonical rendered root guide at `AGENTS.md`, then `spx/local/rust.md` and `spx/local/rust-tests.md` when present, for repository-specific Rust validation requirements. Run the direct Cargo commands below at the closest package or workspace scope that satisfies those requirements, and record that scope. Follow the active runtime's approval flow for the exact repository wrapper command; never infer approval from shell patterns in skill metadata.

```bash
cargo test --all-targets --all-features
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo check --all-targets --all-features
cargo llvm-cov --workspace --all-features
```

Run `cargo llvm-cov` only when the repository requires a deterministic coverage gate and declares no wrapper; otherwise omit it or use the repository-declared coverage command.

After writing or repairing tests:

1. Run the repository-canonical focused Rust test command for `$node_path/tests/` and record its exit status.
2. In Write mode, PASS only when the test fails for the expected assertion mismatch, or when the source-contract gate established before the run that the owning production module or item is absent and the focused failure contains only that missing owner. Syntax, harness, workspace, manifest, configuration, and unrelated compilation failures are FAIL.
3. In Fix mode, PASS only when every repaired assertion's clause matrix remains complete and the focused test reaches the RED or passing state required by the active TDD phase.
4. Run the repository-canonical Rust formatting, lint, and type/compile commands for the changed scope. Formatting MUST exit zero. Lint and compile commands MUST exit zero except on the declared specified-node path, where every diagnostic must be the direct compiler consequence of the same missing production module or item; actual lint diagnostics and unrelated compiler diagnostics are FAIL.
5. When the repository requires a deterministic coverage gate, run its declared coverage command, falling back to `cargo llvm-cov --workspace --all-features` only when no wrapper exists. Exit zero is PASS; any nonzero result is FAIL. On the declared specified-node path, record coverage as not applicable until implementation exists.
6. Proceed to reporting or evidence audit only when the matrix gate, focused test gate, formatting gate, lint gate, compile gate, and applicable coverage gate all pass.

</verification_gates>

<workflow>
1. Load the governing spec context before editing any co-located `spx/.../tests/` file.
2. Map each assertion to the assertion type and level chosen by `/test`.
3. Apply the `/test` source-contract-first gate: read the assertion, the existing or planned test, and the Rust code under test; state the production contract the evidence exercises.
4. If the source does not expose the enum, constructor, trait boundary, parser entry point, registry, schema, or observable behavior the assertion needs, fix the source contract before writing test predicates.
5. Use `/rust-test-standards` `<router_mapping>` and `<alignment_rules>` to choose the Rust implementation shape, then load only the level-pattern section or bundled level guide selected by that mapping.
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

<reference_guides>
All Rust test examples are owned by `/rust-test-standards`:

- `/rust-test-standards` `<level_1_patterns>`
- `/rust-test-standards` `<property_and_compile_time_patterns>`
- `/rust-test-standards` `<level_2_patterns>`
- `/rust-test-standards` `<level_3_patterns>`
- `/rust-test-standards` `<reference_guides>` for the bundled level 1, level 2, and level 3 guides

</reference_guides>

<success_criteria>
Rust test evidence is sound when:

- Every assertion-to-evidence matrix names the assertion type, level, linked Rust evidence file, source-coupling path, independent oracle, relevant source branches, and one concrete falsifying mutation per clause.
- Every subpart trigger inventories each linked test, `<package>-testing` harness, generator, inert fixture, source contract, oracle, and assertion-relevant implementation path.
- Every Rust evidence file uses the canonical `<subject>.<evidence>.<level>[.<runner>].rs` name and the assertion type's required form from `/rust-test-standards`.
- Executed test files declare no `const`, `static`, `let`, fixture parameters, property-generated parameters, source vocabulary, expected values, or runner policy.
- Controlled implementations preserve executable coupling to the real trait or boundary; property claims use meaningful property-based evidence, and compile-time claims use compile-fail evidence.
- In Write mode, the resolved test command fails only for the expected missing implementation or assertion mismatch; in Fix mode, it reaches the RED or passing state required by the active TDD phase.
- The resolved formatting command exits zero; lint and compile commands exit zero except on the declared specified-node path where every diagnostic is the direct compiler consequence of the same missing production module or item; the report records every exact command and exit status.
- The repository-declared coverage command exits zero when coverage is required; when no coverage gate is declared or the node is on the declared specified-node path, the report records that coverage is not applicable.
- Every merged Rust audit finding and same-class instance maps to a completed repair before redispatch.

</success_criteria>

<failure_modes>

**Failure: Patched one Rust finding and redispatched**

Claude changed the cited assertion while adjacent clauses and `<package>-testing` infrastructure retained the same evidence defect. The next audit rejected another instance and the apply loop lost its autonomous repair boundary.

Why it failed: Claude treated a finding as a single predicate repair instead of evidence that the assertion's full chain and same-class instances were untrusted.

How to avoid: Reinvoke `/test` after the first merged audit failure, rebuild the complete assertion matrix, inspect the full evidence chain, apply every same-class repair together, then run `<verification_gates>` once before redispatch.

</failure_modes>
