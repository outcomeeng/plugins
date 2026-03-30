# Verification Protocol (Phases 6-7)

> **Write access is earned by passing review.** This phase only runs on APPROVED.

## Phase 6: Verify Tests Pass

When all checks pass, verify all tests for the work item pass.

### 6.1 Identify Test Files

**Test Files tables in specs are contractual.** Every link must resolve to an actual file. Stale links = REJECTED. This is distinct from the **Analysis section** (stories only), which documents the agent's codebase examination. Analysis references may diverge from implementation — do NOT reject specs for stale Analysis references.

Locate tests in the work item directory:

```bash
find spx/ -path "*/{work-item}/tests/*.test.ts" -name "*.test.ts"
```

Test files are co-located with their specs:

| Test Level  | Location                           | Filename Suffix         |
| ----------- | ---------------------------------- | ----------------------- |
| Unit        | `spx/.../NN-{slug}.outcome/tests/` | `*.unit.test.ts`        |
| Integration | `spx/.../NN-{slug}.enabler/tests/` | `*.integration.test.ts` |
| E2E         | `spx/NN-{slug}.outcome/tests/`     | `*.e2e.test.ts`         |

### 6.2 Run Tests

Run all tests for the work item:

```bash
npx vitest run spx/.../NN-{slug}.outcome/tests/
```

**If tests fail**: The verdict becomes REJECTED with reason "Tests don't pass."

## Phase 7: Verification Summary

Report verification completion.

### 7.1 Final Output

```markdown
## Review Complete: {work-item}

### Verdict: APPROVED

### Verification

| Tool            | Status | Details                      |
| --------------- | ------ | ---------------------------- |
| `pnpm validate` | PASS   | Project validation succeeded |
| vitest          | PASS   | {X}/{X} tests, {Y}% coverage |

### Tests Passing

| Test File                 | Status |
| ------------------------- | ------ |
| `feature.unit.test.ts`    | PASS   |
| `edge-cases.unit.test.ts` | PASS   |

### Work Item Status

This work item is now DONE.
```

**Continue to**: `workflows/commit-protocol.md`
