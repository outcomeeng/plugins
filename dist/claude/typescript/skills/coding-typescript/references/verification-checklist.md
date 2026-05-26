# Pre-Submission Verification Checklist

Before declaring "done," confirm:

## Required Checks

- [ ] All tsc errors resolved
- [ ] All eslint errors resolved (auto-fix applied where safe)
- [ ] All tests pass
- [ ] Coverage ≥80% for new code
- [ ] JSDoc present for all public functions
- [ ] No TODO/FIXME comments left unaddressed
- [ ] No console.log statements (use logger)
- [ ] No hardcoded secrets or paths

## Tool Commands

Resolve placeholders from the repository's docs, package scripts, Makefile, Justfile, or local agent instructions. Raw `tsc`, `eslint`, or `vitest` commands are fallback commands only when the repository has no validation wrapper.
When sources conflict, resolve in this priority: local agent instructions, repository docs, Justfile, Makefile, package scripts, raw tool fallback.

```bash
# TypeScript validation through the repository's canonical command
<product-typecheck-command>

# Auto-fix style issues through the repository's canonical command, when available
<product-lint-fix-command>

# Lint validation through the repository's canonical command
<product-lint-command>

# Run tests through the repository's canonical command
<product-test-command>

# Bare-repo fallback examples only when no repository wrapper exists:
# npx tsc --noEmit
# npx eslint src/ test/ --fix
# npx eslint src/ test/
# npx vitest run
```

## Completion Criteria Table

| Criterion                            | Status   |
| ------------------------------------ | -------- |
| Spec fully implemented               | Required |
| All functions have type annotations  | Required |
| All public functions have JSDoc      | Required |
| Tests exist for all public functions | Required |
| tsc passes with zero errors          | Required |
| eslint passes with zero errors       | Required |
| All tests pass                       | Required |
| Coverage ≥80% for new code           | Required |
| No TODOs/FIXMEs unaddressed          | Required |
| No console.log statements            | Required |
| No hardcoded secrets                 | Required |

## What to Check For

### Type Safety

- No `any` without explicit justification
- No `@ts-ignore` without explanation (prefer `@ts-expect-error`)
- All function parameters and returns are typed

### Code Quality

- Public functions have JSDoc with @param/@returns/@throws
- No dead code or commented-out code blocks
- Constants are UPPER_SNAKE_CASE, no magic numbers
- Dependencies injected via parameters

### Testing

- Tests exist for all public functions
- Tests cover edge cases
- Tests use descriptive names
- No mocking - dependency injection only
