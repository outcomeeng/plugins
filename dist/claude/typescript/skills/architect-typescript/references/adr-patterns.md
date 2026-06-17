# Common ADR Patterns for TypeScript

These patterns show how testability constraints appear under the `## Verification` section's `### Audit` subsection. See `/typescript-architecture-standards` for the canonical ADR section structure.

## Pattern: External Tool Integration

When integrating with external tools (Hugo, Caddy, LHCI):

```markdown
# External Tool Integration

Use dependency injection for all external tool invocations.

## Verification

### Audit

- ALWAYS: functions that call external tools accept a `deps` parameter with a typed interface -- enables `l1` testing of command-building logic ([audit])
- ALWAYS: default implementations use real tools; tests inject controlled implementations -- no mocking ([audit])
- NEVER: direct `child_process.exec/spawn` without a DI wrapper -- prevents isolated testing ([audit])
```

## Pattern: Configuration Loading

When defining configuration approach:

```markdown
# Configuration Loading

Use Zod schemas for all configuration validation.

## Verification

### Audit

- ALWAYS: config files have corresponding Zod schemas -- ensures type-safe, validated config ([audit])
- ALWAYS: config loading validates at load time with `.parse()` -- fail fast with descriptive errors ([audit])
- NEVER: unvalidated config access at use time -- defers errors to runtime ([audit])
- NEVER: `as` type assertions on config data -- bypasses validation ([audit])
```

## Pattern: CLI Structure

When defining CLI architecture:

```markdown
# CLI Structure

Use Commander.js with subcommand pattern.

## Verification

### Audit

- ALWAYS: each command is a separate module exporting a registration function -- enables isolated `l1` testing ([audit])
- ALWAYS: commands delegate to runner functions that accept DI parameters -- separates parsing from logic ([audit])
- NEVER: business logic in command handlers -- prevents isolated testing ([audit])
- NEVER: direct I/O in command modules without DI -- couples commands to environment ([audit])
```

## Pattern: Error Handling

When defining error handling approach:

```markdown
# Error Handling

Use typed error classes with structured error codes.

## Verification

### Audit

- ALWAYS: errors extend a base `AppError` class with structured error codes -- enables programmatic handling ([audit])
- ALWAYS: error messages are user-facing and actionable -- no raw stack traces in output ([audit])
- NEVER: throwing plain `Error` or string literals -- loses structure ([audit])
- NEVER: swallowing errors without logging or re-throwing -- hides failures ([audit])
```

## Pattern: Async Operations

When defining async patterns:

```markdown
# Async Operations

Use async/await with explicit error handling and timeouts.

## Verification

### Audit

- ALWAYS: async functions have explicit return types -- prevents implicit `Promise<any>` ([audit])
- ALWAYS: timeouts are configurable via dependency injection -- enables `l1` testing of timeout logic ([audit])
- ALWAYS: errors are caught and converted to typed `AppError` subclasses -- structured propagation ([audit])
- NEVER: unhandled promise rejections -- crashes process ([audit])
- NEVER: hardcoded timeout values -- prevents testing and configuration ([audit])
```
