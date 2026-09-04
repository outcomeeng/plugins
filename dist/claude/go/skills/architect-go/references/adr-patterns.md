<overview>
These patterns show how testability constraints appear under the `## Verification` section's `### Audit` subsection. See `/go-architecture-standards` for the canonical ADR section structure.

Each pattern carries its own `## Verification` section with an `### Audit` subsection.
</overview>

<contents>

- `<external_tool_integration>`
- `<configuration_loading>`
- `<cli_structure>`
- `<error_handling>`
- `<concurrent_work>`
- `<unsafe_or_cgo_boundary>`

</contents>

<external_tool_integration>

When integrating with external tools:

```markdown
# External Tool Integration

Use dependency injection for all external tool invocations.

## Verification

### Audit

- ALWAYS: functions that call external tools accept a runner interface or function parameter -- enables isolated testing of command-building logic ([audit])
- ALWAYS: default implementations use real tools; tests inject controlled implementations -- no mocking ([audit])
- NEVER: direct `os/exec` construction in core domain logic without an injected seam -- prevents isolated testing ([audit])
```

</external_tool_integration>

<configuration_loading>

When defining configuration approach:

```markdown
# Configuration Loading

Use typed configuration structs with boundary validation and fail-fast loading.

## Verification

### Audit

- ALWAYS: config files decode into unexported raw structs and validate into exported typed structs -- ensures validated config ([audit])
- ALWAYS: config loading validates at load time through a constructor or parse function -- fail fast with descriptive errors ([audit])
- NEVER: unvalidated config access at use time -- defers errors to runtime ([audit])
- NEVER: a config field read through a package-level variable -- couples every caller to process-global state ([audit])
```

</configuration_loading>

<cli_structure>

When defining CLI architecture:

```markdown
# CLI Structure

Use thin command handlers with delegated runners and an exported command vocabulary.

## Verification

### Audit

- ALWAYS: each command is a typed command definition whose name and flags are exported constants -- enables explicit command contracts ([audit])
- ALWAYS: command handlers delegate to runner functions or services that accept injected dependencies -- separates parsing from logic ([audit])
- NEVER: business logic in command handlers -- prevents isolated testing ([audit])
- NEVER: direct I/O in command packages without DI -- couples commands to environment ([audit])
```

</cli_structure>

<error_handling>

When defining error handling approach:

```markdown
# Error Handling

Use sentinel and typed errors with `%w` wrapping at every boundary.

## Verification

### Audit

- ALWAYS: domain and library boundaries define sentinel errors or error structs -- enables `errors.Is` and `errors.As` handling ([audit])
- ALWAYS: error messages are user-facing and actionable at the presentation boundary -- no raw internals in output ([audit])
- ALWAYS: infrastructure errors are wrapped with `%w` at layer boundaries instead of leaking driver types upward unwrapped ([audit])
- NEVER: `panic` or `log.Fatal` for expected failures -- loses structure ([audit])
- NEVER: swallowing errors without logging or propagation -- hides failures ([audit])
```

</error_handling>

<concurrent_work>

When defining concurrency patterns:

```markdown
# Concurrent Work

Every goroutine has an owner, a context, and an exit condition; shared state moves through channels or one owning goroutine.

## Verification

### Audit

- ALWAYS: functions that spawn goroutines accept a `context.Context` and stop every goroutine on cancellation -- keeps lifetime observable ([audit])
- ALWAYS: fan-out work runs under `errgroup.Group` or a `sync.WaitGroup` with a results channel -- structured completion ([audit])
- ALWAYS: timeouts are configurable via injected policy or typed configuration -- enables testing of timeout logic ([audit])
- NEVER: a mutex held across a blocking call, channel operation, or callback -- creates deadlock and contention risks ([audit])
- NEVER: an unstructured `go` statement with no owner -- leaks goroutines ([audit])
- NEVER: hardcoded timeout values -- prevents testing and configuration ([audit])
```

</concurrent_work>

<unsafe_or_cgo_boundary>

When defining unsafe code or interop boundaries:

```markdown
# Unsafe or cgo Boundary

Confine `unsafe` and cgo to one package with documented safety contracts and safe wrappers.

## Verification

### Audit

- ALWAYS: every `unsafe.Pointer` conversion carries a `SAFETY:` explanation tied to the actual invariant being relied on ([audit])
- ALWAYS: cgo calls live in one package that converts to Go types at the boundary and frees C memory in the same package ([audit])
- NEVER: using `unsafe` as a shortcut around type design problems ([audit])
- NEVER: exposing C pointers or layout-sensitive details directly to high-level application code without a documented boundary ([audit])
```

</unsafe_or_cgo_boundary>
