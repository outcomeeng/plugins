# Example Architecture Review

This is a complete example of a REJECTED review showing all concern types.

# ARCHITECTURE REVIEW

**Decision:** REJECTED

## Verdict

| # | Concern               | Status | Detail                                      |
| - | --------------------- | ------ | ------------------------------------------- |
| 1 | Section structure     | REJECT | Contains phantom "Testing Strategy" section |
| 2 | Testability in Verif. | REJECT | Verification has no DI/no-mocking rules     |
| 3 | Atemporal voice       | REJECT | Decision statement narrates code state      |
| 4 | Mocking prohibition   | REJECT | "mock the execa calls at the boundary"      |
| 5 | Level accuracy        | PASS   | Level references are correct                |
| 6 | Anti-patterns         | REJECT | Level assignment table in Testing Strategy  |
| 7 | Ancestor consistency  | PASS   | Consistent with product ADRs                |

---

## Violations

### Mocking External Service

**Where:** decision statement, "mock the execa calls at the boundary"
**Concern:** Mocking prohibition
**Why this fails:** ADR prescribes mocking where dependency injection is required. Testing principles mandate DI with TypeScript interfaces, not mocking.

**Correct approach:**

```typescript
interface BuildDependencies {
  run: (cmd: string[], opts?: ExecOptions) => Promise<ExecResult>;
}

// l1: inject controlled implementation
// l2: inject real binary wrapper
```

---

### Phantom Testing Strategy Section

**Where:** "## Testing Strategy" section with level assignment table
**Concern:** Section structure, Anti-patterns
**Why this fails:** The authoritative ADR template has no Testing Strategy section. Level assignments are a downstream concern for `/test`. Testability constraints belong under `## Verification`'s `### Audit` subsection as ALWAYS/NEVER rules.

**Correct approach:**

```markdown
## Verification

### Audit

- ALWAYS: external tool invocations accept a dependency-injected runner
  parameter -- enables `l1` testing of command logic ([audit])
- NEVER: direct child_process.exec/spawn without a DI wrapper -- prevents
  isolated testing ([audit])
```

---

### Missing Testability in Verification

**Where:** `## Verification`
**Concern:** Testability in Verification
**Why this fails:** The `## Verification` rules cover error handling and config validation but include no ALWAYS/NEVER rules for dependency injection or mocking prohibition. Removing the phantom Testing Strategy section is not enough -- the testability constraints must move here, under `### Audit`.

---

### Temporal Language in the Decision Statement

**Where:** decision statement, "The current BuildRunner class in build.ts shells out to Hugo directly without dependency injection, making `l1` testing impossible."
**Concern:** Atemporal voice
**Why this fails:** Narrates code state -- becomes false the moment the file changes. The ADR states what the architecture IS, not what code currently exists.

**Correct approach:**

```markdown
Build orchestration uses dependency injection to isolate tool invocation from
build logic, so command-building is verifiable at `l1`.
```

---

## Required Changes

1. Remove phantom "Testing Strategy" section entirely
2. Add ALWAYS/NEVER testability rules under `## Verification`'s `### Audit` (DI, no mocking)
3. Replace "mock at boundary" with DI interface approach
4. Rewrite the decision statement in atemporal voice -- no references to current code state

---

## References

- /typescript-architecture-standards: `<adr_sections>` (no Testing Strategy section)
- /typescript-architecture-standards: `<testability_in_verification>` (ALWAYS/NEVER pattern)
- /typescript-architecture-standards: `<atemporal_voice>` (temporal patterns)
- /typescript-architecture-standards: `<di_patterns>` (mocking prohibition)

---

Revise and resubmit.
