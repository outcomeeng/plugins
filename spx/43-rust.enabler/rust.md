# Rust

PROVIDES the complete Rust development workflow — architecture, testing, implementation, review, and unsafe-code auditing
SO THAT Rust projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality and soundness

The rust plugin contains 9 skills following the foundational + language-specific pattern: `/rust-standards` (reference), `/rust-architecture-standards` (reference), `/rust-test-standards` (reference), `/test-rust`, `/code-rust`, `/audit-rust-code`, `/audit-rust-tests`, `/architect-rust`, `/audit-rust-architecture`. The `rust-simplifier` agent preloads its skill; the `audit-rust-{code|tests|architecture}` skills carry no language-specific auditor agent and are composed by the generic artifact-type auditors, per `spx/21-spec-tree.enabler/17-audit.adr.md`. Rust `unsafe`/FFI soundness is part of the Rust code audit (`audit-rust-code`).

## Assertions

### Compliance

- ALWAYS: the `audit-rust-{code|tests|architecture}` skills carry no Rust-specific auditor agent, name no caller, and stay invocable on their own; an artifact-type auditor composes them for the Rust concerns in scope, and the author-context isolation an audit verdict requires binds the author context per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, Rust-specific patterns in `/test-rust` ([review])
- ALWAYS: Rust test-standard specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the language-neutral seam rules — predicate ownership, semantic binding by choice, assertion-type case provenance, oracle independence, the controlled-collaborator verdict prohibition, and property-harness ownership — and declare only the Rust delta below rather than restating them ([review])
- ALWAYS: the Rust assertion API the executed `#[test]` or `#[tokio::test]` function owns is `assert!`, `assert_eq!`, `assert_ne!`, and `matches!`-based checks, and the Rust bindings judged by semantic choice are `let`, `const`, `static`, and closure or macro parameters ([review])
- ALWAYS: Rust test infrastructure lives in a separate workspace-member crate — `product-testing/` at workspace root, Cargo package `product-testing`, import path `product_testing`, declared as a `[dev-dependencies]` entry, with modules `product_testing::harnesses::*`, `product_testing::generators::*`, and `product_testing::fixtures::*` — the Rust realization of the test-infrastructure home the governing PDR mandates ([review])
- ALWAYS: Rust property tests draw their domains from `proptest` or `quickcheck`, and Rust controlled implementations and recording collaborators implement the same trait boundary as production while the linked test owns every predicate and assertion macro ([review])
- NEVER: the Rust plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/fixtures/`, `crate::test_support`, `super::tests`, or any inside-`tests/` or in-crate location for shared harnesses, generators, or fixtures ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
- ALWAYS: `unsafe` blocks and FFI boundaries pass the Rust code audit's soundness checks (`audit-rust-code`, composed by the implementation auditor) — covering aliasing, lifetimes, validity invariants, and panic safety ([review])
