# PLAN — Rust test standards follow-ups

## Why

`docs/cross-language-test-standards-drift-audit.md` records a Rust test-standard follow-up around credentialed `l3` behavior.

Rust currently has only the top-level Rust node for these concerns, so this note lives here until a dedicated Rust test-standards subtree exists.

## Steps

1. Decide whether credentialed `l3` behavior belongs in a shared cross-language decision or a Rust execution-level child node.
2. Align the existing fail-loud Level 3 guidance with that governing declaration.
3. Gate with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check`, and `rust:audit-rust-tests`.

## Revisit condition

Pick this up after the `review-changes` vocabulary boundary is clarified, so Rust standards work is reviewed with the corrected distinction between review and audit.
