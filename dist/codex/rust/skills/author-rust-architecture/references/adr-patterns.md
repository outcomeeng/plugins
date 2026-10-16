# Common ADR Patterns for Rust

These patterns show how testability constraints appear under the `## Verification` section's `### Audit` subsection. See `/rust-architecture-standards` for the canonical ADR section structure.

## Contents

- Pattern: External Tool Integration
- Pattern: Configuration Loading
- Pattern: CLI Structure
- Pattern: Error Handling
- Pattern: Async Operations
- Pattern: Unsafe or FFI Boundary

Each pattern carries its own `## Verification` section with an `### Audit` subsection.

## Pattern: External Tool Integration

When integrating with external tools:

```markdown
# External Tool Integration

Use dependency injection for all external tool invocations.

## Verification

### Audit

- ALWAYS: functions that call external tools accept a dependency parameter with a typed interface -- enables isolated testing of command-building logic ([audit])
- ALWAYS: default implementations use real tools; tests inject controlled implementations -- no mocking ([audit])
- NEVER: direct `std::process::Command` construction in core domain logic without an injected seam -- prevents isolated testing ([audit])
```

## Pattern: Configuration Loading

When defining configuration approach:

```markdown
# Configuration Loading

Use typed configuration structs with boundary validation and fail-fast loading.

## Verification

### Audit

- ALWAYS: config files map to typed Rust structs with explicit validation rules -- ensures validated config ([audit])
- ALWAYS: config loading validates at load time through constructors, `TryFrom`, or deserializer validation -- fail fast with descriptive errors ([audit])
- NEVER: unvalidated config access at use time -- defers errors to runtime ([audit])
- NEVER: `unwrap()` on untrusted config fields in production paths -- hides configuration defects ([audit])
```

## Pattern: CLI Structure

When defining CLI architecture:

```markdown
# CLI Structure

Use `clap` derive with thin command handlers and delegated runners.

## Verification

### Audit

- ALWAYS: each command is represented by typed `Parser` / `Subcommand` structs or enums -- enables explicit command contracts ([audit])
- ALWAYS: command handlers delegate to runner functions or services that accept injected dependencies -- separates parsing from logic ([audit])
- NEVER: business logic in command handlers -- prevents isolated testing ([audit])
- NEVER: direct I/O in command modules without DI -- couples commands to environment ([audit])
```

## Pattern: Error Handling

When defining error handling approach:

```markdown
# Error Handling

Use typed error enums with explicit boundary conversions.

## Verification

### Audit

- ALWAYS: domain and library boundaries define typed error enums or structs -- enables programmatic handling ([audit])
- ALWAYS: error messages are user-facing and actionable at the presentation boundary -- no raw internals in output ([audit])
- ALWAYS: infrastructure errors are converted at layer boundaries instead of leaking crate-specific types upward ([audit])
- NEVER: using stringly-typed errors or ad hoc `panic!` for expected failures -- loses structure ([audit])
- NEVER: swallowing errors without logging or propagation -- hides failures ([audit])
```

## Pattern: Async Operations

When defining async patterns:

```markdown
# Async Operations

Use async only for I/O-bound concurrency, with explicit error handling and timeouts.

## Verification

### Audit

- ALWAYS: async functions have explicit return types -- keeps boundary contracts readable ([audit])
- ALWAYS: timeouts are configurable via injected policy or typed configuration -- enables testing of timeout logic ([audit])
- ALWAYS: errors are converted to typed boundary errors rather than leaked as runtime-specific details -- structured propagation ([audit])
- ALWAYS: shared async state uses `Send`/`Sync` safe types where cross-task or cross-thread access is required ([audit])
- NEVER: blocking calls inside async request paths without an explicit offload strategy -- harms latency and throughput ([audit])
- NEVER: holding locks across `.await` points -- creates deadlock and contention risks ([audit])
- NEVER: hardcoded timeout values -- prevents testing and configuration ([audit])
```

## Pattern: Unsafe or FFI Boundary

When defining unsafe code or interop boundaries:

```markdown
# Unsafe or FFI Boundary

Confine unsafe operations to narrow modules with documented safety contracts and safe wrappers.

## Verification

### Audit

- ALWAYS: every unsafe block carries a `SAFETY:` explanation tied to the actual invariant being relied on ([audit])
- ALWAYS: FFI and layout assumptions are isolated behind small wrappers with explicit ownership and lifetime contracts ([audit])
- NEVER: using unsafe as a shortcut around ownership or borrowing design problems ([audit])
- NEVER: exposing raw pointers or layout-sensitive details directly to high-level application code without a documented boundary ([audit])
```
