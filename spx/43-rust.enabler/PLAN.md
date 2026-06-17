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

Pick this up after the `review-changes` vocabulary boundary is clarified, so Rust standards work is reviewed with the corrected distinction between reviewing and auditing.
