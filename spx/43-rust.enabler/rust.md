# Rust

PROVIDES the complete Rust development workflow — architecture, testing, implementation, review, and unsafe-code auditing
SO THAT Rust projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality and soundness

The rust plugin contains 9 skills following the foundational + language-specific pattern: `/rust-standards` (reference), `/rust-architecture-standards` (reference), `/rust-test-standards` (reference), `/test-rust`, `/code-rust`, `/audit-rust-code`, `/audit-rust-tests`, `/architect-rust`, `/audit-rust-architecture`. The `rust-simplifier` agent preloads its skill; the `audit-rust-{code|tests|architecture}` skills carry no language-specific auditor agent and are composed by the generic artifact-type auditors. `implementation-auditor` composes the code, test, and architecture concern skills for implementation audits; `adr-auditor` and `test-evidence-auditor` compose the matching concern skills for decision and test-evidence audits, per `spx/21-spec-tree.enabler/17-audit.adr.md`. Rust `unsafe`/FFI soundness is part of the Rust code audit (`audit-rust-code`).

## Assertions

### Compliance

- ALWAYS: the `audit-rust-{code|tests|architecture}` skills carry no Rust-specific auditor agent and are composed by the generic artifact-type auditor for the Rust concerns in scope; the main conversation does not invoke them in place — the dispatched verifier's isolated context produces the verdict, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, Rust-specific patterns in `/test-rust` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- ALWAYS: the Rust plugin's testing skills (`/rust-test-standards`, `/test-rust`, `/audit-rust-tests`) teach that test infrastructure (harnesses, generators, fixtures) lives in a separate workspace-member crate (e.g., `product-testing/` at workspace root, Cargo package `product-testing`, Rust import path `product_testing`), declared as a `[dev-dependencies]` entry of consumers, with modules `product_testing::harnesses::*`, `product_testing::generators::*`, `product_testing::fixtures::*` — per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([review])
- ALWAYS: property-based Rust tests run through spec-governed harnesses that own seed selection, run count, replay input, and failure diagnostics, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([review])
- NEVER: executed Rust test files declare `const`, `static`, or `let` bindings; every value or configuration choice those declarations would bind lives in the `product-testing` workspace crate, source contracts, inert whole-payload fixtures, or justified eval case data ([review])
- NEVER: the Rust plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/fixtures/`, `crate::test_support`, `super::tests`, or any inside-`tests/` or in-crate location for shared harnesses, generators, or fixtures ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
- ALWAYS: `unsafe` blocks and FFI boundaries pass the Rust code audit's soundness checks (`audit-rust-code`, composed by the implementation auditor) — covering aliasing, lifetimes, validity invariants, and panic safety ([review])
