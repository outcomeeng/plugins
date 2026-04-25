# Common ADR Patterns for Rust

These patterns show how testability constraints appear in the Compliance section. See `/standardizing-rust-architecture` for the canonical ADR section structure.

## Pattern: External Tool Integration

When integrating with external tools:

```markdown
## Decision

Use dependency injection for all external tool invocations.

## Compliance

### Recognized by

Observable dependency parameter in all functions that invoke external tools.

### MUST

- All functions that call external tools accept a dependency parameter with a typed interface -- enables isolated testing of command-building logic ([review])
- Default implementations use real tools; tests inject controlled implementations -- no mocking ([review])

### NEVER

- Direct `std::process::Command` construction in core domain logic without an injected seam -- prevents isolated testing ([review])
```

## Pattern: Configuration Loading

When defining configuration approach:

```markdown
## Decision

Use typed configuration structs with boundary validation and fail-fast loading.

## Compliance

### Recognized by

Typed config struct accompanying every config source. Validation happens at load time, not use time.

### MUST

- All config files map to typed Rust structs with explicit validation rules -- ensures validated config ([review])
- Config loading validates at load time through constructors, `TryFrom`, or deserializer validation -- fail fast with descriptive errors ([review])

### NEVER

- Unvalidated config access at use time -- defers errors to runtime ([review])
- `unwrap()` on untrusted config fields in production paths -- hides configuration defects ([review])
```

## Pattern: CLI Structure

When defining CLI architecture:

```markdown
## Decision

Use `clap` derive with thin command handlers and delegated runners.

## Compliance

### Recognized by

Separate module per command or subcommand. Business logic delegated to application services or runners.

### MUST

- Each command is represented by typed `Parser` / `Subcommand` structs or enums -- enables explicit command contracts ([review])
- Command handlers delegate to runner functions or services that accept injected dependencies -- separates parsing from logic ([review])

### NEVER

- Business logic in command handlers -- prevents isolated testing ([review])
- Direct I/O in command modules without DI -- couples commands to environment ([review])
```

## Pattern: Error Handling

When defining error handling approach:

```markdown
## Decision

Use typed error enums with explicit boundary conversions.

## Compliance

### Recognized by

Errors are modeled as enums or structured types. Boundary adapters convert them for CLI, HTTP, or storage layers.

### MUST

- Domain and library boundaries define typed error enums or structs -- enables programmatic handling ([review])
- Error messages are user-facing and actionable at the presentation boundary -- no raw internals in output ([review])
- Infrastructure errors are converted at layer boundaries instead of leaking crate-specific types upward ([review])

### NEVER

- Using stringly-typed errors or ad hoc `panic!` for expected failures -- loses structure ([review])
- Swallowing errors without logging or propagation -- hides failures ([review])
```

## Pattern: Async Operations

When defining async patterns:

```markdown
## Decision

Use async only for I/O-bound concurrency, with explicit error handling and timeouts.

## Compliance

### Recognized by

Explicit return types on all async functions. Timeouts configurable at boundaries.

### MUST

- All async functions have explicit return types -- keeps boundary contracts readable ([review])
- Timeouts are configurable via injected policy or typed configuration -- enables testing of timeout logic ([review])
- Errors are converted to typed boundary errors rather than leaked as runtime-specific details -- structured propagation ([review])
- Shared async state uses `Send`/`Sync` safe types where cross-task or cross-thread access is required ([review])

### NEVER

- Blocking calls inside async request paths without an explicit offload strategy -- harms latency and throughput ([review])
- Holding locks across `.await` points -- creates deadlock and contention risks ([review])
- Hardcoded timeout values -- prevents testing and configuration ([review])
```

## Pattern: Unsafe or FFI Boundary

When defining unsafe code or interop boundaries:

```markdown
## Decision

Confine unsafe operations to narrow modules with documented safety contracts and safe wrappers.

## Compliance

### Recognized by

Unsafe code lives in dedicated modules. Public APIs expose safe wrappers or explicitly documented `unsafe fn` contracts.

### MUST

- Every unsafe block carries a `SAFETY:` explanation tied to the actual invariant being relied on ([review])
- FFI and layout assumptions are isolated behind small wrappers with explicit ownership and lifetime contracts ([review])

### NEVER

- Using unsafe as a shortcut around ownership or borrowing design problems ([review])
- Exposing raw pointers or layout-sensitive details directly to high-level application code without a documented boundary ([review])
```
