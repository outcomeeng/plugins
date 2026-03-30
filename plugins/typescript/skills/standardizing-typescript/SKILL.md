---
name: standardizing-typescript
disable-model-invocation: true
description: >-
  TypeScript code standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
TypeScript code standards enforced by tsc strict mode, eslint, and manual review. Defines what `/coding-typescript` must follow and `/auditing-typescript` enforces.
</objective>

<quick_start>
Reference this skill when coding or reviewing TypeScript. Standards grouped by category with eslint rule codes. All examples show correct (✅) and incorrect (❌) patterns.
</quick_start>

<success_criteria>
Code follows these standards when tsc strict mode and eslint checks pass. See summary table at the end for the complete rejection criteria with rule codes.
</success_criteria>

<reference_note>
This is a reference skill. Other TypeScript skills reference these standards. You typically don't invoke this directly—invoke `/coding-typescript`, `/testing-typescript`, or `/auditing-typescript` instead.

These standards apply to ALL TypeScript code: production and test code alike.
</reference_note>

---

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

---

<named_constants>

Test values and configuration must use named constants, not inline literals.

```typescript
// ✅ REQUIRED: Named constants at module level
const VALID_SCORE = 85;
const MIN_SCORE = 0;
const MAX_SCORE = 100;
const VALID_INPUT = "simple";
const EXPECTED_RESULT = 42;

describe("ScoreValidation", () => {
  it("accepts valid score", () => {
    expect(validateScore(VALID_SCORE)).toBe(true);
  });

  it("rejects above maximum", () => {
    expect(validateScore(MAX_SCORE + 1)).toBe(false);
  });
});

// ❌ REJECTED: Magic values
describe("ScoreValidationBad", () => {
  it("accepts valid score", () => {
    expect(validateScore(85)).toBe(true); // What is 85?
  });

  it("rejects above maximum", () => {
    expect(validateScore(101)).toBe(false); // Magic number
  });
});
```

**Why named constants matter:**

- Sharing between tests and production code
- Clear documentation of what values mean
- Easy updates when requirements change
- Self-documenting test intent

**ESLint rules enforced:**

| Rule                                | What it catches              |
| ----------------------------------- | ---------------------------- |
| no-magic-numbers                    | Literal numbers in code      |
| @typescript-eslint/no-magic-numbers | TypeScript-specific literals |

**Rule exemptions:** ESLint already exempts common idiomatic values: `0`, `1`, `-1` in array indexes, and enum values. You don't need constants for these.

```typescript
// ✅ OK: Idiomatic values are exempt
expect(results.length).toBe(0);
expect(count).toBe(1);
const first = items[0];
const last = items[items.length - 1];
```

</named_constants>

---

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

---

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

Context matters for security rules—a CLI tool invoked by the user has different trust boundaries than a web service. See `/auditing-typescript` for false positive handling.

**ESLint rules enforced:**

| Rule        | What it catches                             |
| ----------- | ------------------------------------------- |
| no-eval     | Use of `eval()`                             |
| no-new-func | Use of `new Function()`                     |
| (manual)    | Hardcoded secrets                           |
| (manual)    | `child_process.exec()` with untrusted input |

</security>

---

<code_hygiene>

```typescript
// ❌ REJECTED: Unused variables (@typescript-eslint/no-unused-vars)
import { processData } from "./utils"; // Never used
const unusedVariable = 42;

// ❌ REJECTED: Dead code or commented-out code
// function oldImplementation() {
//   return 42;
// }

// ❌ REJECTED: console.log in production code (no-console)
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
| no-console                        | `console.log` in production code |
| (manual)                          | Dead code or commented-out code  |

</code_hygiene>

---

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

**Infrastructure** is stable code that doesn't move when your feature moves. Must use path aliases:

```typescript
// ❌ REJECTED: Deep relative to infrastructure
import { createTree } from "../../../../../../tests/helpers";

// ✅ REQUIRED: Path alias
import { createTree } from "@testing/helpers";
```

**Anti-Patterns**

```typescript
// ❌ REJECTED: Deep relative imports
import { helper } from "../../../../lib/utils";

// ❌ REJECTED: Assuming working directory
import { helper } from "lib/utils"; // Only works if CWD is project root
```

**Required Project Setup**

**1. Configure `tsconfig.json` with path aliases:**

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@testing/*": ["tests/*"],
      "@lib/*": ["src/lib/*"]
    }
  }
}
```

**2. Common path alias patterns:**

| Alias        | Maps to     | Purpose                    |
| ------------ | ----------- | -------------------------- |
| `@/*`        | `src/*`     | Main application code      |
| `@testing/*` | `tests/*`   | Test helpers and utilities |
| `@lib/*`     | `src/lib/*` | Shared library code        |

**3. Usage with path aliases:**

```typescript
// ✅ REQUIRED: Stable infrastructure via alias
import { processData } from "@/features/processing";
import { Logger } from "@lib/logger";
import { createMockContext } from "@testing/helpers";

// ✅ ACCEPTABLE: Module-internal relative
import { Position } from "./position";
import { tokenize } from "./tokens";
```

</import_hygiene>

---

<rejection_criteria_summary>

| Issue                            | Example                                     | Rule/Tool                                     |
| -------------------------------- | ------------------------------------------- | --------------------------------------------- |
| Unqualified `any`                | `function f(x: any): any`                   | @typescript-eslint/no-explicit-any            |
| `@ts-ignore` without reason      | `// @ts-ignore`                             | @typescript-eslint/ban-ts-comment             |
| Type assertion without narrowing | `return x as string`                        | @typescript-eslint/consistent-type-assertions |
| Unconstrained generic            | `function f<T>(x: T)`                       | tsc strict mode                               |
| Union without narrowing          | `value.toUpperCase()` on `string \| number` | tsc strict mode                               |
| Magic numbers in tests           | `expect(result).toBe(42)`                   | @typescript-eslint/no-magic-numbers           |
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
