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

## Decomposition disposition — flat node carries the full test-evidence seam set (interim)

The test-evidence seam alignment added six Compliance assertions to `rust.md` (predicate ownership, semantic-binding-by-choice, controlled-implementation rules, case provenance, oracle independence), taking its Compliance section to 15 assertions — past the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md` and beyond the sibling nodes `spx/43-python.enabler/python.md` (7) and `spx/43-typescript.enabler/typescript.md` (6). Those siblings stay small because Python holds these rules in the decomposed `25-python-standards.enabler/25-python-tests.enabler` subtree; Rust has no equivalent subtree yet.

**Disposition: defer decomposition; keep the assertions inline as the interim home.** The seam assertions are correct product truth the alignment needed now, and they must live somewhere until the subtree exists. Decomposing `rust.md` into a dedicated Rust test-standards subtree that mirrors Python's structure is a separate structural `/decompose` — it creates new nodes, relocates the roughly ten test-standard assertions, and assigns ordering evidence — larger than the seam-alignment scope and already the direction this PLAN anticipates. When that subtree is created, move the seam and test-infrastructure assertions into it and shrink `rust.md` back below the signal.

Recorded so the decomposition signal is dispositioned, not silently carried forward on the next edit. Surfaced by `changes-reviewer` (rule `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md:ALWAYS:1`) during the Rust seam alignment.
