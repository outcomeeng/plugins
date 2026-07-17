# PLAN — Rust credentialed Level-3 governance

## Pending test-standard skill corrections

1. Replace "test-owned" generator and harness wording in `rust-test-standards/SKILL.md` with `product-testing` workspace-member crate ownership.
2. Move the generator example from `tests/generators/audit.rs` to `product-testing/src/generators/audit.rs` and import it through `product_testing::generators::*`.

## Pending decision

1. Decide whether credentialed Level-3 behavior belongs in a shared cross-language decision or a Rust execution-level child node.
2. After that governing decision exists, replace reasoned `#[ignore]` credential examples with helpers that fail loudly and explain the required setup.

## Revisit conditions

- Resume the skill corrections during the next Rust test-standards maintenance changeset.
- Resume the credential decision when the credentialed Level-3 evidence policy is ready for product-decision authoring.
