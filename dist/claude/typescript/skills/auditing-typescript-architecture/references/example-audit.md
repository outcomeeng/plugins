# Example Architecture Review

This is a complete example of a REJECTED review showing all concern types.

# ARCHITECTURE REVIEW

**Decision:** REJECTED

## Verdict

| # | Concern               | Status | Detail                                      |
| - | --------------------- | ------ | ------------------------------------------- |
| 1 | Section structure     | REJECT | Contains phantom "Testing Strategy" section |
| 2 | Testability in Compl. | REJECT | Compliance has no DI/no-mocking rules       |
| 3 | Atemporal voice       | REJECT | Context narrates code state                 |
| 4 | Mocking prohibition   | REJECT | "mock the execa calls at the boundary"      |
| 5 | Level accuracy        | PASS   | Level references are correct                |
| 6 | Anti-patterns         | REJECT | Level assignment table in Testing Strategy  |
| 7 | Ancestor consistency  | PASS   | Consistent with product ADRs                |

---

## Violations

### Mocking External Service

**Where:** Decision section, "mock the execa calls at the boundary"
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
**Why this fails:** The authoritative ADR template has no Testing Strategy section. Level assignments are a downstream concern for `/testing`. Testability constraints belong in the Compliance section as MUST/NEVER rules.

**Correct approach:**

```markdown
## Compliance

### MUST

- All external tool invocations accept a dependency-injected runner
  parameter -- enables `l1` testing of command logic ([review])

### NEVER

- Direct child_process.exec/spawn without DI wrapper -- prevents
  isolated testing ([review])
```

---

### Missing Testability in Compliance

**Where:** Compliance section
**Concern:** Testability in Compliance
**Why this fails:** The Compliance section has constraints for error handling and config validation but no MUST/NEVER rules for dependency injection or mocking prohibition. Removing the phantom Testing Strategy section is not enough -- the testability constraints must move here.

---

### Temporal Language in Context Section

**Where:** Context section, "The current BuildRunner class in build.ts shells out to Hugo directly without dependency injection, making `l1` testing impossible."
**Concern:** Atemporal voice
**Why this fails:** Narrates code state -- becomes false the moment the file changes. The ADR states what the architecture IS, not what code currently exists.

**Correct approach:**

```markdown
**Technical constraints:** Build orchestration depends on external binaries
(Hugo, Caddy). Dependency injection isolates build logic from tool invocation.
```

---

## Required Changes

1. Remove phantom "Testing Strategy" section entirely
2. Add MUST/NEVER testability rules to Compliance (DI, no mocking)
3. Replace "mock at boundary" with DI interface approach
4. Rewrite Context in atemporal voice -- no references to current code state

---

## References

- /standardizing-typescript-architecture: `<adr_sections>` (no Testing Strategy section)
- /standardizing-typescript-architecture: `<testability_in_compliance>` (MUST/NEVER pattern)
- /standardizing-typescript-architecture: `<atemporal_voice>` (temporal patterns)
- /standardizing-typescript-architecture: `<di_patterns>` (mocking prohibition)

---

Revise and resubmit.
