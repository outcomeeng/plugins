---
name: standardizing-rust
disable-model-invocation: true
description: Rust code standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical Rust standards for implementation, testing, architecture, and review. Defines the baseline expectations for type usage, ownership, error handling, module boundaries, async design, testing seams, and unsafe code, and routes specialized Rust standards to the reference skills that contain their examples.
</objective>

<success_criteria>
Rust work follows this standard when `/standardizing-rust` is loaded first, relevant specialized Rust standards are loaded next, repo-local overlays are applied, and implementation or audit decisions can cite the applicable standard section.
</success_criteria>

<reference_note>
This is a reference skill. Other Rust skills load these standards automatically. Invoke `/coding-rust`, `/testing-rust`, `/auditing-rust`, or related Rust skills rather than invoking this directly.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/rust.md` at the repository root. Read that file after this reference if it exists and apply it as the repo-local specialization.
</repo_local_overlay>

<standard_family>
Load `/standardizing-rust` as the container before any specialized Rust standard.

| Work area                  | Specialized standard               | Purpose                                                                                      |
| -------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------- |
| test code                  | `/standardizing-rust-tests`        | Rust test filenames, levels, evidence rules, doubles, harnesses, fixtures, and examples      |
| ADRs and architecture docs | `/standardizing-rust-architecture` | Rust architecture decision structure, testability constraints, and architecture review rules |

Keep examples in standardizing skills. Task skills such as `/coding-rust`, `/testing-rust`, and `/auditing-rust-tests` describe workflow and load order; the standardizing family owns reusable policy and concrete examples.
</standard_family>

<tooling_baseline>

Rust code follows the repository's actual toolchain. Unless a repo-local overlay states otherwise:

- formatting uses `rustfmt`
- linting uses `clippy`
- compilation and tests run through `cargo`
- public APIs and boundaries use explicit types

These standards are enforced by compiler checks, linting, and code review together. Passing one tool is not enough if the code still violates the architectural intent below.

</tooling_baseline>

<type_system>

Use the Rust type system to encode meaning and constraints.

- prefer newtypes for domain identifiers and validated values
- use enums instead of stringly-typed state
- use `Option` and `Result` deliberately; do not collapse them into booleans or sentinel values
- keep public signatures explicit and stable
- make invalid states unrepresentable when the domain rules are stable

```rust
// preferred
pub struct UserId(u64);

pub enum JobStatus {
    Pending,
    Running,
    Failed,
    Complete,
}

// rejected
pub type UserId = u64;
pub type JobStatus = String;
```

</type_system>

<ownership_and_borrowing>

Ownership is a design tool, not a compiler obstacle.

- prefer single ownership by default
- borrow when the callee does not need ownership
- introduce `Arc`, `Rc`, `Mutex`, `RwLock`, or interior mutability only when the use case requires them
- avoid clone-driven designs that hide unclear data flow
- document long-lived shared state in architecture-level decisions

```rust
// preferred
pub fn render(config: &Config) -> Output { /* ... */ }

// suspicious unless justified
pub fn render(config: Config) -> Output {
    let config = config.clone();
    /* ... */
}
```

</ownership_and_borrowing>

<error_handling>

Error handling must preserve structure and intent.

- use typed errors at domain and library boundaries
- use `thiserror` for structured public errors when it helps consumers
- use `anyhow` for application orchestration when the boundary is not public
- reserve `panic!`, `unwrap()`, and `expect()` for invariants, tests, or process-fatal startup requirements
- include enough context for operators and callers to act

```rust
#[derive(thiserror::Error, Debug)]
pub enum LoadConfigError {
    #[error("missing config file at {0}")]
    Missing(PathBuf),
    #[error("invalid config format")]
    Invalid(#[source] serde_yaml::Error),
}
```

</error_handling>

<module_boundaries>

Use modules and visibility to enforce architecture.

- keep fields private unless external mutation is part of the contract
- expose constructors and behavior, not arbitrary mutation
- keep adapters thin and domain logic isolated from transport, storage, and CLI glue
- prefer traits at true architectural seams; avoid trait abstraction when a concrete type is enough

```rust
pub struct Account {
    balance: Money,
}

impl Account {
    pub fn credit(&mut self, amount: Money) {
        self.balance += amount;
    }
}
```

</module_boundaries>

<async_and_concurrency>

Async and concurrency choices need justification.

- use async for I/O-bound concurrency
- use threads or data parallelism for CPU-bound work
- do not hold locks across `.await`
- document `Send` and `Sync` assumptions in shared state
- prefer channels or ownership transfer over unnecessary shared mutable state

```rust
// preferred
let item = {
    let mut guard = state.queue.lock().await;
    guard.pop_front()
};
process(item).await;
```

</async_and_concurrency>

<testing_seams>

Code should support evidence-rich tests without framework mocks.

- inject external process runners, clocks, and boundary adapters through traits or narrow function parameters
- use small hand-written doubles when a controlled implementation is needed
- keep pure logic separable from boundary glue
- do not make `mockall` or similar generated mocks the default strategy

```rust
pub trait Clock {
    fn now(&self) -> DateTime<Utc>;
}

pub struct Service<C: Clock> {
    clock: C,
}
```

</testing_seams>

<unsafe_and_ffi>

Unsafe code is a last-mile boundary, not a convenience feature.

- keep unsafe blocks narrow
- require `SAFETY:` comments tied to the actual invariant
- isolate FFI and raw pointer handling behind safe wrappers where possible
- prefer `MaybeUninit`, `NonNull`, and typed wrappers over ad hoc pointer manipulation

```rust
// SAFETY: ptr is non-null, aligned, and valid for len initialized bytes.
let slice = unsafe { std::slice::from_raw_parts(ptr, len) };
```

</unsafe_and_ffi>

<tool_preferences>

Prefer Rust-native tools and idioms unless a repo-local overlay says otherwise:

- `clap` for CLI parsing
- `serde` for serialization
- `tracing` for structured observability
- `tempfile` for tempdir-backed tests
- `assert_cmd` for CLI integration tests
- `proptest` or `quickcheck` for property testing
- `trybuild` for compile-time contracts

</tool_preferences>

<anti_patterns>

| Anti-pattern                            | Why it is rejected                                |
| --------------------------------------- | ------------------------------------------------- |
| stringly-typed domain states            | loses invariants and discoverability              |
| clone-heavy data flow                   | hides unclear ownership design                    |
| `unwrap()` in ordinary production paths | turns expected failures into crashes              |
| public mutable fields by default        | breaks encapsulation and invariant control        |
| locks held across `.await`              | deadlock and contention risk                      |
| generated mocks as the default seam     | weakens evidence and severs reality-based testing |
| unsafe used to bypass ownership design  | replaces clear design with soundness risk         |

</anti_patterns>
