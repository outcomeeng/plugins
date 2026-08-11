# PLAN — Rust test standards follow-ups

## Why

`docs/cross-language-test-standards-drift-audit.md` records Rust test-standard follow-ups around "test-owned" wording, an inside-`tests/` generator example, and credentialed `l3` behavior.

Rust currently has only the top-level Rust node for these concerns, so this note lives here until a dedicated Rust test-standards subtree exists.

## Steps

1. **Satisfied.** "test-owned" survives in `rust-test-standards` only in its correct sense — the predicate the linked `#[test]` owns — not as generator or harness placement wording. `audit-rust-tests` uses it as a finding label for a binding that chooses configuration or data.
2. **Satisfied.** The generator example sits at `<product>-testing/src/generators/audit.rs` with `<product>_testing::generators::*` imports. `tests/generators/audit.rs` remains only as the subject of a documented failure mode, which is where it belongs.
3. Decide whether credentialed `l3` behavior belongs in a shared cross-language decision or a Rust execution-level child node.
4. After that governing decision exists, replace `#[ignore]` credential examples with fail-loud credential helpers.
5. Gate with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check`, and `rust:audit-rust-tests`.

Steps 3 and 4 are independent of the predicate-seam correction recorded below: that correction changes what each example asserts and who owns the assertion, and decides nothing about credential resolution or skip policy.

## Rust delta for the source-laundering rule — pending

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` carries the language-neutral source-laundering rule: a case, example, or expectation table placed inside a module under test so a test can cite a production path as its provenance, with ownership following consumption rather than address. `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/` declares the Python discriminator in the same changeset. Rust has no delta yet.

The Rust delta is the discriminator in Rust terms: a `pub` item in the product crate whose only callers are `spx/**/tests/` modules and the `<product>-testing` crate, reached because `#[path]`-wired spec tests compile inside the product crate and can therefore call items no released consumer can. `#[cfg(test)]` gating is the adjacent case and is a different defect — it keeps the symbol out of the shipped artifact while still putting test data in the product crate.

**Blocked on nothing.** It was left out because the operator scoped the authoring pass to the language-neutral level and Python.

## Predicate-seam correction to the worked examples — executed

`rust-test-standards` stated the predicate seam correctly in `<success_criteria>`, `<acceptable_doubles>`, `<predicate_and_oracle_litmus>`, `<test_data_policy>`, and `<anti_patterns>`, and contradicted it in all fourteen worked examples, each of which was a single call to an `assert_*` harness function with no assertion macro in the `#[test]` body. The governing rules are
`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` ALWAYS:18 and NEVER:36, and the shared `test-evidence-standards` `<predicate_seam>`.

Every example now ends in an assertion macro the reader can see, with the harness supplying resources, lifecycle, and — for property runs — case count, seed, and replay output while the invariant stays in the `#[test]` closure. Four examples also imported domain values from `fixtures::` modules, which
`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` forbids; those now draw from generators, and the surviving `fixtures::` imports return paths.

No Rust assertion was added for the seam itself. It is a language-neutral rule the superset owns, and `rust.md:15` binds this node to Rust deltas only.

## Revisit condition

Pick this up after the `review-changes` vocabulary boundary is clarified, so Rust standards work is reviewed with the corrected distinction between review and audit.

## Decomposition disposition — duplication removed; residual count still above the signal

The test-evidence seam rules no longer live inline in `rust.md`. The subtractive-spec reduction removed the restated language-neutral seam assertions — they are owned once by `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`, which `rust.md` now cites — leaving `rust.md` carrying only Rust deltas (assertion macros, semantic-choice bindings, the `product-testing` crate home, `proptest`/`quickcheck`, inside-crate anti-locations, `unsafe`/FFI) plus its auditor-composition and foundational-pattern assertions.

`rust.md` now holds 9 Compliance assertions, down from 15. That clears the duplication that inflated the count, but 9 still exceeds the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md:ALWAYS:1`, so a decomposition-analysis pass remains a soft, deferred follow-up — no longer forced by duplicated content, but not closed by assertion count either. Unlike the Python and TypeScript siblings, Rust has no test-standards subtree to absorb the residual deltas yet; creating one is the structural `/decompose` this note anticipates, taken up when a Rust test-standards subtree is otherwise warranted.
