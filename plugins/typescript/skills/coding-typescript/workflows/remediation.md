# Remediation Protocol

When your input is **rejection feedback** from a reviewer, follow this protocol.

## Phase R0: Parse the Rejection

1. **Read the rejection feedback** completely
2. **Categorize issues**:
   - **Blocking**: Must fix (type errors, security, test failures, design problems)
   - **Conditional**: Need eslint-disable with justification (false positives)
   - **Warnings**: Should fix but not blocking
3. **Identify affected files**: List every file:line mentioned
4. **Check for patterns**: Multiple similar issues may have a common root cause

## Phase R1: Understand Root Cause

Before fixing, understand WHY the code was rejected:

1. **Read the affected code** in context (not just the flagged line)
2. **Read the spec/decision record (ADR/PDR)** if the issue is about compliance
3. **Identify root cause vs symptoms**:
   - If 5 type errors stem from one wrong return type, fix the return type
   - If tests fail because of a logic error, fix the logic (not the test assertions)

## Phase R2: Plan Non-Trivial Fixes

For complex fixes, write a brief plan:

```markdown
## Fix Plan

### Issue: {description}

**Root Cause**: {why this happened}

**Fix Approach**:

1. {step 1}
2. {step 2}

**Verification**: {how to prove it's fixed}
```

## Phase R3: Apply Fixes

Fix systematically. Common patterns:

**Type Errors**:

```typescript
// WRONG - Suppressing without understanding
const result = someFunction(); // @ts-ignore

// RIGHT - Fix the actual type
const result: ExpectedType = someFunction();

// RIGHT - If truly unavoidable, explain
// @ts-expect-error - external library lacks type definitions
const result = externalLib.call();
```

**Security Issues**:

```typescript
// WRONG - Ignoring security rule
// eslint-disable-next-line security/detect-child-process
exec(userInput);

// RIGHT - Remove the vulnerability
execFile(command, args); // No shell, no injection

// RIGHT - If context makes it safe, explain fully
// eslint-disable-next-line security/detect-child-process -- command is hardcoded, no user input
exec("git status");
```

**Test Failures**:

1. Read the test to understand what it's checking
2. Read the implementation to understand actual behavior
3. Determine which is wrong:
   - If test is wrong: Fix test AND explain why
   - If implementation is wrong: Fix implementation
   - If both are wrong: Fix both

**Spec Deviations**:

1. Quote the spec requirement you're aligning to
2. Show the deviation in current code
3. Implement the aligned version
4. Add a test that verifies spec compliance

## Phase R4: Add Missing Tests

If the rejection identified missing test coverage:

1. Add named test for the specific case that was broken
2. Add edge case tests if the bug was an edge case
3. Follow the 4-part debuggability progression

```typescript
it("GIVEN empty email WHEN parsing user THEN throws ValidationError", () => {
  // Regression: Reviewer caught missing empty email handling.
  const input = { name: "John", email: "" };

  expect(() => parseUser(input)).toThrow(ValidationError);
  expect(() => parseUser(input)).toThrow(/email/);
});
```

## Phase R5: Self-Verification

Run ALL tools before declaring fixed:

```bash
<project-typecheck-command>
<project-lint-fix-command>
<project-lint-command>
<project-test-command>

# Bare-repo fallback examples only when no repository wrapper exists:
# npx tsc --noEmit
# npx eslint src/ test/ --fix
# npx eslint src/ test/
# npx vitest run
```

**All must pass.** If any fail, go back to Phase R3.

## Phase R6: Submit for Re-Review

```markdown
## Fixes Applied

### Issues Addressed

| Original Issue            | Fix Applied    | Verification |
| ------------------------- | -------------- | ------------ |
| {file:line - description} | {what changed} | {tool/test}  |

### Verification Results

| Tool   | Status           |
| ------ | ---------------- |
| tsc    | PASS (0 errors)  |
| eslint | PASS (0 errors)  |
| vitest | PASS (X/X tests) |

### Ready for Re-Review

This fix is ready for re-review.
```
