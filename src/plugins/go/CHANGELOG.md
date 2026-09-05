# Changelog — go plugin

Go engineering: coding, testing, architecture, the matching concern audits, and the `go-simplifier` agent.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.1.0

### Added

- **The Go language plugin.** Nine skills at parity with the python, rust, and typescript plugins — `/go-standards`, `/go-test-standards`, `/go-architecture-standards`, `/test-go`, `/code-go`, `/architect-go`, `/audit-go-code`, `/audit-go-tests`, `/audit-go-architecture` — plus the `go-simplifier` agent and the lifecycle skill every plugin ships. A Go product's test-evidence, implementation, and ADR auditors compose these skills, and `/apply` resolves `go` at language detection.
- **Go test conventions.** `go test` is the default runner; a test file declares its cell as `<subject>.<evidence>.<level>[.<runner>]_test.go`; Level 2 and Level 3 files carry `//go:build l2` and `//go:build l3`; property evidence runs through a harness over `pgregory.net/rapid`; compile-time claims use the toolchain as the oracle.
- **Test infrastructure home.** Harnesses, generators, and fixture resolvers live in `internal/testinfra/` (package `testinfra`, never `test`), with fixture payloads under `internal/testinfra/fixtures/testdata/` so the toolchain ignores violating source fixtures.
- **Concurrency and unsafe soundness in the code audit.** `/audit-go-code` carries a `concurrency-soundness` row for goroutine ownership, context propagation, mutex discipline, and races, and an `unsafe-soundness` row for `unsafe` conversions and cgo boundaries.

This changelog begins here.
