# Go Architectural Principles

## Contents

- Packages Are Architecture
- Type-Driven Invariants
- Clean Architecture in Go
- Error Boundaries Are a Design Decision
- Concurrency Needs an Owner
- Resource Lifecycle and Close
- Security and Unsafe Boundaries
- Module Selection Is Architectural

## Packages Are Architecture

- Model ownership explicitly in ADRs: which package owns each concern, and what stays under `internal/`
- Define interfaces where they are consumed; keep them small; return concrete types
- Treat exported surface as API design, not a convenience
- Avoid architecture that relies on package-level mutable state to make flows compile

```go
package users

type Store interface {
    Load(ctx context.Context, id UserID) (User, error)
}
```

## Type-Driven Invariants

- Prefer defined types for domain identifiers and validated values
- Use typed constant sets with `iota` when a closed vocabulary matters
- Make invalid states unrepresentable through validating constructors and unexported fields
- Keep runtime validation at boundaries, then trust validated types internally

```go
type Email struct{ raw string }

func NewEmail(raw string) (Email, error) {
    if err := validateEmail(raw); err != nil {
        return Email{}, err
    }
    return Email{raw: raw}, nil
}
```

## Clean Architecture in Go

- Prefer interfaces at architectural seams and concrete types inside packages
- Inject dependencies through constructors or function parameters
- Keep command handlers, HTTP handlers, and adapters thin
- Use packages and `internal/` to enforce boundaries

```go
type Clock interface {
    Now() time.Time
}

type Service struct {
    clock Clock
}

func NewService(clock Clock) *Service { return &Service{clock: clock} }
```

## Error Boundaries Are a Design Decision

- Use sentinel errors for conditions callers branch on and error structs for conditions that carry data
- Wrap with `%w` at every boundary so `errors.Is` and `errors.As` resolve through the chain
- Decide explicitly which failures are retryable, degradable, user-facing, or fatal
- Convert infrastructure errors at boundaries instead of leaking driver types upward unwrapped

```go
var ErrDuplicateEmail = errors.New("email already exists")

type StorageError struct{ Err error }

func (e *StorageError) Error() string { return "storage: " + e.Err.Error() }
func (e *StorageError) Unwrap() error { return e.Err }
```

## Concurrency Needs an Owner

- Every goroutine has an owner, a `context.Context`, and an exit condition
- Choose `errgroup` or a `sync.WaitGroup` with a results channel for fan-out
- Move shared state through channels or one owning goroutine before adding a mutex
- Do not hold a mutex across a blocking call

```go
func (s *Service) Handle(ctx context.Context, items []Item) error {
    g, ctx := errgroup.WithContext(ctx)
    for _, item := range items {
        g.Go(func() error { return s.process(ctx, item) })
    }
    return g.Wait()
}
```

## Resource Lifecycle and Close

- Treat connection pools, file handles, transactions, and listeners as lifecycle decisions
- Expose a `Close` method the caller defers; never rely on finalizers for correctness
- Prefer `sync.Once` or `sync.OnceValue` for application-wide initialization
- Document pooling, caching, and cleanup strategy in the ADR when resource cost matters

## Security and Unsafe Boundaries

- Validate external input at boundaries
- Keep secrets out of source and config defaults
- Isolate `unsafe` and cgo behind small, documented safe wrappers in one package
- Require explicit soundness reasoning for `unsafe.Pointer` conversions and C memory ownership

```go
// SAFETY: b stays reachable for the duration of the call, so the string never outlives its bytes.
s := unsafe.String(unsafe.SliceData(b), len(b))
```

## Module Selection Is Architectural

- Treat HTTP framework, serialization, persistence, and logging modules as ADR-level choices
- Prefer the standard library where it suffices, then mature modules with clear maintenance and compatibility stories
- Minimize architectural commitment to modules that leak through exported APIs
- Record why a module is chosen and what switching cost it creates
