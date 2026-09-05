---
name: go-architecture-standards
user-invocable: false
description: >-
  Go ADR conventions enforced across architect and auditor skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The canonical Go ADR conventions — allowed sections, how Go testability appears in Verification rules, acceptable dependency-injection patterns, and which architectural claims belong in ADRs versus downstream testing.
</objective>

<success_criteria>
Go ADR guidance follows this standard when `/go-standards` is loaded first, ADRs use only the authoritative sections, testability constraints live in `## Verification`'s `### Audit` subsection, dependency seams are expressed in Go terms, and test-level references match `/go-test-standards`.
</success_criteria>

<reference_note>
This is a reference skill. Composing Go architecture skills load these conventions explicitly before authoring or auditing ADRs. It is not a standalone workflow.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/go-architecture.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions.

When evaluating test-level references in ADRs, also check for `spx/local/go-tests.md` and apply any repo-local routing to governing test-level specs or decisions.

A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<adr_sections>

The ADR template (from `/understand`) is decision-first — the decision is stated directly under the title, with no `Purpose` heading and no preamble:

1. **Title + decision** -- `# {Decision Name}`, then the decision stated directly as permanent truth in 1-3 sentences: what it governs and what it decides.
2. **Rationale** -- Why this is right given the constraints. Name a rejected alternative only when it sharpens the decision. Omit if self-evident.
3. **Invariants** (optional) -- Algebraic properties that hold for ALL governed code. Omit if none apply.
4. **Verification** -- Each rule is an ALWAYS guarantee or a NEVER boundary, grouped under the one subsection naming how it is verified: `### Testing` (deterministic test, `([{assertion type}])`), `### Eval` (graded LLM behavior, `([eval])`), `### Audit` (agent judgment, `([audit])`), ordered by decreasing enforcement strength. Include only the subsections that apply.

**This is the complete list.** An ADR has no other sections. There is no `Purpose` heading, no `Context` section, no `Trade-offs` section, no `Testing Strategy` section, no `Status` field, no `Level Assignments` table — business context and trade-offs fold into the decision statement and Rationale. Go architecture rules — DI mandates, mocking prohibitions, goroutine ownership, `unsafe` boundaries — require agent judgment, so they live under `### Audit` with `([audit])`.

**When an ADR is required:** Every package or boundary that makes architectural decisions -- package layout, interface seams, module choice, concurrency model, DI patterns, persistence boundaries, `unsafe` or cgo boundaries -- requires an ADR. Missing ADRs are violations.

</adr_sections>

<testability_in_verification>

ADRs do not assign testing levels. They establish constraints that make levels achievable. The `/test` router and `/test-go` decide how assertions are verified once they combine spec assertions, architecture constraints, and product infrastructure.

**The mechanism:** Verification rules under `### Audit` that mandate observable seams, explicit package and boundary types, DI, and the absence of mocking frameworks.

**Correct pattern -- testability as ALWAYS/NEVER under `### Audit`:**

```markdown
## Verification

### Audit

- ALWAYS: external tool invocations accept an injected runner interface or function parameter -- enables isolated testing without generated mocks ([audit])
- ALWAYS: configuration is parsed into typed structs at load time -- enables Level 1 verification of config logic ([audit])
- NEVER: `gomock`, `mockery`, or generated mocks as the primary testing strategy for architectural seams -- violates reality-based testing ([audit])
- NEVER: direct `os/exec` construction in domain logic without an injected seam -- prevents isolated testing ([audit])
```

**What this replaces -- the following does NOT belong in an ADR:**

```text
Testing Strategy

Level Assignments

| Component        | Level | Justification                   |
| ---------------- | ----- | ------------------------------- |
| Command building | 1     | Pure function, no external deps |
| Installed CLI    | 2     | Needs the released binary       |

Escalation Rationale

- Level 1->2: released binary required for acceptance
```

**Why:** Level assignments depend on spec assertions, local tooling, and the `/test` analysis flow. The ADR cannot know those details at authoring time. The ADR's job is to establish constraints that make the right tests possible.

</testability_in_verification>

<atemporal_voice>

ADRs state architectural truth. They never narrate code history, current implementation snapshots, or migration plans. This is a rejection-level violation in any section.

An ADR that references current code ("The current package uses X", "The file Y does not exist") becomes stale when the code changes. Code that violates an ADR is discovered later through code review and test evidence.

**Temporal patterns to reject:**

- "The current `parser.go` uses..." -- narrates code state
- "The file `legacy/handler.go` does not exist" -- narrates filesystem state
- "We need to replace..." / "We need to migrate..." -- narrates a plan
- "Currently X uses..." -- snapshot that expires
- "The existing implementation..." -- references code, not architecture
- "After evaluating options..." -- narrates decision history
- "Previously..." / "Before this..." -- there is no before
- "Going forward..." / "In the future..." -- there is only product truth

**The rewrite pattern:**

- TEMPORAL: "The current command runner in `cli.go` calls `exec.Command` directly."
- ATEMPORAL: "Command orchestration accepts an injected runner seam."

- TEMPORAL: "We discovered that direct process calls make testing impossible."
- ATEMPORAL: "Direct process invocation prevents isolated testing. Injected runner seams enable L1 verification."

- TEMPORAL: "The existing handler holds the mutex across the database call."
- ATEMPORAL: "Request paths release locks before any blocking call."

</atemporal_voice>

<di_patterns>

When an ADR mandates dependency injection, these are acceptable Go patterns to reference in `## Verification` `### Audit` rules.

**Interface-based DI:**

```go
type CommandRunner interface {
    Run(ctx context.Context, program string, args ...string) (CommandOutput, error)
}

func BuildSite(ctx context.Context, cfg *BuildConfig, runner CommandRunner) (BuildResult, error) {
    if _, err := runner.Run(ctx, "hugo", "--destination", cfg.OutputDir); err != nil {
        return BuildResult{}, fmt.Errorf("build site: %w", err)
    }
    return BuildResult{Success: true}, nil
}
```

**Function-based DI:**

```go
type RunFunc func(ctx context.Context, program string, args ...string) (CommandOutput, error)

func SyncRepo(ctx context.Context, source, destination string, run RunFunc) (SyncResult, error) {
    if _, err := run(ctx, "git", "fetch"); err != nil {
        return SyncResult{}, fmt.Errorf("sync repo: %w", err)
    }
    return SyncResult{Success: true}, nil
}
```

**ADR Compliance rule to code mapping:**

| ADR Verification rule                 | Code implements                                                     |
| ------------------------------------- | ------------------------------------------------------------------- |
| "ALWAYS accept runner as parameter"   | `func f(ctx, deps Runner)` or `func f(ctx, run RunFunc)`            |
| "ALWAYS validate config at load time" | `encoding/json` + raw struct + parse function into a typed struct   |
| "NEVER use mock frameworks"           | hand-written interface implementations or recorder structs in tests |
| "NEVER shell out without DI wrapper"  | no bare `exec.Command` in core logic                                |

**Mocking prohibition in ADR language:**

The auditor checks for these violations in ADR text:

- `gomock`, `mockery`, `moq`, "auto-generated mocks", or "mock the boundary" described as the intended testing strategy
- monkey-patching a package-level function variable to spy on the function under test rather than exercising it through a real seam
- generated doubles where a small controlled implementation would preserve coupling

Correct ADR language: "Use dependency injection to isolate X from Y" or "Accept X as a parameter implementing interface Y."

</di_patterns>

<level_context>

The architect needs enough testing context to write effective Verification rules. The auditor uses the same context to check whether those rules actually enable the right tests.

| Level | Name        | Go Infrastructure                                                 | When to Use                                                     |
| ----- | ----------- | ----------------------------------------------------------------- | --------------------------------------------------------------- |
| 1     | Unit        | Go stdlib, `go test`, `t.TempDir()`, git, a binary built in-cycle | Pure logic, parsing, validation, command building, in-cycle CLI |
| 2     | Integration | local services, containers, databases, an installed binary        | Real DB adapters, local worker flows, released CLI              |
| 3     | E2E         | external network, SaaS APIs, browsers, deployed systems           | Full workflows with remote systems or browser UI                |

**Key rules:**

- Git, filesystem, `t.TempDir()`, the toolchain, and a product binary the harness builds in-cycle are Level 1
- Local services, containers, and an installed or downloaded binary are Level 2
- External APIs, SaaS systems, browsers, and deployed environments are Level 3
- Product specs or decisions may disable Level 3 when the suite cannot safely stand up, isolate, or clean up the external collaborator; `spx/local/go-tests.md` may point the skill to that declaration

**How levels relate to ADRs:** The ADR does not assign levels. It establishes constraints that determine what levels are achievable. "ALWAYS accept a runner as parameter" makes Level 1 possible for command-building logic. "NEVER call external APIs from domain logic" preserves Level 1 for the domain and pushes the real remote boundary to Level 3 or to a repo-specific product decision.

</level_context>

<anti_patterns>

| Anti-pattern                  | Why it is wrong                                | Where it belongs                   |
| ----------------------------- | ---------------------------------------------- | ---------------------------------- |
| `## Testing Strategy` section | Not in the authoritative ADR template          | `/test` skill output               |
| Level assignment tables       | Downstream concern; depends on spec assertions | `/test` Stage 2                    |
| Escalation rationale          | Downstream concern; depends on product infra   | `/test` Stage 2                    |
| `## Status` field             | Not in the authoritative ADR template          | Git history / commit metadata      |
| File names to delete          | Temporal; becomes stale immediately            | Code review against ADR invariants |
| Migration plans               | Temporal; narrates a transition                | Code review / work items           |
| Implementation code           | ADRs constrain implementation, not provide it  | `/code-go`                         |

</anti_patterns>
