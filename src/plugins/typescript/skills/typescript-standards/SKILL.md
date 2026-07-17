---
name: typescript-standards
user-invocable: false
description: >-
  TypeScript code standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The TypeScript code standards every TypeScript skill enforces.
</objective>

<success_criteria>
Code follows these standards when tsc strict mode and eslint pass, every manual-review criterion in the rejection summary has been evaluated, and no source-ownership, error-context, security, import-hygiene, async, or code-hygiene rule in this reference remains violated.
</success_criteria>

<reference_note>
This is a reference skill. Composing TypeScript skills load these standards explicitly before writing, testing, or auditing. It is not a standalone workflow.

These standards apply to ALL TypeScript code, including tests and scripts. `/typescript-test-standards` adds stricter rules for test code.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/typescript.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<type_safety>

TypeScript strict mode enforces type safety. All violations are caught by tsc at compile time.

```typescript
// ❌ REJECTED: Unqualified any without justification
function process(data: any): any {
  return data;
}

// ✅ REQUIRED: Use concrete types
function process(data: Record<string, string>): ProcessResult {
  return new ProcessResult(data);
}

// ❌ REJECTED: @ts-ignore without explanation
// @ts-ignore
const result = someFunction();

// ✅ REQUIRED: Use @ts-expect-error with explanation
// @ts-expect-error - third-party library missing type definitions
const result = someFunction();

// ❌ REJECTED: Type assertion without narrowing
function getValue(x: string | number): string {
  return x as string; // Unsafe
}

// ✅ REQUIRED: Type guard before assertion
function getValue(x: string | number): string {
  if (typeof x === "string") {
    return x;
  }
  return x.toString();
}

// ❌ REJECTED: Unconstrained generic
function process<T>(value: T): T {
  return value.toString(); // Error: toString might not exist
}

// ✅ REQUIRED: Properly constrained generic
function process<T extends { toString(): string }>(value: T): string {
  return value.toString();
}

// ❌ REJECTED: Union type used without narrowing
function handle(value: string | number): void {
  console.log(value.toUpperCase()); // Error: number has no toUpperCase
}

// ✅ REQUIRED: Narrow union before use
function handle(value: string | number): void {
  if (typeof value === "string") {
    console.log(value.toUpperCase());
  } else {
    console.log(value.toString());
  }
}
```

**tsconfig.json strict mode settings:**

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true
  }
}
```

**ESLint rules enforced:**

| Rule                                          | What it catches                            |
| --------------------------------------------- | ------------------------------------------ |
| @typescript-eslint/no-explicit-any            | Unqualified `any` usage                    |
| @typescript-eslint/ban-ts-comment             | `@ts-ignore` instead of `@ts-expect-error` |
| @typescript-eslint/consistent-type-assertions | Type assertions without justification      |

</type_safety>

<production_constants>

Production code must name domain-significant literals and export reusable constants from the module that owns them.

```typescript
// ✅ REQUIRED: Named reusable constants at module level
export const MIN_SCORE = 0;
export const MAX_SCORE = 100;
export const DEFAULT_SCORE = 85;

export function validateScore(score: number): boolean {
  return score >= MIN_SCORE && score <= MAX_SCORE;
}

validateScore(DEFAULT_SCORE);

// ❌ REJECTED: Inline domain literals
export function validateScoreBad(score: number): boolean {
  return score >= 0 && score <= 100;
}
```

**Why named constants matter in production code:**

- Exported constants become the canonical source for tests and other modules
- Thresholds, command flags, and status tokens stay synchronized
- Code communicates domain meaning instead of unexplained literals

**ESLint rules enforced:**

| Rule                                | What it catches              |
| ----------------------------------- | ---------------------------- |
| no-magic-numbers                    | Literal numbers in code      |
| @typescript-eslint/no-magic-numbers | TypeScript-specific literals |

**Rule exemptions:** ESLint already exempts common idiomatic values: `0`, `1`, `-1` in array indexes, and enum values. These do not need constants.

```typescript
// ✅ OK: Idiomatic values are exempt
if (results.length === 0) {
  return;
}
if (count === 1) {
  doThing();
}
const first = items[0];
const last = items[items.length - 1];
```

For test values, fixture placement, and inline diagnostics, follow `/typescript-test-standards`.

</production_constants>

<source_of_truth_registries>

Closed sets must have one runtime source of truth. Use `as const` registries or tuples, then derive unions and schemas from that declaration instead of duplicating string unions by hand.

```typescript
export const VERDICT_STATUSES = {
  APPROVED: "approved",
  REJECTED: "rejected",
} as const;

export type VerdictStatus = (typeof VERDICT_STATUSES)[keyof typeof VERDICT_STATUSES];

export const verdictStatusSchema = z.enum(
  Object.values(VERDICT_STATUSES) as [string, ...string[]],
);
```

The tuple cast is only for `z.enum`'s non-empty tuple signature. Keep the runtime registry as the source of truth; do not add a separate string union to satisfy the schema API.

Hand-maintained unions that can drift from the runtime registry are rejected.

</source_of_truth_registries>

<script_boundaries>

Checked-in entrypoints in `scripts/` are boundary code.

Scripts may:

- parse arguments
- read and normalize environment variables at the boundary
- format terminal output
- dispatch to one orchestrator module or a small dispatcher
- map the final result to a process exit code at the outermost `main`

Scripts must NOT become the home of business logic, workflow policy, or transforms that deserve their own specification.

**Canonical argument parsing**

Every repository must converge on one argument parsing library. Script entrypoints must use the repo's canonical parser instead of manual parsing with `process.argv`, ad hoc loops, or mixed parser libraries.

```typescript
// ❌ REJECTED: manual parsing
const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const target = args[args.indexOf("--target") + 1];

// ✅ REQUIRED: repository-canonical parser
const options = parseArgsWithRepoStandard(process.argv.slice(2));
```

**Boundary flexibility**

- Relative imports are acceptable inside `scripts/`
- Boundary env parsing is acceptable inside `scripts/`
- `console.*` is acceptable inside `scripts/` for terminal output

Imported orchestrator modules should still follow the normal codebase standards for configuration, logging, and specification coverage.

</script_boundaries>

<error_handling>

```typescript
// ❌ REJECTED: Empty catch block (no-empty)
try {
  process();
} catch (err) {
  // Silent failure
}

// ❌ REJECTED: Unhandled promise rejection (@typescript-eslint/no-floating-promises)
async function bad(): Promise<void> {
  fetchData(); // Promise not awaited or handled
}

// ✅ REQUIRED: Catch specific errors with context
try {
  process();
} catch (err) {
  if (err instanceof ValidationError) {
    log.error("Invalid input:", err.message);
    throw err;
  }
  throw new ProcessingError("Unexpected error during processing", { cause: err });
}

// ✅ REQUIRED: Handle or await promises
async function good(): Promise<void> {
  await fetchData();
  // or
  fetchData().catch(err => handleError(err));
}

// ✅ REQUIRED: Custom error classes for domain errors
class ValidationError extends Error {
  constructor(
    message: string,
    public readonly field: string,
    public readonly value: unknown,
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

// ✅ REQUIRED: Error messages include context
throw new ValidationError(
  `Score must be between ${MIN_SCORE} and ${MAX_SCORE}, got ${score}`,
  "score",
  score,
);
```

**ESLint rules enforced:**

| Rule                                    | What it catches              |
| --------------------------------------- | ---------------------------- |
| no-empty                                | Empty catch blocks           |
| @typescript-eslint/no-floating-promises | Unhandled promise rejections |

</error_handling>

<security>

```typescript
// ❌ REJECTED: Hardcoded secrets
const API_KEY = "sk-1234567890";
const password = "hunter2";

// ❌ REJECTED: eval (no-eval)
const result = eval(userInput);

// ❌ REJECTED: new Function (no-new-func)
const fn = new Function("x", "return x + 1");

// ❌ REJECTED: child_process.exec with untrusted input
import { exec } from "child_process";
exec(`grep ${userInput} file.txt`); // Shell injection

// ✅ REQUIRED: Use execFile with argument array
import { execFile } from "child_process";
execFile("grep", [userInput, "file.txt"]);

// ✅ REQUIRED: Load secrets from environment
const apiKey = process.env.API_KEY;
if (!apiKey) {
  throw new Error("API_KEY environment variable required");
}
```

Context matters for security rules—a CLI tool invoked by the user has different trust boundaries than a web service. Reading env vars in `scripts/` is acceptable boundary behavior; imported modules should prefer typed config once past that boundary. See `/audit-typescript-code` for false positive handling.

**ESLint rules enforced:**

| Rule        | What it catches                             |
| ----------- | ------------------------------------------- |
| no-eval     | Use of `eval()`                             |
| no-new-func | Use of `new Function()`                     |
| (manual)    | Hardcoded secrets                           |
| (manual)    | `child_process.exec()` with untrusted input |

</security>

<code_hygiene>

```typescript
// ❌ REJECTED: Unused variables (@typescript-eslint/no-unused-vars)
import { processData } from "./utils"; // Never used
const unusedVariable = 42;

// ❌ REJECTED: Dead code or commented-out code
// function oldImplementation() {
//   return 42;
// }

// ❌ REJECTED: console.log in application/runtime modules (no-console)
function process(data: string): void {
  console.log("Processing:", data);
  // ...
}

// ✅ REQUIRED: Use proper logging
import { logger } from "./logger";

function process(data: string): void {
  logger.debug("Processing:", data);
  // ...
}

// ✅ REQUIRED: Remove unused imports and variables
import { processData } from "./utils";

function handle(input: string): void {
  processData(input);
}
```

**ESLint rules enforced:**

| Rule                              | What it catches                  |
| --------------------------------- | -------------------------------- |
| @typescript-eslint/no-unused-vars | Unused variables and imports     |
| no-console                        | `console.log` in runtime modules |
| (manual)                          | Dead code or commented-out code  |

`scripts/` entrypoints are the exception: console output is acceptable there because they are terminal boundaries. Imported modules should still use the repo's normal logging pattern.

</code_hygiene>

<import_hygiene>

**Depth Rules**

| Depth     | Syntax                         | Verdict | Rationale                                 |
| --------- | ------------------------------ | ------- | ----------------------------------------- |
| Same dir  | `import { x } from './y'`      | OK      | Module-internal, same package             |
| 1 level   | `import { x } from '../y'`     | REVIEW  | Is this truly module-internal?            |
| 2+ levels | `import { x } from '../../..'` | REJECT  | Use path alias — crosses package boundary |

**Module-Internal vs. Infrastructure**

**Module-internal files** live in the same package and move together. Relative imports are acceptable:

```typescript
// ✅ ACCEPTABLE: Same package, files move together
import { Position } from "./position";
import { tokenize } from "./tokens";
```

**Stable shared modules** are project-owned code that does not move when a feature moves. Path aliases are required, using the aliases the repository declares:

```typescript
// ❌ REJECTED: Deep relative import to stable shared code
import { getRepoRoot } from "../../../../../../src/shared/paths";

// ✅ REQUIRED: Repository-declared path alias
import { getRepoRoot } from "@shared/paths";
```

`scripts/` entrypoints are the exception: relative imports are acceptable there because they are boundary modules and often need to avoid circular dependency tangles. Imported orchestrator modules should still follow the normal alias rules for stable infrastructure.

**Anti-Patterns**

```typescript
// ❌ REJECTED: Deep relative imports
import { helper } from "../../../../lib/utils";

// ❌ REJECTED: Assuming working directory
import { helper } from "lib/utils"; // Only works if CWD is product root
```

**Required Product Setup**

**1. Configure `tsconfig.json` with path aliases:**

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@feature/*": ["<feature-root>/*"],
      "@shared/*": ["<shared-root>/*"]
    }
  }
}
```

**2. Common path alias patterns:**

| Alias        | Maps to            | Purpose                  |
| ------------ | ------------------ | ------------------------ |
| `@feature/*` | `<feature-root>/*` | Feature-owned modules    |
| `@shared/*`  | `<shared-root>/*`  | Stable shared modules    |
| `@testing/*` | `<testing-root>/*` | Test infrastructure root |

**3. Usage with path aliases:**

```typescript
// ✅ REQUIRED: Stable infrastructure via alias
import { processData } from "@feature/processing";
import { Logger } from "@shared/logger";

// ✅ ACCEPTABLE: Module-internal relative
import { Position } from "./position";
import { tokenize } from "./tokens";
```

</import_hygiene>

<rejection_criteria_summary>

| Issue                            | Example                                     | Rule/Tool                                     |
| -------------------------------- | ------------------------------------------- | --------------------------------------------- |
| Unqualified `any`                | `function f(x: any): any`                   | @typescript-eslint/no-explicit-any            |
| `@ts-ignore` without reason      | `// @ts-ignore`                             | @typescript-eslint/ban-ts-comment             |
| Type assertion without narrowing | `return x as string`                        | @typescript-eslint/consistent-type-assertions |
| Unconstrained generic            | `function f<T>(x: T)`                       | tsc strict mode                               |
| Union without narrowing          | `value.toUpperCase()` on `string \| number` | tsc strict mode                               |
| Unnamed domain literals          | `return score >= 0 && score <= 100`         | @typescript-eslint/no-magic-numbers           |
| Empty catch block                | `catch (err) {}`                            | no-empty                                      |
| Unhandled promise                | `fetchData();` without await                | @typescript-eslint/no-floating-promises       |
| Missing error context            | `throw new Error('failed')`                 | manual review                                 |
| Hardcoded secrets                | `const API_KEY = "sk-..."`                  | manual review                                 |
| `eval()` usage                   | `eval(userInput)`                           | no-eval                                       |
| `new Function()` usage           | `new Function('x', 'return x')`             | no-new-func                                   |
| `exec()` with untrusted input    | `exec(\`grep ${input} file\`)`              | manual review                                 |
| Unused variables/imports         | `import { x } from 'y'; // never used`      | @typescript-eslint/no-unused-vars             |
| `console.log` in production      | `console.log('debug')`                      | no-console                                    |
| Dead/commented code              | `// function old() { ... }`                 | manual review                                 |
| Deep relative imports            | `from '../../../lib'`                       | manual review                                 |

</rejection_criteria_summary>
