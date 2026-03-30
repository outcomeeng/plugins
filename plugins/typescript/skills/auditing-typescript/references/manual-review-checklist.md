# Manual Review Checklist (Phase 4)

Read ALL code under review. Check each item:

## Project Convention Matching (CHECK FIRST)

**New code must fit the existing project, not introduce foreign patterns.**

- [ ] Uses libraries from `package.json` (no new dependencies without justification)
- [ ] Follows project's naming conventions (check 3-5 existing files in same directory)
- [ ] Reuses existing utilities instead of reinventing (grep for similar functions)
- [ ] Matches project's error handling pattern (custom error classes, logging style)
- [ ] File structure matches project conventions (where do types go? configs?)

### Convention Rejection Criteria

| Violation                       | Example                                              | Verdict  |
| ------------------------------- | ---------------------------------------------------- | -------- |
| Adds dependency when one exists | Uses `axios` when project has `fetch` wrapper        | REJECTED |
| Invents new utility             | New `formatDate()` when `@/utils/date` exists        | REJECTED |
| Wrong naming convention         | `fetch_user` when project uses `fetchUser`           | REJECTED |
| Different error style           | Bare `throw new Error()` when project has `AppError` | REJECTED |
| Ignores existing patterns       | New logging approach when `@/lib/logger` exists      | REJECTED |

**If conventions are unclear**: Check `docs/`, `CLAUDE.md`, `README.md` before rejecting. If no docs exist and code is inconsistent, flag for clarification rather than rejecting.

## Type Safety (Beyond tsc)

- [ ] No use of `any` without explicit justification
- [ ] No `@ts-ignore` without explanation comment (prefer `@ts-expect-error`)
- [ ] Union types are narrowed before use
- [ ] Generic types are properly constrained
- [ ] `as` assertions are justified (prefer type guards)

## Error Handling

- [ ] No empty `catch` blocks (swallowing all errors)
- [ ] Custom error classes for domain errors
- [ ] Error messages include context (what failed, with what input)
- [ ] Async errors are properly caught (no unhandled rejections)

## Resource Management

- [ ] Streams and connections properly closed
- [ ] `finally` blocks for cleanup where needed
- [ ] Timeouts specified for network/subprocess operations
- [ ] AbortController used for cancellable operations

## Security

- [ ] No hardcoded secrets, API keys, or passwords
- [ ] No `eval()` or `new Function()` usage
- [ ] No `child_process.exec()` with user input (use `execFile`)
- [ ] Input validation present where needed
- [ ] SSL verification enabled for HTTP requests

## Code Quality

- [ ] Public functions have JSDoc with @param/@returns/@throws
- [ ] No dead code or commented-out code blocks
- [ ] No unused imports
- [ ] Function names are verbs (`getUser`, `calculateTotal`)
- [ ] Class names are nouns (`UserRepository`, `PaymentProcessor`)
- [ ] Constants are UPPER_SNAKE_CASE
- [ ] No magic numbers (use named constants)

## Architecture

- [ ] Dependencies injected via parameters, not imported globals
- [ ] No circular imports
- [ ] Single responsibility per module/class
- [ ] Clear separation of concerns (IO vs logic)

## Import Hygiene

**Before evaluating any import, ask yourself:**

> "Is this import referring to a **module-internal file** (lives in the same module, will move together) or **infrastructure** (stable locations like `lib/`, `tests/helpers/`, `shared/`)?"

- [ ] No deep relative imports (2+ levels of `../`)
- [ ] Imports to stable locations use path aliases, not relative paths
- [ ] Module-internal files may use `./` or `../` (1 level max)
- [ ] Test files use `@testing/` alias for shared test infrastructure

### Module-Internal vs. Infrastructure

**Module-internal files** live together and move together. Relative imports are acceptable because if you move the module, you move both files:

```typescript
// ✅ ACCEPTABLE: Same module, files move together
// File: src/parser/lexer.ts
import { Position } from "./position"; // These files are part of "parser" module
import { Token } from "./token"; // ./token.ts is in same directory
```

**Stable locations** are infrastructure that doesn't move when your feature moves. These MUST use path aliases:

```typescript
// ❌ REJECT: test helpers are stable infrastructure
// File: spx/21-core-cli.enabler/54-commands.enabler/54-run.outcome/tests/validate.test.ts
import { helper } from "../../../../../../tests/helpers/tree-builder";

// ✅ ACCEPT: Use path alias for stable locations
import { helper } from "@testing/helpers/tree-builder";
```

### Depth Rules (Strict)

| Depth     | Example        | Verdict | Rationale                                   |
| --------- | -------------- | ------- | ------------------------------------------- |
| Same dir  | `./utils`      | OK      | Module-internal, same module                |
| 1 level   | `../types`     | REVIEW  | Is this truly module-internal?              |
| 2+ levels | `../../config` | REJECT  | Use path alias — this crosses module bounds |

### Examples: Module-Internal (Relative OK)

```typescript
// File: src/commands/build/index.ts
import { formatOutput } from "../shared"; // ⚠️ Review: is "shared" truly module-internal?
import { BuildOptions } from "./types"; // ✅ Same command module
import { validateArgs } from "./validate"; // ✅ Same command module

// File: src/parser/ast/node.ts
import { NodeType } from "../types"; // ⚠️ Borderline: "../types" might be shared infrastructure
import { Position } from "./position"; // ✅ Same AST module
```

### Examples: Stable Locations (Path Alias Required)

```typescript
// ❌ REJECT: These are all stable infrastructure
import { createTestDb } from "../../../../../../tests/helpers/db";
import { Logger } from "../../../../lib/logging";
import { Config } from "../../../shared/config";

// ✅ ACCEPT: Use configured path aliases
import { Logger } from "@lib/logging";
import { Config } from "@shared/config";
import { createTestDb } from "@testing/helpers/db";
```

### Examples: Test Files (Special Attention)

Test files are the most common source of deep relative imports:

```typescript
// File: tests/integration/api/users.test.ts
// ❌ REJECT: Reaching back into src with relatives
import { UserService } from "../../../src/services/user";
import { createFixture } from "../../helpers/fixtures";

// ✅ ACCEPT: Path aliases make intent clear
import { UserService } from "@/services/user";
import { createFixture } from "@testing/helpers/fixtures";

// File: spx/21-core-cli.enabler/54-commands.enabler/42-run.outcome/tests/feature.test.ts
// ❌ REJECT: Deep relative to shared test helpers
import { helper } from "../../../../../../tests/helpers/tree-builder";

// ✅ ACCEPT: Alias for test infrastructure
import { helper } from "@testing/helpers/tree-builder";
```

### Examples: Monorepo Packages

```typescript
// File: packages/cli/src/commands/init.ts
// ❌ REJECT: Crossing package boundaries with relatives
import { Logger } from "../../../shared/src/logging";
import { Config } from "../../config/src/types";

// ✅ ACCEPT: Use workspace package imports
import { Config } from "@myorg/config";
import { Logger } from "@myorg/shared";
```

### Required tsconfig.json Setup

When you reject code for deep imports, guide the developer to configure aliases:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@testing/*": ["tests/*"],
      "@lib/*": ["lib/*"],
      "@shared/*": ["shared/*"]
    }
  }
}
```

For monorepos with project references:

```json
{
  "compilerOptions": {
    "paths": {
      "@myorg/shared": ["packages/shared/src"],
      "@myorg/config": ["packages/config/src"]
    }
  },
  "references": [
    { "path": "../shared" },
    { "path": "../config" }
  ]
}
```

### Decision Tree for Import Review

```text
Is this import using 2+ levels of "../"?
├── NO → ✅ Likely acceptable (verify it's truly module-internal)
└── YES → Is the target a stable location (lib/, tests/helpers/, shared/)?
    ├── YES → ❌ REJECT: Must use path alias
    └── NO → Is this a temporary/experimental structure?
        ├── YES → ⚠️ WARN: Will need refactoring before merge
        └── NO → ❌ REJECT: Restructure or add path alias
```

## Testing

**Test Existence & Coverage**:

- [ ] Tests exist for public functions
- [ ] Tests cover edge cases (empty inputs, null, large values)
- [ ] Tests use descriptive names that explain the scenario
- [ ] No hardcoded paths or environment-specific values in tests
- [ ] Fixtures clean up after themselves

See `references/verification-tests.md` for test organization rules.

## ADR/PDR Compliance

> **ADRs/PDRs GOVERN — compliance is verified through code review, not testing.**

Check that implementation follows all applicable ADR/PDR constraints:

- [ ] Code structure conforms to ADR architectural decisions
- [ ] Implementation approach matches ADR-specified patterns
- [ ] Dependencies align with ADR technology choices
- [ ] Test levels match ADR Testing Strategy (Level 1/2/3)
- [ ] Product behavior conforms to PDR-defined constraints
- [ ] Deviations from ADRs/PDRs are documented or decision records are updated

**How to check**:

1. Find applicable ADRs/PDRs in the spec hierarchy (`*.adr.md`, `*.pdr.md`)
2. Verify each ADR/PDR decision is followed in the implementation
3. Flag any undocumented deviations as REJECTED

**Common ADR/PDR violations**:

| Decision Record Constraint           | Violation Example                   | Verdict  |
| ------------------------------------ | ----------------------------------- | -------- |
| "Use dependency injection" (ADR)     | Direct imports of external services | REJECTED |
| "Level 1 tests for logic" (ADR)      | Unit tests hitting network          | REJECTED |
| "No class components" (ADR)          | React class component added         | REJECTED |
| "Lifecycle is Draft→Published" (PDR) | Added hidden `Archived` state       | REJECTED |
