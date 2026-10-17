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

- ALWAYS: functions that call external tools accept a runner interface or function parameter -- enables isolated testing of command-building logic ([audit:runner-parameter-for-external-tools])
- ALWAYS: default implementations use real tools; tests inject controlled implementations -- no mocking ([audit:real-defaults-injected-in-tests])
- NEVER: direct `os/exec` construction in core domain logic without an injected seam -- prevents isolated testing ([audit:no-uninjected-os-exec-in-domain])
```

</external_tool_integration>

<configuration_loading>

When defining configuration approach:

```markdown
# Configuration Loading

Use typed configuration structs with boundary validation and fail-fast loading.

## Verification

### Audit

- ALWAYS: config files decode into unexported raw structs and validate into exported typed structs -- ensures validated config ([audit:raw-struct-decodes-to-typed-struct])
- ALWAYS: config loading validates at load time through a constructor or parse function -- fail fast with descriptive errors ([audit:validate-config-at-load-time])
- NEVER: unvalidated config access at use time -- defers errors to runtime ([audit:no-unvalidated-config-at-use])
- NEVER: a config field read through a package-level variable -- couples every caller to process-global state ([audit:no-package-level-config-variable])
```

</configuration_loading>

<cli_structure>

When defining CLI architecture:

```markdown
# CLI Structure

Use thin command handlers with delegated runners and an exported command vocabulary.

## Verification

### Audit

- ALWAYS: each command is a typed command definition whose name and flags are exported constants -- enables explicit command contracts ([audit:typed-commands-with-exported-constants])
- ALWAYS: command handlers delegate to runner functions or services that accept injected dependencies -- separates parsing from logic ([audit:handlers-delegate-to-injected-runners])
- NEVER: business logic in command handlers -- prevents isolated testing ([audit:no-business-logic-in-handlers])
- NEVER: direct I/O in command packages without DI -- couples commands to environment ([audit:no-undi-io-in-command-packages])
```

</cli_structure>

<error_handling>

When defining error handling approach:

```markdown
# Error Handling

Use sentinel and typed errors with `%w` wrapping at every boundary.

## Verification

### Audit

- ALWAYS: domain and library boundaries define sentinel errors or error structs -- enables `errors.Is` and `errors.As` handling ([audit:sentinel-errors-at-boundaries])
- ALWAYS: error messages are user-facing and actionable at the presentation boundary -- no raw internals in output ([audit:actionable-user-facing-error-messages])
- ALWAYS: infrastructure errors are wrapped with `%w` at layer boundaries instead of leaking driver types upward unwrapped ([audit:wrap-infrastructure-errors-with-percent-w])
- NEVER: `panic` or `log.Fatal` for expected failures -- loses structure ([audit:no-panic-for-expected-failures])
- NEVER: swallowing errors without logging or propagation -- hides failures ([audit:no-swallowed-errors])
```

</error_handling>

<concurrent_work>

When defining concurrency patterns:

```markdown
# Concurrent Work

Every goroutine has an owner, a context, and an exit condition; shared state moves through channels or one owning goroutine.

## Verification

### Audit

- ALWAYS: functions that spawn goroutines accept a `context.Context` and stop every goroutine on cancellation -- keeps lifetime observable ([audit:goroutines-stop-on-context-cancellation])
- ALWAYS: fan-out work runs under `errgroup.Group` or a `sync.WaitGroup` with a results channel -- structured completion ([audit:structured-fan-out-completion])
- ALWAYS: timeouts are configurable via injected policy or typed configuration -- enables testing of timeout logic ([audit:configurable-timeouts])
- NEVER: a mutex held across a blocking call, channel operation, or callback -- creates deadlock and contention risks ([audit:no-mutex-held-across-blocking-calls])
- NEVER: an unstructured `go` statement with no owner -- leaks goroutines ([audit:no-ownerless-go-statements])
- NEVER: hardcoded timeout values -- prevents testing and configuration ([audit:no-hardcoded-timeouts])
```

</concurrent_work>

<unsafe_or_cgo_boundary>

When defining unsafe code or interop boundaries:

```markdown
# Unsafe or cgo Boundary

Confine `unsafe` and cgo to one package with documented safety contracts and safe wrappers.

## Verification

### Audit

- ALWAYS: every `unsafe.Pointer` conversion carries a `SAFETY:` explanation tied to the actual invariant being relied on ([audit:unsafe-pointer-safety-explanation])
- ALWAYS: cgo calls live in one package that converts to Go types at the boundary and frees C memory in the same package ([audit:cgo-confined-to-one-package])
- NEVER: using `unsafe` as a shortcut around type design problems ([audit:no-unsafe-as-type-design-shortcut])
- NEVER: exposing C pointers or layout-sensitive details directly to high-level application code without a documented boundary ([audit:no-c-pointers-in-application-code])
```

</unsafe_or_cgo_boundary>
