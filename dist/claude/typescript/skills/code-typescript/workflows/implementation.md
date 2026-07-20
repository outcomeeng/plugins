<required_reading>

- Read the specification completely: node spec, ADR/PDR, design note, ticket, or user request.
- Read repository-local authority before existing code: root guide, docs, and any spec-tree context already loaded by `spec-tree:contextualize`.
- Read `/typescript-standards` and `/typescript-test-standards`; they own TypeScript code and test conventions.
- Read `package.json`, `tsconfig*`, test configuration, and relevant local overlays or harness guides before selecting commands.

</required_reading>

<process>

1. Identify deliverables, public interfaces, edge cases, error behavior, and the evidence selected by `/verify`. If the specification or routing result is missing or unclear, stop and resolve it before writing code.
2. Discover existing contracts and reusable artifacts before writing code: package dependencies, source-owned constants, registries, constructors, harnesses, fixtures, generators, entrypoints, and neighboring modules.
3. Record the discovery result in the working notes: libraries already available, authoritative rules loaded, reusable artifacts found, and commands selected from repository wrappers.

<gate name="discovery">

Proceed only when the specification, source contracts, reusable test infrastructure, and repository command surface are identified. Stop before mutation when any required authority or contract is missing; report the exact missing input instead of inventing a local substitute.

</gate>

4. Invoke `/verify` before adding or revising evidence, then handle every selected type:
   - test — write or update the co-located tests first using the assertion type chosen by `/test` and the TypeScript expression from `/typescript-test-standards`
   - evaluate — read the eval definition, cases, materialized prompt, real producer contract, selected product command, and declared completion threshold
   - audit — apply `<audit_requirement_handoff>` from `SKILL.md` without fabricating a deterministic artifact
5. For selected tests, run the focused test command and confirm the new or changed test fails for the expected reason before implementation. For selected evals, run the selected product command and record the preimplementation score against its threshold.

<gate name="red-evidence">

For selected tests, proceed only when the focused test fails because the declared behavior is absent or incorrect. Stop and repair the test or source contract when it passes before implementation, fails during setup, or fails for an unrelated reason. For selected evals, require a valid baseline score; for audit-only work, require the pathless audit constraint and its real subject to be identified.

</gate>

6. Implement the smallest TypeScript change that satisfies the governed behavior while preserving dependency injection, explicit types, source-owned contracts, and repository import rules.
7. Run every selected test and eval command, then typecheck, lint, and repository-selected validation commands. Require selected evals to meet their declared thresholds and preserve pathless audit requirements. Use raw tool fallbacks only when no repository wrapper exists.

<gate name="completion">

Report completion only when every selected test passes, every selected eval meets its declared threshold, the `Audit requirements` row count and `preserved` statuses match `/verify`'s audit routing rows, and each repository-selected typecheck, lint, and validation command exits successfully. A missing command, skipped required check, or non-zero exit keeps the workflow incomplete and must be reported with the exact command and result.

</gate>

Use this file-structure model as an illustration of separation, not as a required product layout:

```
src/
├── index.ts             # Exports public interface
├── core.ts              # Main implementation
├── errors.ts            # Custom error classes
└── types.ts             # Type definitions

testing/
├── generators/
│   └── paths.ts         # Variable input domains
├── harnesses/
│   └── index.ts         # External resource setup
└── fixtures/
    └── sample-rule.ts   # Inert source file read by tool tests

spx/{node-path}/tests/   # Co-located tests (Outcome Engineering framework)
├── core.mapping.l1.test.ts
└── core.scenario.l2.test.ts
```

Apply these coding rules while implementing:

- Public functions and exported values carry explicit types.
- Errors are typed and carry actionable context.
- Dependencies enter through parameters, constructor arguments, or explicit adapters rather than hidden globals.
- Magic values become named constants when the value has domain meaning.
- Test infrastructure stays outside product code and outside `spx/**/tests/`.

```typescript
// GOOD - Complete type annotations
export async function processItems(
  items: readonly string[],
  config: Config,
  logger: Logger,
): Promise<ProcessResult> {
  /**
   * Process items according to config.
   *
   * @param items - List of item identifiers to process.
   * @param config - Processing configuration.
   * @param logger - Logger instance for diagnostics.
   * @returns ProcessResult containing success/failure counts.
   * @throws ValidationError if items contain invalid identifiers.
   */
  // ...
}

// BAD - Missing types, vague docs
function processItems(items, config, logger) {
  // Process the items.
}
```

```typescript
// Use const assertions for literal types
const CONFIG = {
  timeout: 60,
  retries: 3,
} as const;

// Use satisfies for type checking without widening
const routes = {
  home: "/",
  about: "/about",
} satisfies Record<string, string>;
```

```typescript
// GOOD - Specific error classes with context
export class DatasetNotFoundError extends Error {
  constructor(public readonly dataset: string) {
    super(`Dataset not found: ${dataset}`);
    this.name = "DatasetNotFoundError";
  }
}

// BAD - Bare catch, swallowed error
try {
  return loadDataset(name);
} catch {
  return null;
}
```

```typescript
// GOOD - Dependencies as parameters
export interface SyncDependencies {
  execa: typeof execa;
  logger: Logger;
}

export async function syncFiles(
  source: string,
  dest: string,
  deps: SyncDependencies,
): Promise<SyncResult> {
  deps.logger.info(`Syncing ${source} to ${dest}`);
  // ...
}

// BAD - Hidden dependencies
async function syncFiles(source: string, dest: string): Promise<SyncResult> {
  const logger = getLogger(); // Hidden dependency
}
```

```typescript
// GOOD
const TIMEOUT_MS = 60_000;
const MAX_RETRIES = 3;

// BAD
for (let attempt = 0; attempt < 3; attempt++) {
  // Magic number
}
```

```bash
# TypeScript validation through the repository's canonical command
<product-typecheck-command>

# Auto-fix style issues through the repository's canonical command, when available
<product-lint-fix-command>

# Lint validation through the repository's canonical command
<product-lint-command>

# Tests through the repository's canonical command
<product-test-command>

# Bare-repo fallback examples only when no repository wrapper exists:
# npx tsc --noEmit
# npx eslint src/ test/ --fix
# npx eslint src/ test/
# npx vitest run
```

</process>

<success_criteria>

- The implementation follows the loaded specification and preserves source-owned contracts.
- Selected tests exist, fail before the implementation change for the expected reason, and pass after the change.
- Selected evals have a valid baseline and meet their declared completion thresholds after the change; the `Audit requirements` report matches `/verify`'s audit routing rows.
- Typecheck, lint, and every selected deterministic command pass through repository-selected wrappers or documented fallbacks.
- No new dependency, command, import shape, or test-infrastructure placement contradicts `/typescript-standards`, `/typescript-test-standards`, or loaded repository authority.

</success_criteria>
