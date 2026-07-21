# Rust

PROVIDES the complete Rust development workflow — architecture, testing, implementation, review, and unsafe-code auditing
SO THAT Rust projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality and soundness

The rust plugin contains 9 skills following the foundational + language-specific pattern: `/rust-standards` (reference), `/rust-architecture-standards` (reference), `/rust-test-standards` (reference), `/test-rust`, `/code-rust`, `/audit-rust-code`, `/audit-rust-tests`, `/architect-rust`, `/audit-rust-architecture`. The `rust-simplifier` agent preloads its skill; the `audit-rust-{code|tests|architecture}` skills carry no language-specific auditor agent and are composed by the generic artifact-type auditors, per `spx/21-spec-tree.enabler/17-audit.adr.md`. Rust `unsafe`/FFI soundness is part of the Rust code audit (`audit-rust-code`).

## Assertions

### Compliance

- ALWAYS: the `audit-rust-{code|tests|architecture}` skills carry no Rust-specific auditor agent, name no caller, and stay invocable on their own; an artifact-type auditor composes them for the Rust concerns in scope, and the author-context isolation an audit verdict requires binds the author context per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, Rust-specific patterns in `/test-rust` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- ALWAYS: the Rust plugin's testing skills (`/rust-test-standards`, `/test-rust`, `/audit-rust-tests`) teach that test infrastructure (harnesses, generators, fixtures) lives in a separate workspace-member crate (e.g., `product-testing/` at workspace root, Cargo package `product-testing`, Rust import path `product_testing`), declared as a `[dev-dependencies]` entry of consumers, with modules `product_testing::harnesses::*`, `product_testing::generators::*`, `product_testing::fixtures::*` — per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([review])
- ALWAYS: property-based Rust tests run through spec-governed harnesses that own seed selection, run count, replay input, and failure diagnostics, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([review])
- ALWAYS: executed `#[test]` and `#[tokio::test]` functions own every behavioral predicate and assertion macro call (`assert!`, `assert_eq!`, `assert_ne!`, `matches!`-based checks); imported harnesses and recording collaborators expose observations rather than verdicts ([review])
- ALWAYS: executed Rust test-file bindings (`let`, `const`, `static`, closure or macro parameters) are valid when they only receive or rename an actual result, source-owned contract, generated value, harness observation, or resource handle and introduce no data or policy; a binding that chooses case data, an expected output, a runner setting, a seed, setup policy, a fixture payload, or a generator domain belongs in the `product-testing` workspace crate, source contracts, inert whole-payload fixtures, or justified eval case data ([review])
- ALWAYS: controlled implementations and recording collaborators implement the same trait boundary as production, preserve behavior-relevant state, and expose observations while the linked test owns every predicate and assertion macro ([review])
- ALWAYS: every test case — input and expected output — derives from a source independent of the test author's invention: the spec scenario, a finite source-owned enumeration, a `proptest`/`quickcheck` domain, an external conformance oracle, the governing compliance rule, or an inert whole-payload fixture ([review])
- ALWAYS: expected outputs for generated inputs derive from the input, an independent oracle, or a source outside the crate under test — tests do not copy expected data from the same implementation they verify ([review])
- NEVER: a controlled implementation or recording collaborator accepts an expected outcome, calls an assertion macro, exposes a matcher-style verdict method, or replaces the behavior the assertion claims to verify ([review])
- NEVER: derive an expected output through the implementation table, algorithm, parser, or branch logic that produces the actual output — the expected output comes from an independent oracle ([review])
- NEVER: the Rust plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/fixtures/`, `crate::test_support`, `super::tests`, or any inside-`tests/` or in-crate location for shared harnesses, generators, or fixtures ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
- ALWAYS: `unsafe` blocks and FFI boundaries pass the Rust code audit's soundness checks (`audit-rust-code`, composed by the implementation auditor) — covering aliasing, lifetimes, validity invariants, and panic safety ([review])
