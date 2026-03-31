# Common ADR Patterns for TypeScript

These patterns show how testability constraints appear in the Compliance section. See `/standardizing-typescript-architecture` for the canonical ADR section structure.

## Pattern: External Tool Integration

When integrating with external tools (Hugo, Caddy, LHCI):

```markdown
## Decision

Use dependency injection for all external tool invocations.

## Compliance

### Recognized by

Observable `deps` parameter in all functions that invoke external tools.

### MUST

- All functions that call external tools accept a `deps` parameter with a typed interface -- enables Level 1 testing of command-building logic ([review])
- Default implementations use real tools; tests inject controlled implementations -- no mocking ([review])

### NEVER

- Direct `child_process.exec/spawn` without DI wrapper -- prevents isolated testing ([review])
```

## Pattern: Configuration Loading

When defining configuration approach:

```markdown
## Decision

Use Zod schemas for all configuration validation.

## Compliance

### Recognized by

Zod schema accompanying every config file type. Validation at load time, not use time.

### MUST

- All config files have corresponding Zod schemas -- ensures type-safe, validated config ([review])
- Config loading validates at load time with `.parse()` -- fail fast with descriptive errors ([review])

### NEVER

- Unvalidated config access at use time -- defers errors to runtime ([review])
- `as` type assertions on config data -- bypasses validation ([review])
```

## Pattern: CLI Structure

When defining CLI architecture:

```markdown
## Decision

Use Commander.js with subcommand pattern.

## Compliance

### Recognized by

Separate module per command. Business logic delegated to runners, not in command handlers.

### MUST

- Each command is a separate module exporting a registration function -- enables isolated Level 1 testing ([review])
- Commands delegate to runner functions that accept DI parameters -- separates parsing from logic ([review])

### NEVER

- Business logic in command handlers -- prevents isolated testing ([review])
- Direct I/O in command modules without DI -- couples commands to environment ([review])
```

## Pattern: Error Handling

When defining error handling approach:

```markdown
## Decision

Use typed error classes with structured error codes.

## Compliance

### Recognized by

All thrown errors extend `AppError`. Error codes are unique and documented.

### MUST

- All errors extend a base `AppError` class with structured error codes -- enables programmatic handling ([review])
- Error messages are user-facing and actionable -- no raw stack traces in output ([review])

### NEVER

- Throwing plain `Error` or string literals -- loses structure ([review])
- Swallowing errors without logging or re-throwing -- hides failures ([review])
```

## Pattern: Async Operations

When defining async patterns:

```markdown
## Decision

Use async/await with explicit error handling and timeouts.

## Compliance

### Recognized by

Explicit return types on all async functions. Timeouts configurable via DI.

### MUST

- All async functions have explicit return types -- prevents implicit `Promise<any>` ([review])
- Timeouts are configurable via dependency injection -- enables Level 1 testing of timeout logic ([review])
- Errors are caught and converted to typed `AppError` subclasses -- structured propagation ([review])

### NEVER

- Unhandled promise rejections -- crashes process ([review])
- Hardcoded timeout values -- prevents testing and configuration ([review])
```
