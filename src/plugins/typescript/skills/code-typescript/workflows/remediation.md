<required_reading>

- Read the complete rejection feedback, including every referenced file and line.
- Read the affected code in context before editing.
- For a spec-tree work item, require the live governing node context and read every loaded spec, ADR, and PDR before editing. For a non-spec-tree item, require the caller-provided specification or contract and block when none is available.
- Read `/typescript-standards` and `/typescript-test-standards` before changing implementation or tests.
- Before changing TypeScript tests for a spec-tree work item, invoke `/test-typescript <full-spx-node-path>`; that skill owns test-evidence repair and the resolved product test command. For a non-spec-tree item, apply `/typescript-test-standards` to the caller-provided contract and resolve the product test command from the repository.

</required_reading>

<process>

1. Validate each finding against its cited rule, then classify it as valid or unbacked according to the governing verifier and merge contracts. Preserve the verifier's concrete file and line references. Repair every valid finding and re-run review; when its repair belongs to a capability too large for the changeset, remove that capability before re-review. Treat only an exact operator waiver that accepts the finding's stated consequence as waiver evidence; tracking, general merge authorization, and severity-only authorization resolve nothing.
2. Apply the finding-validity gate before editing: proceed only when every finding has an individual validity classification backed by its cited rule. A valid finding enters the repair set; an unbacked finding records the refutation evidence. An unclassified finding blocks editing until its rule and changed site are inspected.
3. Group repeated findings by root cause. A single wrong return type, missing source contract, or invalid abstraction can surface as many local failures.
4. Identify the actual layer in violation: implementation, test evidence, source contract, or specification alignment. Do not change tests to make implementation defects disappear.
5. For complex fixes, write a brief local plan before editing:

```text
Fix Plan

Issue: {description}

**Root Cause**: {why this happened}

**Fix Approach**:

1. {step 1}
2. {step 2}

**Verification**: {how to prove it's fixed}
```

6. Apply fixes systematically, keeping changes bounded to the rejected defect class and any same-class instances in the touched node.
7. Use `@ts-expect-error` or lint suppression only with a precise reason and only when the governing rules allow the exception.
8. When the rejection identifies missing or weak evidence, route spec-tree test additions or corrections through `/test-typescript <full-spx-node-path>`. For non-spec-tree work, apply `/typescript-test-standards` to the caller-provided contract and repository-resolved test command. The added test names the behavior and fails for the original defect.
9. Run the focused test as the inner loop. Then run the product's resolved TypeScript test command for the governed node or changeset, followed by typecheck, lint, and repository-selected validation commands. Repeat the fix loop until every command passes.
10. Apply the re-review-readiness gate: proceed only when every valid finding has repair evidence, every unbacked finding has refutation evidence, the resolved TypeScript test command and all selected validation commands pass, and the changeset is ready to present as one exact re-review subject.
11. Prepare the re-review summary with original issue, fix applied, and verification command output.

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
# npx eslint . --fix
# npx eslint .
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

- The re-review summary maps every input finding ID to a repaired file and line, an evidence-backed refutation, removed capability, or exact operator waiver accepting that finding's consequence.
- The summary names the artifact layer changed for each valid finding, and no spec or test change weakens a higher-layer contract to match defective implementation.
- The same-class sweep records every inspected touched path and reports zero unrepaired parallel instances.
- The focused inner-loop test, resolved TypeScript test command for the governed node or changeset, typecheck, lint, and selected validation commands each exit successfully and appear with their exact command and result in the verification table.
- A current-head re-review reports no unresolved valid finding, except an individually recorded exact operator waiver.

</success_criteria>
