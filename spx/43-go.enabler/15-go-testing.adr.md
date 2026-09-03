# Go Testing

`go test` is the runner for Go `[test]` evidence and the default an omitted `<runner>` token names in the filename cell `<subject>.<evidence>.<level>[.<runner>]_test.go`. One `_test.go` file declares one assertion type and one execution level; `t.Run` subtests partition cases inside that cell and never combine cells. The executed `Test*` function owns every predicate through the `testing.T` failure API, and a `t.Helper()` mark removes an infrastructure frame from failure output without moving that ownership. Property evidence draws its domains from `pgregory.net/rapid`, whose generators compose and shrink and whose `rapid.Check` call owns seed selection, run count, and replay. Fixture payloads live under `internal/testinfra/fixtures/testdata/` and reach a test by path through the `fixtures` package, so the Go toolchain's `testdata` exclusion keeps violating source fixtures out of `go build ./...` and `go vet ./...` while the payloads stay inside the normative infrastructure home `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` declares; no other `testdata/` directory exists. `l2` and `l3` files carry a `//go:build l2` or `//go:build l3` constraint, so `go test ./...` runs `l1` alone and a heavier level is selected by `-tags`. The declared deterministic test command runs with `-race`. A missing mandatory dependency fails the test through `t.Fatal`; `t.Skip` is reserved for evidence the suite declares optional.

## Rationale

`go test` is the toolchain's own runner, so a second runner would add a dependency without adding evidence; a non-default runner token names a framework such as `ginkgo` only when a product declares one. Subtests keep table-driven cases readable, but a subtest that changes assertion type or execution level would smuggle two cells into one filename, which the cell declaration exists to prevent. `t.Helper()` is a diagnostic affordance the predicate seam in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` does not exempt: a helper that calls `t.Fatal` on the test's behalf has moved the predicate into infrastructure, and the mark then hides exactly the frame a reader needs. `testing/quick` is rejected for property evidence because it does not shrink, and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` requires a shrinking generator for a property cell; `rapid` shrinks, composes generators, and reports a replayable seed. A `.go` fixture that violates a rule is compiled by every `./...` invocation unless it sits under a `testdata` directory, so the fixture home nests the toolchain's ignore rule inside the normative path rather than adding a second fixture location the audit chain would have to traverse. Build constraints are the toolchain's own level selector: they keep `l1` the default without an environment variable or a skip, and `-race` on the declared command makes data-race safety deterministic evidence instead of an audit-only claim. Go's `internal/` rule already keeps `internal/testinfra` out of every importer outside the module, and importing it only from `_test.go` files keeps it out of every shipped binary.

## Invariants

- Every `_test.go` file names exactly one assertion type and one execution level.
- A `Test*` function that fails does so through a `testing.T` failure call written in that function or in the property closure it passes to `rapid.Check`.
- `go test ./...` with no tags runs only `l1` evidence.

## Verification

### Audit

- ALWAYS: Go skills teach `go test` as the default runner and the filename cell `<subject>.<evidence>.<level>[.<runner>]_test.go`, with a runner token only for a non-default runner the product declares ([audit])
- ALWAYS: Go skills teach that one `_test.go` file declares one assertion type and one execution level, and that `t.Run` subtests partition cases within that cell ([audit])
- ALWAYS: Go skills teach that a `t.Helper()`-marked function returns observations and never calls `t.Error`, `t.Errorf`, `t.Fatal`, or `t.Fatalf` on the executed test's behalf ([audit])
- ALWAYS: Go skills teach `pgregory.net/rapid` for property evidence, with generators in `internal/testinfra/generators/`, the invariant in the closure the executed test passes to `rapid.Check`, and seed, run count, and replay owned by the harness ([audit])
- ALWAYS: Go skills teach `internal/testinfra/fixtures/testdata/` as the sole fixture-payload location, reached by path through the `fixtures` package, with no other `testdata/` directory in the module ([audit])
- ALWAYS: Go skills teach `//go:build l2` and `//go:build l3` constraints on `l2` and `l3` files, so `go test ./...` runs `l1` alone ([audit])
- ALWAYS: Go skills teach the declared deterministic test command with `-race` ([audit])
- NEVER: Go skills teach `testing/quick` or another non-shrinking source for property evidence ([audit])
- NEVER: Go skills teach `t.Skip` for a missing mandatory dependency — a missing credential, binary, or service fails through `t.Fatal` unless the suite declares that evidence optional ([audit])
- NEVER: Go skills teach a `_test.go` file in a `tests/` directory, an in-package harness, or a `testdata/` directory outside `internal/testinfra/fixtures/` ([audit])
