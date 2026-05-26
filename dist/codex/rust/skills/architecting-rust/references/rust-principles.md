# Rust Architectural Principles

## Ownership and Borrowing Are Architecture

- Model ownership explicitly in ADRs for state, caches, handles, and domain aggregates
- Prefer single ownership by default; introduce `Arc`, `Rc`, interior mutability, or pools only when the use case requires them
- Treat borrowing boundaries as API design, not a compiler inconvenience
- Avoid architecture that relies on pervasive cloning to make flows compile

```rust
pub struct AppState {
    config: Arc<Config>,
    pool: PgPool,
}
```

## Type-Driven Invariants

- Prefer newtypes for domain identifiers and validated values
- Use type state or marker types when valid transitions matter
- Make invalid states unrepresentable where the domain rules are stable
- Keep runtime validation at boundaries, then trust validated types internally

```rust
pub struct Email(String);

impl Email {
    pub fn new(raw: &str) -> Result<Self, ValidationError> {
        validate_email(raw)?;
        Ok(Self(raw.to_owned()))
    }
}
```

## Clean Architecture in Rust

- Prefer traits at architectural seams and concrete types inside modules
- Inject dependencies through constructors or function parameters
- Keep command handlers, HTTP handlers, and adapters thin
- Use modules and visibility to enforce boundaries

```rust
pub trait Clock {
    fn now(&self) -> DateTime<Utc>;
}

pub struct Service<C: Clock> {
    clock: C,
}
```

## Error Boundaries Are a Design Decision

- Use typed errors at library and domain boundaries
- Use `thiserror` for structured public errors and `anyhow` for application orchestration when appropriate
- Decide explicitly which failures are retryable, degradable, user-facing, or fatal
- Convert infrastructure errors at boundaries instead of leaking crate-specific types upward

```rust
#[derive(thiserror::Error, Debug)]
pub enum CreateUserError {
    #[error("email already exists")]
    DuplicateEmail,
    #[error("storage failure")]
    Storage(#[source] sqlx::Error),
}
```

## Concurrency and Async Need Architectural Justification

- Choose async for I/O concurrency, not as a default style
- Choose threads or rayon for CPU-bound parallelism
- Document `Send`/`Sync` assumptions in shared state and background work
- Do not hold locks across `.await`

```rust
pub async fn handler(
    State(state): State<Arc<AppState>>,
) -> Result<Json<ResponseDto>, AppError> {
    Ok(Json(state.service.fetch().await?))
}
```

## Resource Lifecycle and RAII

- Treat connection pools, file handles, transactions, and guards as lifecycle decisions
- Use RAII and `Drop` for cleanup that must happen on scope exit
- Prefer lazy initialization only for truly application-wide state
- Document pooling, caching, and cleanup strategy in the ADR when resource cost matters

## Security and Unsafe Boundaries

- Validate external input at boundaries
- Keep secrets out of source and config defaults
- Isolate unsafe code behind small, documented safe wrappers
- Require explicit soundness reasoning for FFI, layout coupling, and raw pointer use

```rust
// SAFETY: ptr is valid for reads of len bytes and comes from the caller contract
unsafe { std::slice::from_raw_parts(ptr, len) }
```

## Crate Selection Is Architectural

- Treat runtime, web framework, serialization, persistence, and tracing crates as ADR-level choices
- Prefer mature crates with clear maintenance, compatibility, and feature-flag story
- Minimize architectural commitment to crates that leak through public APIs
- Record why a crate is chosen and what switching cost it creates
