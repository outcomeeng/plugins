# Implementation Protocol

Execute these phases IN ORDER.

## Phase 0: Understand the Spec

Before writing any code:

1. **Read the specification** completely (TRD, design doc, ticket, or user request)
2. **Identify deliverables**: What files, functions, classes need to be created?
3. **Identify interfaces**: What are the function signatures, input/output types?
4. **Identify edge cases**: What error conditions must be handled?
5. **Identify test scenarios**: What tests will prove correctness?

**If the spec is missing or unclear**:

- Ask for clarification
- Do NOT proceed with assumptions
- Document any decisions made

## Phase 0.5: Codebase Discovery (MANDATORY)

**Before writing ANY code, discover what already exists.**

See `<codebase_discovery>` in SKILL.md for complete guidance.

### Quick Checklist

```bash
# 1. Read project docs (highest authority)
Read: README.md, docs/, CLAUDE.md

# 2. Read the relevant skill/spec first
Read: the skill and spec docs that define the pattern you are about to use

# 3. Check available libraries
Read: package.json → dependencies, devDependencies

# 4. Locate reusable artifacts
Glob/Grep: actual modules, harnesses, fixtures, registries, entrypoints

# 5. Confirm file placement
Read: files in target directory
```

### Discovery Output

Before proceeding to Phase 1, document:

- **Libraries to use**: (from package.json, don't add new ones)
- **Authoritative rules loaded**: (skill/spec/docs that govern this work)
- **Reusable artifacts found**: (existing utilities, harnesses, fixtures, registries)
- **Utilities to reuse**: (don't reinvent what exists)

**Remember the hierarchy**: `docs/` > `CLAUDE.md` > `specs` > `SKILL.md` >>> existing code

Existing code is REFERENCE, not authority. Use code search to find artifacts, never to decide methodology or conventions. When docs and code conflict, docs win.

## Phase 1: Write Tests First (TDD)

For each function/class to implement:

1. **Create test file** if it doesn't exist, following `/standardizing-typescript-tests`: `{module}.scenario.l1.test.ts`
2. **Write test cases** following the debuggability progression (see `references/test-patterns.md`)
3. **Run tests** to confirm they fail (red phase)

## Phase 2: Implement Code

Write implementation that makes tests pass.

### File Structure

```
src/
├── index.ts             # Exports public interface
├── core.ts              # Main implementation
├── errors.ts            # Custom error classes
└── types.ts             # Type definitions

testing/
├── fixtures/
│   ├── values.ts        # Shared test values
│   └── factories.ts     # Test data factories
└── harnesses/
    └── index.ts         # Test harnesses

spx/{node-path}/tests/   # Co-located tests (Outcome Engineering framework)
├── core.mapping.l1.test.ts
└── core.scenario.l2.test.ts
```

### Code Standards

**Type Annotations** (MANDATORY):

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

**Modern TypeScript Syntax** (ES2022+):

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

**Error Handling**:

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

**Dependency Injection**:

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

**Constants, Not Magic Numbers**:

```typescript
// GOOD
const TIMEOUT_MS = 60_000;
const MAX_RETRIES = 3;

// BAD
for (let attempt = 0; attempt < 3; attempt++) {
  // Magic number
}
```

## Phase 3: Self-Verification

Before declaring completion, run ALL verification tools:

```bash
# Type checking
npx tsc --noEmit

# Linting
npx eslint src/ test/
npx eslint src/ test/ --fix

# Tests
npx vitest run --coverage
```

**Expected**:

- tsc: Zero errors
- eslint: Zero errors (auto-fix applied where safe)
- vitest: All tests pass, coverage ≥80% for new code

See `references/verification-checklist.md` for full checklist.

## Phase 4: Submit for Review

When verification passes:

1. **Summarize what was implemented**:
   - Files created/modified
   - Functions/classes added
   - Tests added
   - Any deviations from spec (with justification)

2. **Note any known limitations**:
   - Edge cases not covered
   - Dependencies on external systems
   - Performance considerations

3. **Request review**: Submit for code review.
