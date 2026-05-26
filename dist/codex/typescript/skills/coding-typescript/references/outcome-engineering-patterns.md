# Code Patterns

## Pattern: Subprocess Execution

```typescript
import { execa, type ExecaReturnValue } from "execa";

const TIMEOUT_MS = 60_000;

export class CommandError extends Error {
  constructor(
    public readonly cmd: readonly string[],
    public readonly exitCode: number,
    public readonly stderr: string,
  ) {
    super(`Command failed (${exitCode}): ${cmd.join(" ")}`);
    this.name = "CommandError";
  }
}

export interface CommandDeps {
  execa: typeof execa;
}

export async function runCommand(
  cmd: readonly string[],
  logger: Logger,
  deps: CommandDeps,
  options: { timeout?: number; check?: boolean } = {},
): Promise<ExecaReturnValue> {
  const { timeout = TIMEOUT_MS, check = true } = options;

  logger.debug(`Running: ${cmd.join(" ")}`);

  const result = await deps.execa(cmd[0], cmd.slice(1), {
    timeout,
    reject: false,
  });

  if (check && result.exitCode !== 0) {
    throw new CommandError(cmd, result.exitCode, result.stderr);
  }

  return result;
}
```

## Pattern: Resource Cleanup with Disposable

```typescript
async function* createTemporaryDataset(
  pool: string,
  logger: Logger,
): AsyncGenerator<string, void, unknown> {
  const dataset = `${pool}/tmp-${crypto.randomUUID().slice(0, 8)}`;

  try {
    await createDataset(dataset, logger);
    yield dataset;
  } finally {
    try {
      await destroyDataset(dataset, logger);
    } catch (e) {
      logger.warn(`Failed to cleanup ${dataset}: ${e}`);
    }
  }
}

// Usage with for-await
async function withTemporaryDataset<T>(
  pool: string,
  logger: Logger,
  fn: (dataset: string) => Promise<T>,
): Promise<T> {
  for await (const dataset of createTemporaryDataset(pool, logger)) {
    return fn(dataset);
  }
  throw new Error("Unreachable");
}
```

## Pattern: Configuration with Validation (Zod)

```typescript
import { z } from "zod";

export const syncConfigSchema = z.object({
  source: z.string().min(1),
  destination: z.string().min(1),
  dryRun: z.boolean().default(false),
  maxRetries: z.number().int().nonnegative().default(3),
});

export type SyncConfig = z.infer<typeof syncConfigSchema>;

export function validateConfig(input: unknown): SyncConfig {
  return syncConfigSchema.parse(input);
}

// Usage
const config = validateConfig({
  source: "/data/source",
  destination: "/data/dest",
});
// config is fully typed as SyncConfig
```

## Pattern: Typed Error Classes

```typescript
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class ValidationError extends AppError {
  constructor(
    public readonly field: string,
    message: string,
  ) {
    super(`${field}: ${message}`, "VALIDATION_ERROR");
  }
}

export class NotFoundError extends AppError {
  constructor(
    public readonly resource: string,
    public readonly id: string,
  ) {
    super(`${resource} not found: ${id}`, "NOT_FOUND");
  }
}
```
