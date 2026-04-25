---
name: standardizing-python-architecture
user-invocable: false
description: >-
  Python ADR conventions enforced across architect and auditor skills.
  Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical ADR conventions for Python projects. Defines what sections an ADR has, how testability appears in Compliance rules, and Python-specific DI patterns using Protocols. Loaded by `/architecting-python` (to produce conformant ADRs) and `/auditing-python-architecture` (to validate them).
</objective>

<reference_note>
This is a reference skill. The architect and auditor load these conventions automatically. Invoke `/architecting-python` to write ADRs or `/auditing-python-architecture` to review them.
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

**When an ADR is required:** Every module that makes architectural decisions — module layout, library choice, DI patterns — requires an ADR. The absence of an ADR is itself a violation, not a reason to skip the audit.

</adr_sections>

<testability_in_compliance>

ADRs do not assign testing levels. They establish constraints that *make levels achievable*. The `/testing` skill assigns levels when it reads spec assertions alongside ADR constraints. This separation follows the truth hierarchy: ADR governs, spec declares, test verifies.

**The mechanism:** Compliance rules that mandate DI, prohibit mocking, and require observable Protocol interfaces.

**Correct pattern -- testability as MUST/NEVER:**

```markdown
## Compliance

### Recognized by

Observable Protocol parameters in all functions that invoke external tools or services.

### MUST

- All external tool invocations accept a dependency-injected runner parameter typed as a Protocol -- enables isolated testing without mocking ([review])
- Configuration accepts typed inputs via Pydantic models, not environment reads -- enables `l1` verification of config logic ([review])

### NEVER

- `unittest.mock.patch` for any dependency -- violates reality principle ([review])
- Direct `subprocess.run` without DI wrapper -- prevents isolated testing ([review])
```

**What this replaces -- the following does NOT belong in an ADR:**

```text
## Testing Strategy                    <-- NOT a valid ADR section

### Level Assignments                  <-- downstream concern for /testing

| Component        | Level        | Justification                          |
| ---------------- | ------------ | -------------------------------------- |
| Command building | `l1`         | Pure function, no external deps        |
| Tool invocation  | `l2`         | Needs real binary to verify acceptance |

### Escalation Rationale               <-- downstream concern for /testing

- `l1` -> `l2`: Real binary required for acceptance
```

**Why:** Level assignments depend on the spec's assertions, the project's infrastructure, and the `/testing` skill's Five Factors analysis. The ADR cannot know these at authoring time. The ADR's job is to establish constraints (DI, no mocking) that make the right levels *possible*.

</testability_in_compliance>

<atemporal_voice>

ADRs state architectural truth. They NEVER narrate code history, current state, or migration plans. This is a REJECTION-level violation in ANY section -- Context, Decision, Rationale, Compliance, all of it. No section gets a pass.

An ADR that references existing code ("The current X has...", "The file X does not exist") is temporal -- it becomes stale the moment that code changes. Code that violates an ADR is discovered through code review and test coverage analysis against the ADR's invariants.

**Temporal patterns to reject:**

- "The current `module.py` has..." -- narrates code state
- "The file `deprecated/old.py` does not exist" -- narrates filesystem state
- "We need to replace..." / "We need to migrate..." -- narrates a plan, not a truth
- "Currently X uses..." -- snapshot that expires
- "The existing implementation..." -- references code, not architecture
- "After evaluating options..." -- narrates decision history
- "X has accumulated without..." -- narrates drift
- "Previously..." / "Before this..." -- there is no before
- "Going forward..." / "In the future..." -- there is only the product truth

**The rewrite pattern:**

- TEMPORAL: "The current MmRegs class in mm.py has a @process with bus protocol logic but uses imperative add_reg() calls."
- ATEMPORAL: "Register banks use declarative field definitions. Bus protocol logic belongs in the Entity's tick() method."

- TEMPORAL: "The file deprecated/file.py does not exist and should be removed."
- ATEMPORAL: "Register bank implementations conform to the Entity protocol."

- TEMPORAL: "We discovered that raw signal access causes timing violations."
- ATEMPORAL: "Raw signal access violates the two-phase simulation model. All signal writes use non-blocking assignment."

</atemporal_voice>

<di_patterns>

When an ADR mandates dependency injection, these are the Python patterns to reference in Compliance rules.

**Protocol-based DI:**

```python
from typing import Protocol


# ADR Compliance: "MUST accept runner as parameter"
class CommandRunner(Protocol):
    def run(self, cmd: list[str]) -> tuple[int, str, str]: ...


# l1: inject controlled implementation
# l2/l3: inject real implementation
def sync_files(
    source: Path,
    dest: Path,
    runner: CommandRunner,
) -> SyncResult:
    returncode, stdout, stderr = runner.run(["rsync", str(source), str(dest)])
    return SyncResult(success=returncode == 0)
```

**ADR Compliance rule to code mapping:**

| ADR Compliance rule                  | Code implements                                     |
| ------------------------------------ | --------------------------------------------------- |
| "MUST accept runner as parameter"    | `def f(runner: CommandRunner)`                      |
| "MUST validate config at load time"  | Pydantic model with `.model_validate()` at boundary |
| "NEVER use unittest.mock.patch"      | No mock imports in test files                       |
| "NEVER shell out without DI wrapper" | No bare `subprocess.run()` calls                    |

**Mocking prohibition in ADR language:**

The auditor checks for these violations in ADR text:

- `unittest.mock.patch` or `respx.mock` mentioned as an approach -- reject
- "mock at boundary" or "mock the API calls" -- reject
- "stub" or "fake" without referencing a `/testing` exception case -- reject

Correct ADR language: "Use dependency injection to isolate X from Y" or "Accept X as a parameter implementing the Y Protocol."

</di_patterns>

<level_context>

The architect needs to understand testing levels to write effective Compliance rules. The auditor needs them to verify that Compliance rules enable the right levels. These definitions come from `/testing`.

| Level | Python infrastructure                                | When to use                           |
| ----- | ---------------------------------------------------- | ------------------------------------- |
| `l1`  | Python stdlib + Git + standard tools + temp fixtures | Pure logic, command building, parsing |
| `l2`  | Project-specific binaries/tools (Docker, ZFS, etc.)  | Real binaries with local backend      |
| `l3`  | Network services + external APIs + test accounts     | Real services, OAuth, rate limits     |

**Key rules:**

- Git is `l1` (standard dev tool, always available in CI)
- Project-specific tools require installation/setup (`l2`)
- Network dependencies and external services are `l3`
- SaaS services (Trakt, GitHub API, Stripe, Auth0) jump `l1` to `l3` (no `l2`)

**How levels relate to ADRs:** The ADR does not assign levels. It establishes Compliance rules that determine what levels are *achievable*. "MUST accept runner as Protocol parameter" makes `l1` possible for the logic around the tool. "NEVER call external API directly" means `l3` for the real call, `l1` for the business logic.

</level_context>

<anti_patterns>

| Anti-pattern                  | Why it is wrong                                | Where it belongs                      |
| ----------------------------- | ---------------------------------------------- | ------------------------------------- |
| `## Testing Strategy` section | Not in the authoritative ADR template          | `/testing` skill output               |
| Level assignment tables       | Downstream concern; depends on spec assertions | `/testing` Stage 2                    |
| Escalation rationale          | Downstream concern; depends on project infra   | `/testing` Stage 2                    |
| `## Status` field             | Not in the authoritative ADR template          | Git history / commit metadata         |
| File names to delete          | Temporal; becomes stale immediately            | Code review against ADR invariants    |
| Migration plans               | Temporal; narrates a transition                | Code review / work items              |
| Implementation code           | ADRs constrain implementation, not provide it  | `/coding-python`                      |
| Test references `([test])`    | ADRs are verified by architecture review       | Spec assertions only                  |
| `src.*` import examples       | Ambiguous convention                           | Use `product.*` / `product_testing.*` |

</anti_patterns>
