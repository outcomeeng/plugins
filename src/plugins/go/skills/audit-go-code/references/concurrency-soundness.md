# Concurrency Soundness Audit

Soundness audit for goroutines, channels, `sync` primitives, and `context.Context` propagation — the leaks, deadlocks, and lost cancellations `go vet` and the race detector do not report. Claude runs this pass as part of `/audit-go-code` whenever the scope contains a `go` statement, a channel operation, a `sync` primitive, or a function that accepts a `context.Context`; a scope with no such sites skips it.

A single soundness violation rejects the audit. Claude never approves a goroutine that has no exit condition, and never accepts a workaround that hides the leak behind a timeout the caller cannot configure.

## Enumerate concurrency sites

Collect every site before judging any of them:

```bash
grep -rn "go func\|go [a-zA-Z_.]*(\|make(chan\|sync\.\(Mutex\|RWMutex\|WaitGroup\|Once\)\|errgroup\.\|context\.Context" <scope> --include="*.go" | grep -v "_test.go"
```

Count each goroutine launch, channel, mutex, wait group, and context-accepting function. The verdict's `concurrency-soundness` row reports the totals.

## Per-goroutine checks

For each `go` statement:

1. **Owner named.** The launching function, an `errgroup.Group`, or a `sync.WaitGroup` owns the goroutine and waits for it or observes its exit. An unowned `go` statement is a violation — reject.
2. **Exit condition present.** The goroutine returns on context cancellation, channel close, or completion of bounded work. A `for {}` or `for range ch` with no cancellation path and no close is a violation.
3. **Panic containment.** A goroutine that can panic in production paths recovers or the program's crash policy documents that it aborts; an unhandled panic in a background goroutine takes the process down silently.

## Per-context checks

For each function that accepts a `context.Context`:

1. **Propagated.** Every blocking call and every launched goroutine receives the context or a child of it. A blocking call that ignores it loses cancellation.
2. **Not stored.** The context is never stored in a struct field; it flows through parameters.
3. **Timeouts configurable.** A `context.WithTimeout` inside the function uses an injected or configured duration, never a literal the caller cannot change.

## Per-mutex checks

For each `sync.Mutex` or `sync.RWMutex`:

1. **Not held across blocking.** No I/O, channel operation, callback, or lock acquisition of another mutex happens while this one is held.
2. **Consistent receiver.** The type holding the mutex uses pointer receivers throughout; a value receiver copies the lock.
3. **One owner per state.** Shared state has one owning goroutine or one mutex; two mutexes guarding overlapping state is a violation unless a documented lock order exists.

## Hazard categories

| Category     | Rule prefix | Hazard                                                                      |
| ------------ | ----------- | --------------------------------------------------------------------------- |
| Leak         | `goroutine-*` | Goroutine with no owner or no exit condition                              |
| Cancellation | `context-*`   | Context not propagated, stored in a struct, or timeout hardcoded          |
| Deadlock     | `mutex-*`     | Lock held across a blocking call, lock copied by value, undocumented lock order |
| Race         | `race-*`      | Shared state mutated from two goroutines without a channel, mutex, or atomic |

Record each violation as a finding with `file`, `line`, the rule prefix, and the exact invariant that fails.

## Verdict row

The audit folds a `concurrency-soundness` row into the JSON verdict: `PASS` when every site is sound, `FAIL` on any violation, and `NOT_APPLICABLE` when the scope has no concurrency sites. A `NOT_APPLICABLE` row carries `explanation` naming why the concern does not apply. Findings use `blocking` or `debt` severity and name the site, `file:line`, rule prefix, failed invariant, and observed-versus-expected evidence.
