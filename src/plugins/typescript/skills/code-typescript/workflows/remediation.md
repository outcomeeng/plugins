<required_reading>

- Read the complete rejection feedback, including every referenced file and line.
- Read the affected code in context before editing.
- Read the governing spec, ADR, or PDR when the rejection concerns compliance or product behavior.
- Read `/typescript-standards` and `/typescript-test-standards` before changing implementation or tests.

</required_reading>

<process>

1. Validate each finding against its cited rule, then classify it as valid in-scope, unbacked, or a separate larger concern according to the governing verifier and merge contracts. Preserve the verifier's concrete file and line references.
2. Group repeated findings by root cause. A single wrong return type, missing source contract, or invalid abstraction can surface as many local failures.
3. Identify the actual layer in violation: implementation, selected test or eval evidence, a pathless audit requirement, source contract, or specification alignment. Do not change evidence to make implementation defects disappear.
4. For complex fixes, write a brief local plan before editing:

```text
Fix Plan

Issue: {description}

**Root Cause**: {why this happened}

**Fix Approach**:

1. {step 1}
2. {step 2}

**Verification**: {how to prove it's fixed}
```

5. Apply fixes systematically, keeping changes bounded to the rejected defect class and any same-class instances in the touched node.
6. Use `@ts-expect-error` or lint suppression only with a precise reason and only when the governing rules allow the exception.
7. When the rejection identifies missing or weak evidence, return to `/verify` and its selected specialist. Add a regression test only when test is selected; extend eval evidence only through the eval specialist; preserve pathless audit requirements for their isolated verifier.
8. Run every selected test and eval command, then typecheck, lint, and repository-selected validation commands. Require selected evals to meet their declared thresholds. Repeat the fix loop until all selected commands pass.
9. Prepare the re-review summary with original issue, fix applied, and verification command output.

Common remediation patterns:

```typescript
// WRONG - Suppressing without understanding
const result = someFunction(); // @ts-ignore

// RIGHT - Fix the actual type
const result: ExpectedType = someFunction();

// RIGHT - If truly unavoidable, explain
// @ts-expect-error - external library lacks type definitions
const result = externalLib.call();
```

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

```typescript
it("GIVEN empty email WHEN parsing user THEN throws ValidationError", () => {
  // Regression: Reviewer caught missing empty email handling.
  const input = { name: "John", email: "" };

  expect(() => parseUser(input)).toThrow(ValidationError);
  expect(() => parseUser(input)).toThrow(/email/);
});
```

```bash
<product-typecheck-command>
<product-lint-fix-command>
<product-lint-command>
<product-test-command>

# Bare-repo fallback examples only when no repository wrapper exists:
# npx tsc --noEmit
# npx eslint src/ test/ --fix
# npx eslint src/ test/
# npx vitest run
```

```text
Fixes Applied

Issues Addressed

| Original Issue            | Fix Applied    | Verification |
| ------------------------- | -------------- | ------------ |
| {file:line - description} | {what changed} | {tool/test}  |

Verification Results

| Command                  | Result     |
| ------------------------ | ---------- |
| `<command actually run>` | `<result>` |

Ready for Re-Review

This fix is ready for re-review.
```

</process>

<success_criteria>

- Every verifier finding has a traced root cause and a bounded disposition.
- Implementation defects are fixed in implementation, evidence defects route through `/verify` and the selected specialist, and specs are not weakened to match broken lower layers.
- Same-class defects across the touched node have been swept.
- Selected tests pass, selected evals meet their thresholds, pathless audit requirements remain recorded, and typecheck, lint, and selected validation pass through repository-selected commands.

</success_criteria>
