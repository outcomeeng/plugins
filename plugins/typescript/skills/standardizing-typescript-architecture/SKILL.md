---
name: standardizing-typescript-architecture
disable-model-invocation: true
description: >-
  TypeScript ADR conventions enforced across architect and auditor skills.
  Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical ADR conventions for TypeScript projects. Defines what sections an ADR has, how testability appears in Compliance rules, and TypeScript-specific DI patterns. Loaded by `/architecting-typescript` (to produce conformant ADRs) and `/auditing-typescript-architecture` (to validate them).
</objective>

<reference_note>
This is a reference skill. The architect and auditor load these conventions automatically. Invoke `/architecting-typescript` to write ADRs or `/auditing-typescript-architecture` to review them.
</reference_note>

<adr_sections>

The ADR template (from `/understanding`) defines exactly these sections:

1. **Purpose** -- What concern this decision governs. State as permanent truth.
2. **Context** -- Business impact and technical constraints.
3. **Decision** -- Primary decision in one sentence.
4. **Rationale** -- Why this is right given the constraints. Alternatives considered and rejected.
5. **Trade-offs accepted** -- Table: what is given up, why it is acceptable or mitigated.
6. **Invariants** (optional) -- Algebraic properties that hold for ALL governed code. Omit if none apply.
7. **Compliance** -- Observable patterns (Recognized by), rules (MUST), prohibitions (NEVER).

**This is the complete list.** An ADR has no other sections. There is no "Testing Strategy" section, no "Status" field, no "Level Assignments" table. Testability constraints live in Compliance as MUST/NEVER rules.

</adr_sections>

<testability_in_compliance>

ADRs do not assign testing levels. They establish constraints that *make levels achievable*. The `/testing` skill assigns levels when it reads spec assertions alongside ADR constraints. This separation follows the truth hierarchy: ADR governs, spec declares, test verifies.

**The mechanism:** Compliance rules that mandate DI, prohibit mocking, and require observable interfaces.

**Correct pattern -- testability as MUST/NEVER:**

```markdown
## Compliance

### Recognized by

Observable DI parameters in all functions that invoke external tools.

### MUST

- All external tool invocations accept a dependency-injected runner parameter -- enables isolated testing without mocking ([review])
- Configuration accepts typed inputs, not environment reads -- enables Level 1 verification of config logic ([review])

### NEVER

- `vi.mock()` or `jest.mock()` for any dependency -- violates reality principle ([review])
- Direct `child_process.exec/spawn` without DI wrapper -- prevents isolated testing ([review])
```

**What this replaces -- the following does NOT belong in an ADR:**

```text
## Testing Strategy                    <-- NOT a valid ADR section

### Level Assignments                  <-- downstream concern for /testing

| Component        | Level | Justification                   |
| ---------------- | ----- | ------------------------------- |
| Command building | 1     | Pure function, no external deps |
| Hugo invocation  | 2     | Needs real Hugo binary          |

### Escalation Rationale               <-- downstream concern for /testing

- Level 1->2: Hugo binary required for acceptance
```

**Why:** Level assignments depend on the spec's assertions, the project's infrastructure, and the `/testing` skill's Five Factors analysis. The ADR cannot know these at authoring time. The ADR's job is to establish constraints (DI, no mocking) that make the right levels *possible*.

</testability_in_compliance>

<atemporal_voice>

ADRs state architectural truth. They NEVER narrate code history, current state, or migration plans. This is a REJECTION-level violation in ANY section -- Context, Decision, Rationale, Compliance, all of it. No section gets a pass.

An ADR that references existing code ("The current X has...", "The file X does not exist") is temporal -- it becomes stale the moment that code changes. Code that violates an ADR is discovered through code review and test coverage analysis against the ADR's invariants.

**Temporal patterns to reject:**

- "The current `module.ts` has..." -- narrates code state
- "The file `deprecated/old.ts` does not exist" -- narrates filesystem state
- "We need to replace..." / "We need to migrate..." -- narrates a plan, not a truth
- "Currently X uses..." -- snapshot that expires
- "The existing implementation..." -- references code, not architecture
- "After evaluating options..." -- narrates decision history
- "X has accumulated without..." -- narrates drift
- "Previously..." / "Before this..." -- there is no before
- "Going forward..." / "In the future..." -- there is only the product truth

**The rewrite pattern:**

- TEMPORAL: "The current BuildRunner class in build.ts shells out to Hugo directly without dependency injection."
- ATEMPORAL: "Build orchestration uses dependency injection to isolate tool invocation from build logic."

- TEMPORAL: "The file legacy/builder.ts does not exist and should be removed."
- ATEMPORAL: "Build implementations conform to the BuildDependencies interface."

- TEMPORAL: "We discovered that direct execa calls make testing impossible."
- ATEMPORAL: "Direct process invocation prevents Level 1 testing. Dependency injection enables isolated unit verification."

</atemporal_voice>

<di_patterns>

When an ADR mandates dependency injection, these are the TypeScript patterns to reference in Compliance rules.

**Interface-based DI:**

```typescript
// ADR Compliance: "MUST accept runner as parameter"
interface BuildDependencies {
  run: (cmd: string[], opts?: ExecOptions) => Promise<ExecResult>;
  resolveVersion: (tool: string) => Promise<string>;
}

// Level 1: inject controlled implementation
// Level 2+: inject real implementation
function buildSite(
  config: BuildConfig,
  deps: BuildDependencies,
): Promise<BuildResult> {
  // ...
}
```

**ADR Compliance rule to code mapping:**

| ADR Compliance rule                  | Code implements                        |
| ------------------------------------ | -------------------------------------- |
| "MUST accept runner as parameter"    | `function f(deps: RunnerDeps)`         |
| "MUST validate config at load time"  | Zod schema with `.parse()` at boundary |
| "NEVER use vi.mock()"                | No mock imports in test files          |
| "NEVER shell out without DI wrapper" | No bare `exec()` / `spawn()` calls     |

**Mocking prohibition in ADR language:**

The auditor checks for these violations in ADR text:

- `vi.mock()` or `jest.mock()` mentioned as an approach -- reject
- "mock at boundary" or "mock the X calls" -- reject
- "stub" or "fake" without referencing a `/testing` exception case -- reject

Correct ADR language: "Use dependency injection to isolate X from Y" or "Accept X as a parameter implementing the Y interface."

</di_patterns>

<level_context>

The architect needs to understand testing levels to write effective Compliance rules. The auditor needs them to verify that Compliance rules enable the right levels. These definitions come from `/testing`.

| Level | Name        | TypeScript Infrastructure               | When to Use                                   |
| ----- | ----------- | --------------------------------------- | --------------------------------------------- |
| 1     | Unit        | Node.js built-ins + Git + temp fixtures | Pure logic, FS operations, git operations     |
| 2     | Integration | Project-specific binaries/tools         | Hugo, Caddy, Claude Code, Docker, TS compiler |
| 3     | E2E         | External deps (GitHub, network, Chrome) | Full workflows with external services         |

**Key rules:**

- Git is Level 1 (standard dev tool, always available in CI)
- Project-specific tools require installation/setup (Level 2)
- Network dependencies and external services are Level 3
- SaaS services jump L1 to L3 (no Level 2)

**How levels relate to ADRs:** The ADR does not assign levels. It establishes Compliance rules that determine what levels are *achievable*. "MUST accept runner as parameter" makes Level 1 possible for the logic around the tool. "NEVER call external API directly" means Level 3 for the real call, Level 1 for the business logic.

</level_context>

<anti_patterns>

| Anti-pattern                  | Why it is wrong                                | Where it belongs                   |
| ----------------------------- | ---------------------------------------------- | ---------------------------------- |
| `## Testing Strategy` section | Not in the authoritative ADR template          | `/testing` skill output            |
| Level assignment tables       | Downstream concern; depends on spec assertions | `/testing` Stage 2                 |
| Escalation rationale          | Downstream concern; depends on project infra   | `/testing` Stage 2                 |
| `## Status` field             | Not in the authoritative ADR template          | Git history / commit metadata      |
| File names to delete          | Temporal; becomes stale immediately            | Code review against ADR invariants |
| Migration plans               | Temporal; narrates a transition                | Code review / work items           |
| Implementation code           | ADRs constrain implementation, not provide it  | `/coding-typescript`               |
| Test references `([test])`    | ADRs are verified by architecture review       | Spec assertions only               |

</anti_patterns>
