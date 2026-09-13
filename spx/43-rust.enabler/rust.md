# Rust

PROVIDES the complete Rust development workflow — architecture, testing, implementation, review, and unsafe-code auditing
SO THAT Rust projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality and soundness

The Rust plugin composes foundational methodology with language-specific standards and workflows. Its `rust-simplifier` definition invokes `/simplify-rust` and relays its result. The `audit-rust-{code|tests|architecture}` skills carry no language-specific auditor agent and are composed by the generic artifact-type auditors, per `spx/21-spec-tree.enabler/17-audit.adr.md`. Rust `unsafe`/FFI soundness is part of the Rust code audit (`audit-rust-code`).

## Assertions

- ALWAYS: `/simplify-rust` owns the simplification contract for changed Rust implementation: independently discover scope and governing evidence, preserve behavior and ownership semantics, invoke `/code-rust` for edits, and report changed paths and verification results. Its instructions preserve tests and evidence, block changes lacking behavioral coverage, and limit recovery to its own edits ([audit])

### Compliance

- ALWAYS: the `audit-rust-{code|tests|architecture}` skills carry no Rust-specific auditor agent, name no caller, and stay invocable on their own; an artifact-type auditor composes them for the Rust concerns in scope, and the author-context isolation an audit verdict requires binds the author context per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, Rust-specific patterns in `/test-rust` ([audit])
- ALWAYS: Rust test-standard specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the language-neutral seam rules and declare only the Rust delta below ([audit])
- ALWAYS: the Rust assertion API the executed `#[test]` or `#[tokio::test]` function owns is `assert!`, `assert_eq!`, `assert_ne!`, `matches!`-based checks, and the `prop_assert*` family inside a property closure the function passes to its property harness; a compile-time conformance claim owns `trybuild` case registration — `pass` and `compile_fail` — in the executed function, where the compiler is the external oracle and the expected diagnostic is an inert fixture read by path; the Rust bindings judged by semantic choice are `let`, `const`, `static`, and closure or macro parameters ([audit])
- ALWAYS: Rust test infrastructure lives in a separate workspace-member crate — `product-testing/` at workspace root, Cargo package `product-testing`, import path `product_testing`, declared as a `[dev-dependencies]` entry, with modules `product_testing::harnesses::*`, `product_testing::generators::*`, and `product_testing::fixtures::*` ([audit])
- ALWAYS: Rust property tests draw their domains from `proptest` or `quickcheck`, and Rust controlled implementations and recording collaborators implement the same trait boundary as production ([audit])
- NEVER: the Rust plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/fixtures/`, `crate::test_support`, `super::tests`, or any inside-`tests/` or in-crate location for shared harnesses, generators, or fixtures ([audit])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([audit])
- ALWAYS: `unsafe` blocks and FFI boundaries pass the Rust code audit's soundness checks (`audit-rust-code`, composed by the implementation auditor) — covering aliasing, lifetimes, validity invariants, and panic safety ([audit])
