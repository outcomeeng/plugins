# PLAN — Rust test standards follow-ups

## Why

`docs/cross-language-test-standards-drift-audit.md` records Rust test-standard follow-ups around "test-owned" wording, an inside-`tests/` generator example, and credentialed `l3` behavior.

Rust currently has only the top-level Rust node for these concerns, so this note lives here until a dedicated Rust test-standards subtree exists.

## Steps

1. Replace "test-owned" generator and harness wording in `rust-test-standards` with `product-testing` workspace-member crate wording.
2. Move the generator example path from `tests/generators/audit.rs` to `product-testing/src/generators/audit.rs` and adjust imports to `product_testing::generators::*`.
3. Decide whether credentialed `l3` behavior belongs in a shared cross-language decision or a Rust execution-level child node.
4. After that governing decision exists, replace `#[ignore]` credential examples with fail-loud credential helpers.
5. Gate with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check`, and `rust:audit-rust-tests`.

## Revisit condition

Pick this up after the `review-changes` vocabulary boundary is clarified, so Rust standards work is reviewed with the corrected distinction between review and audit.

## Decomposition disposition — duplication removed; residual count still above the signal

The test-evidence seam rules no longer live inline in `rust.md`. The subtractive-spec reduction removed the restated language-neutral seam assertions — they are owned once by `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`, which `rust.md` now cites — leaving `rust.md` carrying only Rust deltas (assertion macros, semantic-choice bindings, the `product-testing` crate home, `proptest`/`quickcheck`, inside-crate anti-locations, `unsafe`/FFI) plus its auditor-composition and foundational-pattern assertions.

`rust.md` now holds 9 Compliance assertions, down from 15. That clears the duplication that inflated the count, but 9 still exceeds the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md:ALWAYS:1`, so a decomposition-analysis pass remains a soft, deferred follow-up — no longer forced by duplicated content, but not closed by assertion count either. Unlike the Python and TypeScript siblings, Rust has no test-standards subtree to absorb the residual deltas yet; creating one is the structural `/decompose` this note anticipates, taken up when a Rust test-standards subtree is otherwise warranted.
