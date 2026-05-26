# TypeScript Architectural Principles

## Type Safety First

- Strict mode: `strict: true` in tsconfig.json
- No `any` without explicit justification in ADR
- Prefer `unknown` over `any` for truly unknown types
- Use Zod or similar for runtime validation at boundaries
- Leverage TypeScript utilities: `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`

```typescript
// GOOD: Strict types with validation
import { z } from "zod";

const configSchema = z.object({
  url: z.string().url(),
  timeout: z.number().positive(),
});

type Config = z.infer<typeof configSchema>;

// BAD: Loose types
interface Config {
  url: any;
  timeout: any;
}
```

## Clean Architecture

- **Dependency Injection**: Parameters, not imports
- **Single Responsibility**: One reason to change
- **Interface Segregation**: Small, focused interfaces
- **No circular imports**: Clear dependency hierarchy

```typescript
// GOOD: Dependencies as parameters
export interface BuildDependencies {
  execa: typeof execa;
  mkdtemp: (prefix: string) => Promise<string>;
}

export async function buildHugo(
  siteDir: string,
  deps: BuildDependencies,
): Promise<BuildResult> {
  // Implementation uses injected deps
}

// BAD: Hidden dependencies
import { execa } from "execa";

export async function buildHugo(siteDir: string): Promise<BuildResult> {
  await execa("hugo", ["--destination", "/tmp/build"]); // Hidden dependency
}
```

## Security by Design

- Validate at boundaries (user input, config files, API responses)
- No hardcoded secrets (use environment variables)
- Subprocess safety (avoid shell=true, use arrays)
- Context-aware threat modeling

```typescript
// GOOD: Safe subprocess execution
await execa("hugo", ["--destination", outputDir]); // Array args, no shell

// BAD: Shell injection risk
await exec(`hugo --destination ${outputDir}`); // Shell interpolation
```

## Testability by Design

- Design for dependency injection (NO MOCKING)
- Define Compliance constraints that make the right evidence levels achievable
- Pure functions enable `l1` testing
- Design for the minimum level that provides confidence

```typescript
// GOOD: Testable design with DI
export interface LhciDependencies {
  execa: typeof execa;
  getPort: typeof getPort;
}

export async function runLhci(
  options: LhciOptions,
  config: Config,
  deps: LhciDependencies,
): Promise<LhciResult> {
  // Can be tested at l1 with controlled deps
}

// BAD: Not testable without mocking
export async function runLhci(options: LhciOptions): Promise<LhciResult> {
  const port = await getPort(); // Can't control without mocking
  await execa("lhci", ["collect"]); // Can't control without mocking
}
```

## Interface Design

- Use `interface` for object shapes that will be implemented
- Use `type` for unions, intersections, and computed types
- Prefer `readonly` for immutable data
- Export types alongside implementations

```typescript
// Interfaces for implementations
export interface BuildResult {
  readonly buildDir: string;
  readonly exitCode: number;
  readonly duration: number;
}

// Types for unions and computed types
export type BuildStatus = "success" | "failure" | "skipped";
export type BuildConfig = Readonly<z.infer<typeof buildConfigSchema>>;
```

## Error Handling

- Use typed error classes, not string throws
- Include context in error messages
- Fail fast at boundaries
- Propagate errors with stack traces

```typescript
// GOOD: Typed errors with context
export class BuildError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly siteDir: string,
  ) {
    super(`${code}: ${message} (site: ${siteDir})`);
    this.name = "BuildError";
  }
}

// BAD: String throws
throw "Build failed"; // No context, no type
```
