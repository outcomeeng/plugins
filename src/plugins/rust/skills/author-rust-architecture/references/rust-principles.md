# Rust Architectural Decision Prompts

Each section names the decisions an ADR records when its subject touches that concern. Record a decision only when the governed code depends on it; omit a section the ADR does not touch.

## Contents

- Ownership and Borrowing
- Type-Driven Invariants
- Seams and Dependency Injection
- Error Boundaries
- Concurrency and Async
- Resource Lifecycle
- Security and Unsafe Boundaries
- Crate Selection

## Ownership and Borrowing

- Which component owns each piece of shared state, cache, handle, and aggregate
- Where shared ownership or interior mutability is justified by a use case rather than by compiler friction
- Which borrowing boundaries are part of a public API

## Type-Driven Invariants

- Which invariants live in newtypes, type-state transitions, or validated constructors
- Which validation stays at the boundary, with validated types trusted internally

## Seams and Dependency Injection

- Which traits mark architectural seams
- How dependencies reach the code: constructors or function parameters
- Which controlled implementations tests inject in place of mocks

## Error Boundaries

- Which layers define typed errors and which orchestration layers collect them
- Which failures are retryable, degradable, user-facing, or fatal
- Where infrastructure errors convert so crate-specific types stop at the boundary

## Concurrency and Async

- Which workloads are I/O-bound and which are CPU-bound, with the runtime or threading model each implies
- The `Send` and `Sync` assumptions of shared state and background work

## Resource Lifecycle

- Which pools, handles, transactions, and guards have lifecycle rules, and who creates and releases each
- Which initialization is application-wide

## Security and Unsafe Boundaries

- Which inputs cross a trust boundary and where validation happens
- Which modules confine unsafe code, FFI, or layout coupling, with the soundness reasoning each requires

## Crate Selection

- Which runtime, web, serialization, persistence, and tracing crates the ADR commits the product to
- Which of those crates leak through public APIs, and the switching cost each creates
