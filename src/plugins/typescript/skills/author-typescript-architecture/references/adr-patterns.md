# Common ADR Patterns for TypeScript

These patterns show how testability constraints appear under the `## Verification` section's `### Audit` subsection. See `/typescript-architecture-standards` for the canonical ADR section structure.

## Pattern: External Tool Integration

When integrating with external tools (Hugo, Caddy, LHCI):

```markdown
# External Tool Integration

Use dependency injection for all external tool invocations.

## Verification

### Audit

- ALWAYS: functions that call external tools accept a `deps` parameter with a typed interface -- enables `l1` testing of command-building logic ([audit:deps-parameter-typed-interface])
- ALWAYS: default implementations use real tools; tests inject controlled implementations -- no mocking ([audit:real-defaults-injected-test-doubles])
- NEVER: direct `child_process.exec/spawn` without a DI wrapper -- prevents isolated testing ([audit:no-direct-child-process])
```

## Pattern: Configuration Loading

When defining configuration approach:

```markdown
# Configuration Loading

Use Zod schemas for all configuration validation.

## Verification

### Audit

- ALWAYS: config files have corresponding Zod schemas -- ensures type-safe, validated config ([audit:config-zod-schemas])
- ALWAYS: config loading validates at load time with `.parse()` -- fail fast with descriptive errors ([audit:config-parse-at-load])
- NEVER: unvalidated config access at use time -- defers errors to runtime ([audit:no-unvalidated-config-access])
- NEVER: `as` type assertions on config data -- bypasses validation ([audit:no-config-type-assertions])
```

## Pattern: CLI Structure

When defining CLI architecture:

```markdown
# CLI Structure

Use Commander.js with subcommand pattern.

## Verification

### Audit

- ALWAYS: each command is a separate module exporting a registration function -- enables isolated `l1` testing ([audit:command-per-module])
- ALWAYS: commands delegate to runner functions that accept DI parameters -- separates parsing from logic ([audit:commands-delegate-to-runners])
- NEVER: business logic in command handlers -- prevents isolated testing ([audit:no-logic-in-command-handlers])
- NEVER: direct I/O in command modules without DI -- couples commands to environment ([audit:no-direct-io-in-commands])
```

## Pattern: Error Handling

When defining error handling approach:

```markdown
# Error Handling

Use typed error classes with structured error codes.

## Verification

### Audit

- ALWAYS: errors extend a base `AppError` class with structured error codes -- enables programmatic handling ([audit:errors-extend-app-error])
- ALWAYS: error messages are user-facing and actionable -- no raw stack traces in output ([audit:actionable-error-messages])
- NEVER: throwing plain `Error` or string literals -- loses structure ([audit:no-plain-error-throws])
- NEVER: swallowing errors without logging or re-throwing -- hides failures ([audit:no-swallowed-errors])
```

## Pattern: Async Operations

When defining async patterns:

```markdown
# Async Operations

Use async/await with explicit error handling and timeouts.

## Verification

### Audit

- ALWAYS: async functions have explicit return types -- prevents implicit `Promise<any>` ([audit:async-explicit-return-types])
- ALWAYS: timeouts are configurable via dependency injection -- enables `l1` testing of timeout logic ([audit:timeouts-injected])
- ALWAYS: errors are caught and converted to typed `AppError` subclasses -- structured propagation ([audit:errors-converted-to-app-error])
- NEVER: unhandled promise rejections -- crashes process ([audit:no-unhandled-rejections])
- NEVER: hardcoded timeout values -- prevents testing and configuration ([audit:no-hardcoded-timeouts])
```
