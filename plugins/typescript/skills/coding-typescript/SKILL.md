---
name: coding-typescript
description: >-
  ALWAYS invoke this skill when writing or fixing implementation code for TypeScript.
allowed-tools: Read, Write, Bash, Glob, Grep, Edit
---

<accessing_skill_files>
When this skill is invoked, Claude Code provides the base directory in the loading message:

```
Base directory for this skill: {skill_dir}
```

Use this path to access skill files:

- References: `{skill_dir}/references/`
- Workflows: `{skill_dir}/workflows/`

**IMPORTANT**: Do NOT search the project directory for skill files.
</accessing_skill_files>

<reference_loading>
Before discovery or implementation, read `/standardizing-typescript`, then `/standardizing-typescript-tests`. After that, check for `spx/local/typescript.md` and `spx/local/typescript-tests.md` at the repository root. Read each file that exists and apply it as the repo-local specialization.
</reference_loading>

<essential_principles>
**NO MOCKING. DEPENDENCY INJECTION. BEHAVIOR ONLY. TEST FIRST.**

- Use **dependency injection**, NEVER mocking frameworks
- Test **behavior** (what the code does), not implementation (how it does it)
- Run all verification tools before declaring completion
- Type safety first: `strict: true`, no `any` without justification

</essential_principles>

<mandatory_code_patterns>
These patterns are enforced by the reviewer. Violations will be REJECTED.

### Constants

All literal values (strings, numbers) must be module-level constants:

```typescript
// ❌ REJECTED: Magic values inline
function validateScore(score: number): boolean {
  return score >= 0 && score <= 100;
}

// ✅ REQUIRED: Named constants
const MIN_SCORE = 0;
const MAX_SCORE = 100;

function validateScore(score: number): boolean {
  return score >= MIN_SCORE && score <= MAX_SCORE;
}
```

**Share constants between code and tests** — tests import from the module under test:

```typescript
// src/scoring.ts
export const MIN_SCORE = 0;
export const MAX_SCORE = 100;

// spx/.../tests/scoring.mapping.l1.test.ts
import { MIN_SCORE, validateScore } from "@/scoring";

it("rejects below minimum", () => {
  expect(validateScore(MIN_SCORE - 1)).toBe(false);
});
```

### Dependency Injection

External dependencies must be injected, not imported directly:

```typescript
// ❌ REJECTED: Direct import
import { execa } from "execa";

async function syncFiles(src: string, dest: string): Promise<boolean> {
  const result = await execa("rsync", [src, dest]);
  return result.exitCode === 0;
}

// ✅ REQUIRED: Dependency injection
interface SyncDeps {
  execa: typeof execa;
}

async function syncFiles(
  src: string,
  dest: string,
  deps: SyncDeps,
): Promise<boolean> {
  const result = await deps.execa("rsync", [src, dest]);
  return result.exitCode === 0;
}
```

</mandatory_code_patterns>

<hierarchy_of_authority>
**Where to look for guidance, in order of precedence:**

| Priority | Source                    | What It Provides                                      |
| -------- | ------------------------- | ----------------------------------------------------- |
| 1        | `docs/`, `README.md`      | Project architecture, design decisions, intended APIs |
| 2        | `CLAUDE.md`               | Project-specific rules for Claude                     |
| 3        | ADRs/PDRs, specs          | Documented decisions and requirements                 |
| 4        | This skill (`SKILL.md`)   | Generic TypeScript best practices                     |
| 5        | Existing code (reference) | Evidence of implementation, NOT authority             |

**CRITICAL: Existing code is NOT authoritative.**

- Documentation describes **intent** — what SHOULD be done
- Existing code shows **implementation** — what WAS done (may be legacy, wrong, or outdated)
- When docs and code conflict, **docs win**
- When no docs exist, ASK before copying existing patterns

**Never copy patterns from existing code without verifying they match documented intent.**

</hierarchy_of_authority>

<codebase_discovery>
**BEFORE writing any code, discover what already exists.**

### Phase 0: Discovery (MANDATORY)

Run these searches before implementation:

```bash
# 1. Read project documentation
Read: README.md, docs/, CLAUDE.md, CONTRIBUTING.md

# 2. Load the authoritative methodology
Read: relevant skills and spec docs before inferring any convention

# 3. Check available dependencies (don't add what exists)
Read: package.json → dependencies, devDependencies

# 4. Locate concrete artifacts to reuse
Glob/Grep: actual modules, harnesses, fixtures, registries, and entrypoints

# 5. Confirm local file placement
Read: existing files in the same directory you'll write to
```

### What to Discover

| Question                                            | How to Answer It                                                                |
| --------------------------------------------------- | ------------------------------------------------------------------------------- |
| What conventions govern this work?                  | Read the relevant skill, spec, ADR/PDR, `CLAUDE.md`, and project docs first     |
| What libraries are available?                       | `package.json` → dependencies                                                   |
| What concrete modules already exist to reuse?       | `Glob`/`Grep` for actual modules, registries, harnesses, fixtures, and helpers  |
| What error classes already exist?                   | Locate existing error modules; do not infer policy from random call sites       |
| What logging facility already exists?               | Locate the logger module or logging package, then follow documented rules       |
| How are configs structured?                         | Find config modules and config docs; do not infer config policy from ad hoc use |
| If this is a script, which arg parser is canonical? | Read `package.json`, docs, and existing checked-in `scripts/` entrypoints       |

### Discovery Anti-Patterns

```typescript
// ❌ WRONG: Adding lodash when ramda is already used
import _ from "lodash"; // package.json has ramda, not lodash

// ❌ WRONG: Creating new logger when one exists
const logger = console; // Project has @lib/logger

// ❌ WRONG: Inventing naming convention
function fetch_user_by_id() {} // Project uses camelCase

// ❌ WRONG: New error class when domain errors exist
class MyError extends Error {} // Project has @/errors

// ❌ WRONG: Inferring architecture from grep results
// "I saw three files use pattern X, so pattern X is the standard"
```

**Authority rule**: Skills, specs, ADRs/PDRs, `CLAUDE.md`, and project docs answer "how should this be done?" Code search answers only "where is the existing artifact I should reuse?"

### Script Entry Points

If you are editing a checked-in entrypoint under `scripts/`, treat it as boundary code:

- use the repository's canonical argument parsing library
- do not hand-roll `process.argv` parsing
- keep the script thin and dispatch to one orchestrator module or a small dispatcher
- allow relative imports, boundary env parsing, and console output when that avoids circular dependency problems

Before changing script behavior, answer these questions:

- Where is the orchestrator module this script should call?
- If the orchestrator touches a boundary, where is the harness?
- If there is no harness, where is the fixture data?
- Where is the spec for the orchestrator or harness?
- Where are the tests for the orchestrator or harness?

### Discovery Checklist

Before writing code, confirm:

- [ ] Loaded the relevant skill and spec documents before inferring conventions
- [ ] Read `package.json` — know what libraries are available
- [ ] Located reusable modules, harnesses, fixtures, registries, or helpers
- [ ] Identified the canonical logger/config/error modules from docs or known entrypoints
- [ ] If editing `scripts/`, identified the canonical argument parsing library
- [ ] If editing `scripts/`, found the orchestrator's spec and tests (or the harness/fixture gap)

**Never treat grep results as authority.** If existing code conflicts with the skill, spec, or docs, the documented rule wins.

</codebase_discovery>

<testing_methodology>
**For TypeScript testing guidance, load both `/standardizing-typescript-tests` and `/testing-typescript`.**

Use `/standardizing-typescript-tests` as the canonical source for:

- filename conventions
- allowed doubles and dependency-injection rules
- property-based testing requirements
- harness ownership and fixture placement
- source-owned test values and inline diagnostics

Use `/testing-typescript` for:

- router-driven level selection
- concrete Vitest and Playwright implementation patterns
- RED-phase expectations and test-writing workflows
- TypeScript-specific examples for the selected test level

When implementation changes affect test-owned interfaces, harnesses, or fixture boundaries, keep the production code aligned with both skills rather than re-declaring testing policy here.
</testing_methodology>

<context_loading>
**BEFORE ANY IMPLEMENTATION: Load complete specification context.**

**If working on a spec-tree work item** (enabler/outcome):

1. **Invoke `spec-tree:contextualizing` FIRST** with the node path
2. **If context loading fails**: ABORT - do not proceed until all required documents exist
3. **If context loading succeeds**: Proceed with implementation using loaded context

**The `spec-tree:contextualizing` skill provides:**

- Complete ancestor hierarchy (product → all ancestor nodes → target)
- All ADRs/PDRs at every level along the path
- Lower-index siblings (they constrain the target via dependency encoding)
- Target node spec with typed assertions

**Example invocation:**

```bash
# By node path
spec-tree:contextualizing spx/32-cli.enabler/54-commands.outcome
```

**If `spec-tree:contextualizing` returns an error**: The error message will specify which document is missing and how to create it. Create the missing document before proceeding with implementation.

**If NOT working on spec-tree work item**: Proceed directly to implementation mode with provided spec.
</context_loading>

<two_modes>
You operate in one of two modes depending on your input:

| Input                            | Mode               | Workflow                      |
| -------------------------------- | ------------------ | ----------------------------- |
| Spec (ADR/PDR, node spec)        | **Implementation** | `workflows/implementation.md` |
| Rejection feedback from reviewer | **Remediation**    | `workflows/remediation.md`    |

Determine your mode from the input, then follow the appropriate workflow.
</two_modes>

<core_principles>

1. **Spec Is Law**: The specification is your contract. Implement exactly what it says.

2. **Test-Driven Development**: Write tests first or alongside code. Tests prove correctness.

3. **Type Safety First**: Use strict TypeScript with `strict: true`. No `any` without justification.

4. **Self-Verification**: Before declaring "done," run tsc, eslint, and vitest yourself.

5. **Humility**: Your code must pass review. Write code that will survive adversarial review.

6. **Clean Architecture**: Dependency injection, single responsibility, no circular imports, **no deep relative imports**.

</core_principles>

<reference_index>

| File                                         | Purpose                               |
| -------------------------------------------- | ------------------------------------- |
| `references/outcome-engineering-patterns.md` | Subprocess, resource cleanup, config  |
| `references/test-patterns.md`                | Debuggability-first test organization |
| `references/verification-checklist.md`       | Pre-submission verification           |

</reference_index>

<workflows_index>

| Workflow                      | Purpose                         |
| ----------------------------- | ------------------------------- |
| `workflows/implementation.md` | TDD phases, code standards      |
| `workflows/remediation.md`    | Fix issues from review feedback |

</workflows_index>

<what_not_to_do>
**Never Self-Approve**: Always submit for review.

**Never Skip Tests**: Write tests first. No exceptions.

**Never Ignore Type Errors**:

```typescript
// WRONG
const result = someFunction(); // @ts-ignore

// RIGHT
const result: ExpectedType = someFunction();
```

**Never Hardcode Secrets**:

```typescript
// WRONG
const API_KEY = "sk-1234567890abcdef";

// RIGHT
const API_KEY = process.env.API_KEY;
if (!API_KEY) throw new Error("API_KEY required");
```

**Never Use Deep Relative Imports**:

Before writing any import, ask: *"Is this a module-internal file (same module, moves together) or infrastructure (lib/, tests/helpers/, shared/)?"*

```typescript
// WRONG: Deep relatives to stable locations — will REJECT in review
import { helper } from "../../../../../../tests/helpers/tree-builder";
import { Logger } from "../../../../lib/logging";
import { Config } from "../../../shared/config";

// RIGHT: Configure path aliases in tsconfig.json
import { Logger } from "@lib/logging";
import { Config } from "@shared/config";
import { helper } from "@testing/helpers/tree-builder";
```

**Depth Rules:**

- `./sibling` — ✅ OK (same directory, module-internal)
- `../parent` — ⚠️ Review (is it truly module-internal?)
- `../../` or deeper — ❌ REJECT (use path alias)

**Configure tsconfig.json:**

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@testing/*": ["tests/*"],
      "@lib/*": ["lib/*"]
    }
  }
}
```

</what_not_to_do>

<tool_invocation>

```bash
# Type checking
npx tsc --noEmit

# Linting
npx eslint src/ test/
npx eslint src/ test/ --fix

# Testing
npx vitest run --coverage
```

</tool_invocation>

<success_criteria>
Your implementation is ready for review when:

- [ ] Spec fully implemented
- [ ] All functions have type annotations
- [ ] All public functions have JSDoc
- [ ] Tests exist for all public functions
- [ ] tsc passes with zero errors
- [ ] eslint passes with zero errors
- [ ] All tests pass
- [ ] Coverage ≥80% for new code
- [ ] No TODOs/FIXMEs unaddressed
- [ ] No console.log statements
- [ ] No hardcoded secrets

*Your code will face an adversarial reviewer with zero tolerance. Write code that will survive that scrutiny.*
</success_criteria>
