---
name: auditing-python-architecture
description: >-
  ALWAYS invoke this skill when auditing ADRs or architecture decisions.
  NEVER audit architecture decisions without this skill.
allowed-tools: Read, Grep
---

<objective>
Review ADRs against `/testing` principles, atemporal voice rules, and applicable PDR constraints. Reject any ADR that narrates code history, references existing files, or describes migration plans. Point out violations, reference the specific principle, and show correct architecture.
</objective>

<quick_start>

1. Read `/testing` for methodology (5 stages, 5 factors, 7 exceptions)
2. Check EVERY section for temporal language — reject any reference to current code, existing files, or migration plans
3. Identify violations of testing principles and parent PDR constraints
4. Output APPROVED or REJECTED with specific violations
5. Show correct approach with code examples

</quick_start>

<principles_to_enforce>
From `/testing`:

**Level definitions** (from Stage 2 Five Factors):

- **Level 1**: Pure computation, file I/O with temp dirs, standard dev tools (git, curl)
  - Test directly, no doubles needed
- **Level 2**: Real dependencies via harnesses (Docker, databases, project-specific binaries)
  - Use real systems, not fakes
- **Level 3**: Real credentials, external services, browsers
  - Full real-world workflows

**Critical rules** (from Five Factors):

- Standard dev tools (git, cat, grep, curl) are Level 1
- Project-specific tools (Docker, PostgreSQL, Hugo) are Level 2
- SaaS services (Trakt, GitHub API, Stripe, Auth0) jump from Level 1 → Level 3 (no Level 2)
- Network dependencies and external services are Level 3

**Mocking prohibition** (Cardinal Rule):

- **NO mocking. Ever.** - `/testing` cardinal rule
- NO `unittest.mock.patch` for external services
- NO `respx.mock` for internet APIs
- Use dependency injection with Protocol interfaces instead
- Test doubles (stubs, spies, fakes) only when exception case applies

**Reality principle**:

- "Reality is the oracle" - tests must verify behavior against real systems
- A fake proves your code works with your imagination, not the real system

**Test doubles require exception case** (Stage 5):

- Only 7 legitimate exceptions for test doubles
- Each use must document which exception applies
- No exception = no doubles, test at Level 2

**Atemporal voice prohibition** (Durable Map Rule):

- **ADRs state architectural truth. They NEVER narrate code history, current state, or migration plans.**
- This is a REJECTION-level violation in ANY section — Context, Decision, Rationale, Compliance, all of it. No section gets a pass.
- An ADR that references existing code ("The current X has...", "The file X does not exist") is temporal — it becomes stale the moment that code changes.
- Code that violates an ADR is discovered through code review and test coverage analysis against the ADR's invariants. The ADR itself never names files to delete, code to replace, or implementations to migrate away from.

**Temporal patterns to reject:**

- "The current `module.py` has..." — narrates code state
- "The file `deprecated/old.py` does not exist" — narrates filesystem state
- "We need to replace..." / "We need to migrate..." — narrates a plan, not a truth
- "Currently X uses..." — snapshot that expires
- "The existing implementation..." — references code, not architecture
- "After evaluating options..." — narrates decision history
- "X has accumulated without..." — narrates drift
- "Previously..." / "Before this..." — there is no before
- "Going forward..." / "In the future..." — there is only the product truth

**The rewrite pattern:**

- TEMPORAL: "The current MmRegs class in mm.py has a @process with bus protocol logic but uses imperative add_reg() calls and _raw()."
- ATEMPORAL: "Register banks use declarative field definitions. Bus protocol logic belongs in the Entity's tick() method, not in standalone @process decorators."

- TEMPORAL: "The file deprecated/file.py does not exist and should be removed."
- ATEMPORAL: "Register bank implementations conform to the Entity protocol." (Non-conforming code is found by code review, not by the ADR.)

- TEMPORAL: "We discovered that raw signal access causes timing violations."
- ATEMPORAL: "Raw signal access violates the two-phase simulation model. All signal writes use non-blocking assignment."

</principles_to_enforce>

<output_format>

````markdown
# ARCHITECTURE REVIEW

**Decision:** [APPROVED | REJECTED]

---

## Violations

### {Violation name}

**Where:** {Section name or quote identifying the location}
**Principle violated:** /testing {section name}
**Why this fails:** {Direct explanation}

**Correct approach:**

```{language}
{Show what the architecture should be}
```
````

---

{Repeat for each violation}

---

## Required Changes

{Concise list of what must change}

---

## References

- /testing: {section name} (principle violated)
- /standardizing-python-testing: {section if applicable}

---

{If REJECTED: "Revise and resubmit"}
{If APPROVED: "Architecture meets standards"}

````
</output_format>

<review_guidelines>

**Don't:**

- Reference specific line numbers (they change)
- Provide grep commands
- Explain multiple times
- Count statistics

**Do:**

- Reference `/testing` section names (e.g., "Stage 5 Exception 1", "Cardinal Rule")
- Show correct architecture with code examples
- Be direct about violations
- Reference `/standardizing-python-testing` for Python-specific patterns
- Reject temporal language in ANY section — Context, Decision, Rationale, Compliance
- Show the atemporal rewrite alongside each temporal violation

</review_guidelines>

<example_review>

```markdown
# ARCHITECTURE REVIEW

**Decision:** REJECTED

---

## Violations

### Level 2 Assigned to SaaS Service

**Where:** Lines 132-133
**Principle violated:** /testing Stage 2 Factor 2

Trakt.tv is a SaaS service that cannot run locally. Per /testing Five Factors:
- SaaS services have no Level 2 - jump from Level 1 to Level 3

**Correct approach:**

```markdown
| List operations | 1 | DI with TraktListProvider protocol |
| List operations | 3 | Real Trakt API with test account |
````

---

### Mocking External Services

**Where:** Lines 132, 133, 145
**Principle violated:** /testing Cardinal Rule

Testing Strategy says "Mock at the PyTrakt API boundary" - this violates the NO MOCKING principle.

**Correct approach:**

Use dependency injection per /standardizing-python-testing:

```python
class TraktListProvider(Protocol):
    def __call__(self, list_name: str, username: str) -> Any | None: ...


# Level 1: Inject fake implementation (Exception 1: Failure modes)
# Level 3: Use real PyTrakt
```

---

### Temporal Language in Context Section

**Where:** Context section
**Principle violated:** Atemporal voice (Durable Map Rule)

Context says "The current PyTrakt wrapper in trakt_client.py uses direct API calls without dependency injection, making it impossible to test at Level 1."

This narrates code state — it becomes false the moment the file changes. The ADR states what the architecture IS, not what code currently exists. Non-conforming code is discovered through code review against the ADR's invariants.

**Correct approach:**

```markdown
**Technical**: List operations depend on a SaaS API (Trakt.tv) that cannot
run locally. Dependency injection isolates business logic from API transport.
```

---

## Required Changes

1. Remove all Level 2 assignments for SaaS operations
2. Remove "Mock at boundary" language
3. Add DI protocol definitions per /standardizing-python-testing
4. Document which exception case justifies any test doubles
5. Rewrite Context section in atemporal voice — remove all references to current code state

---

## References

- /testing: Cardinal Rule (no mocking)
- /testing: Stage 2 Factor 2 (dependency levels)
- /testing: Stage 5 (exception cases for test doubles)
- /standardizing-python-testing: Protocol patterns

---

Revise and resubmit.

```
</example_review>

<success_criteria>
Review is complete when:

- [ ] Checked ALL sections for temporal language (Durable Map Rule) — Context, Decision, Rationale, Compliance
- [ ] Checked for mocking violations (Cardinal Rule)
- [ ] Verified level assignments match `/testing` Five Factors
- [ ] Checked test double usage has documented exception case
- [ ] Verified ADR never names files to delete or code to replace (code removal comes from code review, not ADRs)
- [ ] Output follows format with section references (not line numbers)
- [ ] Correct approach shown with code examples

</success_criteria>
```
