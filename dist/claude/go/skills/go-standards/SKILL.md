---
name: go-standards
user-invocable: false
description: >-
  Go code standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The canonical Go standards every Go skill enforces across implementation, testing, architecture, and review.
</objective>

<success_criteria>
Go work follows this standard when `gofmt -l .` prints nothing, `go vet ./...`, the repository's linter (`staticcheck ./...` or `golangci-lint run`), and `go test -race ./...` pass, review finds no row of `<anti_patterns>` present, and the code preserves meaningful type design, wrapped structured errors, explicit package boundaries, justified concurrency with context propagation, testable seams, and documented `unsafe` and cgo invariants, with repo-local overlays applied when present.
</success_criteria>

<reference_note>
This is a reference skill. Composing Go skills load these standards explicitly before writing, testing, or auditing. It is not a standalone workflow.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/go.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<standard_family>
Load `/go-standards` as the container before any specialized Go standard.

| Work area                  | Specialized standard         | Purpose                                                                                    |
| -------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------ |
| test code                  | `/go-test-standards`         | Go test filenames, levels, evidence rules, doubles, harnesses, fixtures, and examples      |
| ADRs and architecture docs | `/go-architecture-standards` | Go architecture decision structure, testability constraints, and architecture review rules |

Keep examples in standardizing skills. Task skills such as `/code-go`, `/test-go`, and `/audit-go-tests` describe workflow and load order; the standardizing family owns reusable policy and concrete examples.
</standard_family>

<tooling_baseline>

Go code follows the repository's actual toolchain. Unless a repo-local overlay states otherwise:

- formatting uses `gofmt` and `goimports`
- static analysis uses `go vet` and the repository's linter (`staticcheck` or `golangci-lint`)
- compilation and tests run through `go build` and `go test -race`
- public APIs and boundaries use explicit, named types

These standards are enforced by the compiler, vet, lint, and code review together. Passing one tool is not enough if the code still violates the architectural intent below.

</tooling_baseline>

<type_system>

Use the Go type system to encode meaning and constraints.

- prefer defined types for domain identifiers and validated values
- use typed constants with `iota` and a `String()` method instead of stringly-typed state
- return `(T, error)` and check the error at the call site; a zero value plus a `bool` is for lookups, never for failure
- keep exported signatures explicit and stable
- make invalid states unrepresentable through constructors that validate and unexported fields that hold the result

```go
// preferred
type UserID uint64

type JobStatus int

const (
    JobPending JobStatus = iota
    JobRunning
    JobFailed
    JobComplete
)

func (s JobStatus) String() string { /* ... */ }

// rejected
type UserID = uint64
var status string = "running"
```

</type_system>

<constant_patterns>

Choose the right Go construct for grouped constant values:

| Pattern                                                       | When to use                                                               |
| ------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `const Name Type = value`                                     | Simple scalar compile-time constant                                       |
| typed constants with `iota` and `String()`                    | Closed set of values with type safety — prefer over bare string constants |
| package-level `var` map initialized once, or `sync.OnceValue` | Map-like constants with complex initialization                            |

```go
// ✅ preferred: a typed set for a closed vocabulary
type GateStatus string

const (
    GatePass    GateStatus = "pass"
    GateFail    GateStatus = "fail"
    GateSkipped GateStatus = "skipped"
)

// AllGateStatuses is the source-owned enumeration a mapping test iterates.
var AllGateStatuses = []GateStatus{GatePass, GateFail, GateSkipped}

// ✅ preferred: a constant map built once
var defaultHeaders = sync.OnceValue(func() map[string]string {
    return map[string]string{
        "Content-Type": "application/json",
        "Accept":       "application/json",
    }
})

// ❌ rejected: scattered bare string constants without a type
const StatusPass = "pass"
const StatusFail = "fail"
```

**No re-export of library constants.** When production code and tests both need an HTTP status code, both import it from the same canonical source (`net/http`). Never create product-local aliases.

```go
// ❌ rejected: product-local re-export
const HTTPOK = 200

// ✅ preferred: both production and test code import from the canonical source
resp.StatusCode == http.StatusOK
```

</constant_patterns>

<values_pointers_and_sharing>

Value semantics are a design tool. Choose pointer receivers and shared state deliberately.

- use value receivers for small immutable types and pointer receivers when a method mutates or the type carries a mutex or large state; never mix receiver kinds on one type
- pass `context.Context` as the first parameter of every function that blocks, does I/O, or spawns work; never store it in a struct
- share mutable state through a channel or a single owning goroutine before reaching for `sync.Mutex`
- avoid package-level mutable variables; construct state and inject it
- document long-lived shared state in architecture-level decisions

```go
// preferred
func Render(ctx context.Context, cfg *Config) (Output, error) { /* ... */ }

// suspicious unless justified
var globalConfig *Config

func Render() Output { return render(globalConfig) }
```

</values_pointers_and_sharing>

<error_handling>

Error handling must preserve structure and intent.

- wrap with `fmt.Errorf("...: %w", err)` so callers can `errors.Is` and `errors.As`
- define sentinel errors (`var ErrMissing = errors.New(...)`) for conditions callers branch on, and error structs for conditions that carry data
- reserve `panic` for programmer errors and process-fatal startup requirements; never for expected failures
- check every error; never discard one with `_` outside a documented, deliberate case
- include enough context for operators and callers to act

```go
type LoadConfigError struct {
    Path string
    Err  error
}

func (e *LoadConfigError) Error() string { return "load config " + e.Path + ": " + e.Err.Error() }
func (e *LoadConfigError) Unwrap() error { return e.Err }

var ErrConfigMissing = errors.New("config file missing")
```

</error_handling>

<package_boundaries>

Use packages, exported identifiers, and `internal/` to enforce architecture.

- keep struct fields unexported unless external mutation is part of the contract
- expose constructors and behavior, not arbitrary mutation
- define interfaces where they are consumed, keep them small, and accept them as parameters; return concrete types
- keep adapters thin and domain logic isolated from transport, storage, and CLI glue
- place packages no other module may import under `internal/`

```go
type Account struct {
    balance Money
}

func (a *Account) Credit(amount Money) {
    a.balance += amount
}
```

</package_boundaries>

<concurrency_and_context>

Concurrency choices need justification, and every goroutine has an owner.

- every goroutine has a defined lifetime: it exits on context cancellation, channel close, or `errgroup` completion
- propagate `context.Context` and honor cancellation in every blocking call
- do not hold a mutex across a blocking call, channel operation, or callback
- prefer `errgroup.Group` or a `sync.WaitGroup` plus a results channel over unstructured `go` statements
- run the race detector in the declared test command

```go
// preferred
g, ctx := errgroup.WithContext(ctx)
for _, item := range items {
    g.Go(func() error { return process(ctx, item) })
}
if err := g.Wait(); err != nil {
    return err
}
```

</concurrency_and_context>

<testing_seams>

Code supports evidence-rich tests without generated mocks.

- inject external process runners, clocks, and boundary adapters through small interfaces or function parameters
- use small hand-written fakes when a controlled implementation is needed
- keep pure logic separable from boundary glue
- do not make `gomock`, `mockery`, `moq`, a `mock.Mock` embedding, or similar generated or framework mocks the default strategy

```go
type Clock interface {
    Now() time.Time
}

type Service struct {
    clock Clock
}

func NewService(clock Clock) *Service { return &Service{clock: clock} }
```

</testing_seams>

<unsafe_and_cgo>

`unsafe` and cgo are last-mile boundaries, not convenience features.

- keep `unsafe` uses narrow and behind a safe wrapper
- require a `// SAFETY:` comment tied to the actual invariant at every `unsafe.Pointer` conversion
- keep cgo calls in one package; convert to Go types at the boundary and free C memory in the same package
- prefer `encoding/binary`, `bytes`, and typed slices over pointer arithmetic

```go
// SAFETY: b is a live slice of len bytes the caller keeps reachable for the call's duration.
s := unsafe.String(unsafe.SliceData(b), len(b))
```

</unsafe_and_cgo>

<tool_preferences>

Prefer Go-native tools and idioms unless a repo-local overlay says otherwise:

- `flag` or `cobra` for CLI parsing
- `encoding/json` for serialization
- `log/slog` for structured observability
- `t.TempDir()` for tempdir-backed tests
- `os/exec` against a harness-built binary for CLI tests
- `pgregory.net/rapid` for property testing
- `github.com/google/go-cmp/cmp` for structural diffs in assertions
- `net/http/httptest` for HTTP boundaries
- `testcontainers-go` for local services

</tool_preferences>

<anti_patterns>

| Anti-pattern                                     | Why it is rejected                                |
| ------------------------------------------------ | ------------------------------------------------- |
| stringly-typed domain states                     | loses invariants and discoverability              |
| `context.Context` stored in a struct             | hides lifetime and cancellation from callers      |
| discarded errors (`_ = f()`) in production paths | turns expected failures into silent corruption    |
| exported mutable fields by default               | breaks encapsulation and invariant control        |
| a mutex held across a blocking call              | deadlock and contention risk                      |
| a goroutine with no exit condition               | leaks and unbounded resource growth               |
| generated mocks as the default seam              | weakens evidence and severs reality-based testing |
| `unsafe` used to bypass type design              | replaces clear design with soundness risk         |

</anti_patterns>
