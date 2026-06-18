# Rust

PROVIDES the complete Rust development workflow — architecture, testing, implementation, review, and unsafe-code auditing
SO THAT Rust projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality and soundness

The rust plugin contains 9 skills following the foundational + language-specific pattern: `/rust-standards` (reference), `/rust-architecture-standards` (reference), `/rust-test-standards` (reference), `/test-rust`, `/code-rust`, `/audit-rust`, `/audit-rust-tests`, `/architect-rust`, `/audit-rust-architecture`. Five agents (`rust-code-auditor`, `rust-architecture-auditor`, `rust-test-auditor`, `rust-simplifier`, `rust-unsafe-auditor`) preload the corresponding skills.

## Assertions

### Compliance

- ALWAYS: the `audit-rust*` skills are reached only by dispatching their auditor agent (`rust-code-auditor`, `rust-test-auditor`, `rust-architecture-auditor`, `rust-unsafe-auditor`); the main conversation does not invoke them in place — the agent's isolated context produces the verdict, per `spx/14-verification.pdr.md` ([review])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, Rust-specific patterns in `/test-rust` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- ALWAYS: the Rust plugin's testing skills (`/rust-test-standards`, `/test-rust`, `/audit-rust-tests`) teach that test infrastructure (harnesses, generators, fixtures) lives in a separate workspace-member crate (e.g., `product-testing/` at workspace root, Cargo package `product-testing`, Rust import path `product_testing`), declared as a `[dev-dependencies]` entry of consumers, with modules `product_testing::harnesses::*`, `product_testing::generators::*`, `product_testing::fixtures::*` — per `spx/15-test-infrastructure.pdr.md` ([review])
- NEVER: the Rust plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/fixtures/`, `crate::test_support`, `super::tests`, or any inside-`tests/` or in-crate location for shared harnesses, generators, or fixtures ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
- ALWAYS: `unsafe` blocks and FFI boundaries pass the soundness audit performed by `/rust-unsafe-auditor` — the audit covers aliasing, lifetimes, validity invariants, and panic safety ([review])
