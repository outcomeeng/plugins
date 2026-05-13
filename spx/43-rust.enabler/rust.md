# Rust

PROVIDES the complete Rust development workflow — architecture, testing, implementation, review, and unsafe-code auditing
SO THAT Rust projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality and soundness

The rust plugin contains 9 skills following the foundational + language-specific pattern: `/standardizing-rust` (reference), `/standardizing-rust-architecture` (reference), `/standardizing-rust-tests` (reference), `/testing-rust`, `/coding-rust`, `/auditing-rust`, `/auditing-rust-tests`, `/architecting-rust`, `/auditing-rust-architecture`. Five agents (`rust-code-auditor`, `rust-architecture-auditor`, `rust-test-auditor`, `rust-simplifier`, `rust-unsafe-auditor`) preload the corresponding skills.

## Assertions

### Compliance

- ALWAYS: follow the foundational + language-specific pattern — core principles in `/testing`, Rust-specific patterns in `/testing-rust` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- ALWAYS: the Rust plugin's testing skills (`/standardizing-rust-tests`, `/testing-rust`, `/auditing-rust-tests`) teach that test infrastructure (harnesses, generators, fixtures) lives in a separate workspace-member crate (e.g., `product-testing/` at workspace root, Cargo package `product-testing`, Rust import path `product_testing`), declared as a `[dev-dependencies]` entry of consumers, with modules `product_testing::harnesses::*`, `product_testing::generators::*`, `product_testing::fixtures::*` — per `spx/15-test-infrastructure.adr.md` ([review])
- NEVER: the Rust plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/fixtures/`, `crate::test_support`, `super::tests`, or any inside-`tests/` or in-crate location for shared harnesses, generators, or fixtures ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
- ALWAYS: `unsafe` blocks and FFI boundaries pass the soundness audit performed by `/rust-unsafe-auditor` — the audit covers aliasing, lifetimes, validity invariants, and panic safety ([review])
