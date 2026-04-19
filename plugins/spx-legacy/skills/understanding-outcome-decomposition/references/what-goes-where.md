# What Goes Where

A clear taxonomy of what content belongs in ADRs, PDRs, Specs, and Tests.

## The Four Types

| Type     | Purpose                     | Verified by (skill pattern)          |
| -------- | --------------------------- | ------------------------------------ |
| **ADR**  | GOVERNS how (architecture)  | `/reviewing-{language}-architecture` |
| **PDR**  | GOVERNS what (product)      | Product/UX review                    |
| **Spec** | DESCRIBES what should exist | `/reviewing-{language}`              |
| **Test** | PROVES it exists            | `/reviewing-{language}-tests`        |

*Replace `{language}` with actual language: `python`, `typescript`, etc.*

---

## ADRs (Decisions) — GOVERN

ADRs say "when you do X, do it THIS way." They constrain implementation.

### ADR Content

| Section      | Content                                  | Verified by                          |
| ------------ | ---------------------------------------- | ------------------------------------ |
| Purpose      | What architectural concern this governs  | `/reviewing-{language}-architecture` |
| Options      | Alternatives considered with trade-offs  | `/reviewing-{language}-architecture` |
| Decision     | What we chose and why                    | `/reviewing-{language}-architecture` |
| Consequences | Trade-offs accepted, constraints imposed | `/reviewing-{language}-architecture` |

### ADRs Do NOT Contain

| ❌ Never in ADR     | Why not                               | Where it belongs  |
| ------------------- | ------------------------------------- | ----------------- |
| Outcomes            | ADRs don't describe states to achieve | Spec              |
| Test files          | ADRs don't get tested                 | Spec's test table |
| Implementation code | ADRs govern, don't implement          | Story's Analysis  |
| Work to be done     | ADRs create no work                   | Spec outcomes     |

### ADR Verification

```
/reviewing-{language}-architecture checks ADR STRUCTURE:
□ Purpose states what this decision governs (atemporal voice)
□ Options were genuinely considered (not just "we picked X")
□ Decision states what was chosen and why
□ Consequences acknowledge trade-offs
□ No implementation details leaked in (ADRs GOVERN, don't implement)
□ Constraints are clear and enforceable

/reviewing-{language} checks ADR COMPLIANCE:
□ Code follows constraints from applicable ADRs
□ Deviations are documented or ADR is updated
```

---

## PDRs (Product Decisions) — GOVERN BEHAVIOR

PDRs say "the product behaves THIS way." They constrain product behavior, not code architecture.

### PDR Content

| Section            | Content                                | Verified by       |
| ------------------ | -------------------------------------- | ----------------- |
| Purpose            | What product behavior this governs     | Product/UX review |
| Decision           | What product behavior was chosen       | Product/UX review |
| Product Invariants | Observable behaviors users can rely on | Product/UX review |
| Compliance         | How to verify product behavior         | Product/UX review |

### PDRs Do NOT Contain

| ❌ Never in PDR     | Why not                        | Where it belongs |
| ------------------- | ------------------------------ | ---------------- |
| Code architecture   | PDRs govern product, not code  | ADR              |
| Implementation code | PDRs govern, don't implement   | Story's Analysis |
| Test files          | PDRs don't get tested directly | Spec's tests     |

### ADR vs PDR

| Aspect     | ADR                       | PDR                        |
| ---------- | ------------------------- | -------------------------- |
| Governs    | Code architecture         | Product behavior           |
| Example    | "Use PostgreSQL"          | "Simulation has 3 phases"  |
| Invariants | Algebraic code properties | Observable user guarantees |
| Verified   | Code review               | Product validation         |

---

## Specs (Containers) — DESCRIBE OUTCOMES

Specs define states that should exist. Each level has specific content.

### Spec Content by Level

| Section                   | Capability | Feature | Story | Nature       | Verified by             |
| ------------------------- | :--------: | :-----: | :---: | ------------ | ----------------------- |
| Purpose                   |     ✓      |    ✓    |   ✓   | Contract     | `/reviewing-{language}` |
| Success Metric            |     ✓      |    —    |   —   | Contract     | `/reviewing-{language}` |
| Requirements              |     ✓      |    ✓    |   —   | Contract     | `/reviewing-{language}` |
| Test Strategy             |     ✓      |    ✓    |   —   | Contract     | `/reviewing-{language}` |
| Outcomes (structured)     |     ✓      |    ✓    |   ✓   | Contract     | `/reviewing-{language}` |
| Test File Table           |     ✓      |    ✓    |   ✓   | **Contract** | `/reviewing-{language}` |
| Analysis                  |     —      |    —    |   ✓   | **Context**  | `/reviewing-{language}` |
| Architectural Constraints |     ✓      |    ✓    |   ✓   | Contract     | `/reviewing-{language}` |

**Contract vs. Context:**

- **Contract** sections are durable truth. References must resolve. Stale links = defect.
- **Context** sections document Claude's examination. References may diverge as understanding deepens — this is expected, not a defect.

### Outcome Scoping

| Container  | Outcomes describe...                   | Example                                                                                                                           | Verified by             |
| ---------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| Capability | Complete user journeys                 | "User authenticates and accesses dashboard" (Scenario)                                                                            | `/reviewing-{language}` |
| Feature    | Integration (stories working together) | "Master-slave loopback works" (Scenario)                                                                                          | `/reviewing-{language}` |
| Story      | Atomic behavior                        | "SPI master transmits in mode 0" (Scenario), "All IR types → valid Verilog" (Mapping), "Arithmetic always returns int" (Property) | `/reviewing-{language}` |

### The Integration Test

To determine if an outcome belongs in Feature vs Story:

```
Q: Can this outcome be verified without other stories in this feature?

YES → Story outcome (atomic)
NO  → Feature outcome (integration)
```

### Quality Gates

Quality gates are typically **Feature outcomes** because they verify combined output:

| Quality Gate           | Why Feature-level                    |
| ---------------------- | ------------------------------------ |
| "Lint-clean HDL"       | Verifies all generated code together |
| "All APIs documented"  | Verifies combined API surface        |
| "No security warnings" | Verifies integrated system           |

### Spec Verification

```
/reviewing-{language} checks:
□ Outcomes are states, not tasks
□ Outcome type matches quantifier intent (Scenario for ∃, Mapping for finite ∀, Property for infinite ∀)
□ Outcome notation is specific and testable
□ Test file references resolve to actual files (contract — stale links = defect)
□ Story outcomes are atomic
□ Feature outcomes require integration
□ Analysis section proves examination (context — references may diverge, stories only)
```

---

## Tests — PROVE

Tests are executable proof that outcomes exist.

### Test Organization

| Aspect             | Value                  | Verified by                   |
| ------------------ | ---------------------- | ----------------------------- |
| Location           | `<container>/tests/`   | `/reviewing-{language}-tests` |
| Unit naming        | `*.unit.test.*`        | `/reviewing-{language}-tests` |
| Integration naming | `*.integration.test.*` | `/reviewing-{language}-tests` |
| E2E naming         | `*.e2e.test.*`         | `/reviewing-{language}-tests` |

### Test Level vs Container Level

**These are ORTHOGONAL concepts.**

| Test Level | Infrastructure needed     | Can be used by...             |
| ---------- | ------------------------- | ----------------------------- |
| 1          | None (DI, temp dirs)      | Story, Feature, OR Capability |
| 2          | Real binaries/DB          | Story, Feature, OR Capability |
| 3          | Real services/credentials | Story, Feature, OR Capability |

A **Story** CAN have Level 2 tests (if it needs real binaries).
A **Capability** CAN have Level 1 tests (for pure logic verification).

### Test Verification

```
/reviewing-{language}-tests checks:
□ Tests prove outcomes from spec
□ Test level matches infrastructure needs
□ No mocking (DI instead)
□ Tests are co-located with spec
□ Naming convention followed
```

---

## The Flow

```
┌─────────────────────────────────────────┐
│                  ADR                     │
│         "When you do X, do it           │
│              THIS way"                   │
│                                         │
│  Verified by: /reviewing-{lang}-arch    │
└────────────────┬────────────────────────┘
                 │ constrains HOW
                 ▼
┌─────────────────────────────────────────┐
│                 SPEC                     │
│       "This state should exist"          │
│       (structured outcomes)              │
│                                         │
│  Verified by: /reviewing-{lang}         │
└────────────────┬────────────────────────┘
                 │ defines WHAT
                 ▼
┌─────────────────────────────────────────┐
│                 TEST                     │
│        "Here's proof it exists"          │
│                                         │
│  Verified by: /reviewing-{lang}-tests   │
└─────────────────────────────────────────┘
```

---

## Quick Reference

| I want to...                      | Put it in...     | Verified by                          |
| --------------------------------- | ---------------- | ------------------------------------ |
| Constrain implementation approach | ADR              | `/reviewing-{language}-architecture` |
| Define a state that should exist  | Spec outcome     | `/reviewing-{language}`              |
| Prove an outcome exists           | Test             | `/reviewing-{language}-tests`        |
| Document trade-offs               | ADR Consequences | `/reviewing-{language}-architecture` |
| Show I examined the codebase      | Story Analysis   | `/reviewing-{language}`              |
| Gate on combined quality          | Feature outcome  | `/reviewing-{language}`              |
