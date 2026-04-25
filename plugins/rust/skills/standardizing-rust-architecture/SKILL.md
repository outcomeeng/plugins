---
name: standardizing-rust-architecture
disable-model-invocation: true
description: Rust ADR conventions enforced across architect and auditor skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical ADR conventions for Rust projects, loaded after `/standardizing-rust`. Defines the allowed ADR sections, how Rust testability appears in Compliance rules, which dependency-injection patterns are acceptable, and which architectural claims belong in ADRs versus downstream testing work.
</objective>

<success_criteria>
Rust ADR guidance follows this standard when `/standardizing-rust` is loaded first, ADRs use only the authoritative sections, testability constraints live in Compliance, dependency seams are expressed in Rust terms, and test-level references match `/standardizing-rust-tests`.
</success_criteria>

<reference_note>
This is a reference skill. The architect and auditor load these conventions automatically. Invoke `/architecting-rust` to write ADRs or `/auditing-rust-architecture` to review them.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/rust-architecture.md` at the repository root. Read that file after this reference if it exists and apply it as the repo-local specialization.

When evaluating test-level references in ADRs, also check for `spx/local/rust-tests.md` and apply any repo-local test-level restrictions.
</repo_local_overlay>

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

**When an ADR is required:** Every module or boundary that makes architectural decisions -- module layout, trait seams, library choice, async runtime, DI patterns, persistence boundaries, unsafe boundaries -- requires an ADR. Missing ADRs are violations.

</adr_sections>

<testability_in_compliance>

ADRs do not assign testing levels. They establish constraints that make levels achievable. The `/testing` router and `/testing-rust` decide how assertions are verified once they combine spec assertions, architecture constraints, and project infrastructure.

**The mechanism:** Compliance rules that mandate observable seams, explicit ownership and boundary types, DI, and the absence of mocking frameworks.

**Correct pattern -- testability as MUST/NEVER:**

```markdown
Compliance

Recognized by

Observable dependency parameters in all functions that invoke external tools.

MUST

- External tool invocations accept an injected runner trait or function parameter -- enables isolated testing without framework mocks ([review])
- Configuration is parsed into typed structs at load time -- enables Level 1 verification of config logic ([review])

NEVER

- `mockall`, `faux`, or generated mocks as the primary testing strategy for architectural seams -- violates reality-based testing ([review])
- Direct `std::process::Command` construction in domain logic without an injected seam -- prevents isolated testing ([review])
```

**What this replaces -- the following does NOT belong in an ADR:**

```text
Testing Strategy

Level Assignments

| Component        | Level | Justification                   |
| ---------------- | ----- | ------------------------------- |
| Command building | 1     | Pure function, no external deps |
| CLI execution    | 2     | Needs real binary               |

Escalation Rationale

- Level 1->2: binary required for acceptance
```

**Why:** Level assignments depend on spec assertions, local tooling, and the `/testing` analysis flow. The ADR cannot know those details at authoring time. The ADR's job is to establish constraints that make the right tests possible.

</testability_in_compliance>

<atemporal_voice>

ADRs state architectural truth. They never narrate code history, current implementation snapshots, or migration plans. This is a rejection-level violation in any section.

An ADR that references current code ("The current module uses X", "The file Y does not exist") becomes stale when the code changes. Code that violates an ADR is discovered later through code review and test evidence.

**Temporal patterns to reject:**

- "The current `parser.rs` uses..." -- narrates code state
- "The file `legacy/mod.rs` does not exist" -- narrates filesystem state
- "We need to replace..." / "We need to migrate..." -- narrates a plan
- "Currently X uses..." -- snapshot that expires
- "The existing implementation..." -- references code, not architecture
- "After evaluating options..." -- narrates decision history
- "Previously..." / "Before this..." -- there is no before
- "Going forward..." / "In the future..." -- there is only product truth

**The rewrite pattern:**

- TEMPORAL: "The current command runner in `cli.rs` constructs `Command` directly."
- ATEMPORAL: "Command orchestration accepts an injected runner seam."

- TEMPORAL: "We discovered that direct process calls make testing impossible."
- ATEMPORAL: "Direct process invocation prevents isolated testing. Injected runner seams enable unit verification."

- TEMPORAL: "The existing async handler holds a mutex across await."
- ATEMPORAL: "Async request paths release locks before await points."

</atemporal_voice>

<di_patterns>

When an ADR mandates dependency injection, these are acceptable Rust patterns to reference in Compliance rules.

**Trait-based DI:**

```rust
pub trait CommandRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, CommandError>;
}

pub fn build_site<R: CommandRunner>(
    config: &BuildConfig,
    runner: &R,
) -> Result<BuildResult, BuildError> {
    runner.run("hugo", &["--destination", config.output_dir.as_str()])?;
    Ok(BuildResult::success())
}
```

**Function-based DI:**

```rust
pub fn sync_repo<F>(
    source: &Path,
    destination: &str,
    run: F,
) -> Result<SyncResult, SyncError>
where
    F: Fn(&str, &[&str]) -> Result<CommandOutput, CommandError>,
{
    run("git", &["fetch"])?;
    Ok(SyncResult::success())
}
```

**ADR Compliance rule to code mapping:**

| ADR Compliance rule                  | Code implements                                            |
| ------------------------------------ | ---------------------------------------------------------- |
| "MUST accept runner as parameter"    | `fn f<R: Runner>(deps: &R)` or `fn f(run: impl Fn(...))`   |
| "MUST validate config at load time"  | `serde` + typed structs + constructor/`TryFrom` validation |
| "NEVER use mock frameworks"          | hand-written trait impls or recorder structs in tests      |
| "NEVER shell out without DI wrapper" | no bare `std::process::Command` in core logic              |

**Mocking prohibition in ADR language:**

The auditor checks for these violations in ADR text:

- `mockall`, `faux`, "auto-generated mocks", or "mock the boundary" described as the intended testing strategy
- spying on the function under test rather than exercising it through a real seam
- generated doubles where a small controlled implementation would preserve coupling

Correct ADR language: "Use dependency injection to isolate X from Y" or "Accept X as a parameter implementing trait Y."

</di_patterns>

<level_context>

The architect needs enough testing context to write effective Compliance rules. The auditor uses the same context to check whether those rules actually enable the right tests.

| Level | Name        | Rust Infrastructure                                     | When to Use                                             |
| ----- | ----------- | ------------------------------------------------------- | ------------------------------------------------------- |
| 1     | Unit        | Rust stdlib, `cargo test`, temp dirs, git               | Pure logic, parsing, validation, command building       |
| 2     | Integration | workspace binaries, local services, Docker, databases   | Real CLI binaries, real DB adapters, local worker flows |
| 3     | E2E         | external network, SaaS APIs, browsers, deployed systems | Full workflows with remote systems or browser UI        |

**Key rules:**

- Git, filesystem, tempdirs, and standard Rust tooling are Level 1
- Real workspace binaries, codegen tools, and local services that require setup are Level 2
- External APIs, SaaS systems, browsers, and deployed environments are Level 3
- Project overlays, especially `spx/local/rust-tests.md`, may disable Level 3 when the suite cannot safely stand up, isolate, or clean up the external collaborator

**How levels relate to ADRs:** The ADR does not assign levels. It establishes constraints that determine what levels are achievable. "MUST accept a runner as parameter" makes Level 1 possible for command-building logic. "NEVER call external APIs from domain logic" preserves Level 1 for the domain and pushes the real remote boundary to Level 3 or to a repo-specific product decision.

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
| Implementation code           | ADRs constrain implementation, not provide it  | `/coding-rust`                     |
| Test references `([test])`    | ADRs are verified by architecture review       | Spec assertions only               |

</anti_patterns>
