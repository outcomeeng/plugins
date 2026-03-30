---
name: auditing-typescript-architecture
description: >-
  ALWAYS invoke this skill when auditing ADRs or architecture decisions.
  NEVER audit architecture decisions without this skill.
allowed-tools: Read, Grep
---

<objective>
Review ADRs against testing principles, atemporal voice rules, and applicable PDR constraints. Reject any ADR that narrates code history, references existing files, or describes migration plans. Point out violations, reference the specific principle, and show correct architecture.
</objective>

<context_loading>
**For spec-tree work items: Load complete ADR/PDR hierarchy before reviewing.**

If you're reviewing ADRs for a spec-tree work item (enabler/outcome), ensure complete architectural context is loaded:

1. **Invoke `spec-tree:contextualizing`** with the node path
2. **Verify all ancestor ADRs/PDRs are loaded** - Must check for consistency with decision hierarchy
3. **Verify ADR references ancestor decisions** - Node ADRs should reference relevant ancestor ADRs/PDRs

**The `spec-tree:contextualizing` skill provides:**

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- TRD with technical requirements
- Target node spec with typed assertions

**Review focus:**

- Does ADR contradict any ancestor ADR/PDR decisions?
- Does ADR include testing strategy with level assignments?
- Does ADR honor no-mocking principle?
- Does ADR document trade-offs and consequences?

**If NOT working on specs-based work item**: Proceed directly with ADR review using provided architectural decision.
</context_loading>

<process>
1. **Read the ADR** completely
2. **Check EVERY section for temporal language** — reject any reference to current code, existing files, or migration plans
3. **Identify violations** - what contradicts testing principles
4. **Output decision** - APPROVED or REJECTED with specific violations
5. **Show correct approach** - what the architecture should be

</process>

<principles_to_enforce>
**Level definitions:**

- Level 1: Node.js built-ins (fs, git, etc.) + temp fixtures
  - Includes: All Node.js standard library, Git operations, standard dev tools (cat, grep, curl)
  - Excludes: Project-specific binaries, network, external services

- Level 2: Project-specific binaries/tools running locally
  - Includes: Hugo, Caddy, Claude Code, Docker, TypeScript compiler
  - Excludes: Network calls, GitHub, external services

- Level 3: External dependencies (GitHub, network, Chrome)
  - Includes: Network services, APIs, external repos, browsers
  - Full real-world workflows with external dependencies

**Critical rules:**

- Git is Level 1 (standard dev tool, always available in CI)
- Project-specific tools require installation/setup (Level 2)
- Network dependencies and external services are Level 3

**Mocking prohibition:**

- NO `vi.mock()` or `jest.mock()` for external services
- NO mocking HTTP responses for external APIs
- Use dependency injection with TypeScript interfaces instead

**Reality principle:**

- "Reality is the oracle, not mocks"
- Tests must verify behavior against real systems at appropriate levels

**Atemporal voice prohibition** (Durable Map Rule):

- **ADRs state architectural truth. They NEVER narrate code history, current state, or migration plans.**
- This is a REJECTION-level violation in ANY section — Context, Decision, Rationale, Compliance, all of it. No section gets a pass.
- An ADR that references existing code ("The current X has...", "The file X does not exist") is temporal — it becomes stale the moment that code changes.
- Code that violates an ADR is discovered through code review and test coverage analysis against the ADR's invariants. The ADR itself never names files to delete, code to replace, or implementations to migrate away from.

**Temporal patterns to reject:**

- "The current `module.ts` has..." — narrates code state
- "The file `deprecated/old.ts` does not exist" — narrates filesystem state
- "We need to replace..." / "We need to migrate..." — narrates a plan, not a truth
- "Currently X uses..." — snapshot that expires
- "The existing implementation..." — references code, not architecture
- "After evaluating options..." — narrates decision history
- "X has accumulated without..." — narrates drift
- "Previously..." / "Before this..." — there is no before
- "Going forward..." / "In the future..." — there is only the product truth

**The rewrite pattern:**

- TEMPORAL: "The current BuildRunner class in build.ts shells out to Hugo directly without dependency injection."
- ATEMPORAL: "Build orchestration uses dependency injection to isolate tool invocation from build logic."

- TEMPORAL: "The file legacy/builder.ts does not exist and should be removed."
- ATEMPORAL: "Build implementations conform to the BuildDependencies interface." (Non-conforming code is found by code review, not by the ADR.)

- TEMPORAL: "We discovered that direct execa calls make testing impossible."
- ATEMPORAL: "Direct process invocation prevents Level 1 testing. Dependency injection enables isolated unit verification."

</principles_to_enforce>

<output_format>

````markdown
# ARCHITECTURE REVIEW

**Decision:** [APPROVED | REJECTED]

---

## Violations

### {Violation name}

**Where:** {Section name or quote identifying the location}
**Principle violated:** {Specific principle}
**Why this fails:** {Direct explanation}

**Correct approach:**

```typescript
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

- Testing principles: {specific principle violated}

---

{If REJECTED: "Revise and resubmit"}
{If APPROVED: "Architecture meets standards"}

````
</output_format>

<what_to_avoid>
**Don't:**

- Provide checklists - the architect understands what needs to change
- Explain multiple times - be concise
- Count how many times you've seen this - focus on principles
- Provide grep commands - focus on principles, not commands

**Do:**

- Reference specific principles
- Show correct architecture (code examples)
- Be direct about what violates principles
- Assume the architect will understand and fix
- Reject temporal language in ANY section — Context, Decision, Rationale, Compliance
- Show the atemporal rewrite alongside each temporal violation

</what_to_avoid>

<example_review>
```markdown
# ARCHITECTURE REVIEW

**Decision:** REJECTED

---

## Violations

### Mocking External Service

**Where:** Lines 45-47
**Principle violated:** NO MOCKING principle

ADR says "mock the execa calls at the boundary" - this violates testing principles which require dependency injection, not mocking.

**Correct approach:**

```typescript
interface BuildDependencies {
  execa: typeof execa;
}

// Level 1: Inject controlled implementation
// Level 2: Use real binary
````

---

### Missing Testing Strategy

**Where:** ADR has no Testing Strategy section
**Principle violated:** Every ADR must include Testing Strategy

All ADRs require a Testing Strategy section with level assignments.

**Correct approach:**

```markdown
## Testing Strategy

### Level Assignments

| Component        | Level | Justification                   |
| ---------------- | ----- | ------------------------------- |
| Command building | 1     | Pure function, no external deps |
| Hugo invocation  | 2     | Needs real Hugo binary          |
```

---

### Temporal Language in Context Section

**Where:** Context section
**Principle violated:** Atemporal voice (Durable Map Rule)

Context says "The current BuildRunner class in build.ts shells out to Hugo directly without dependency injection, making unit testing impossible."

This narrates code state — it becomes false the moment the file changes. The ADR states what the architecture IS, not what code currently exists. Non-conforming code is discovered through code review against the ADR's invariants.

**Correct approach:**

```markdown
**Technical**: Build orchestration depends on external binaries (Hugo, Caddy).
Dependency injection isolates build logic from tool invocation.
```

---

## Required Changes

1. Remove "mock at boundary" language
2. Add DI interface definitions showing how Level 1 works
3. Add Testing Strategy section with level assignments
4. Update escalation rationale
5. Rewrite Context section in atemporal voice — remove all references to current code state

---

## References

- Testing principles: NO MOCKING, Dependency Injection
- Testing principles: Every ADR must include Testing Strategy

---

Revise and resubmit.

```
</example_review>

<success_criteria>
Review is complete when:

- [ ] Checked ALL sections for temporal language (Durable Map Rule) — Context, Decision, Rationale, Compliance
- [ ] All testing principle violations identified
- [ ] Correct approach shown for each violation
- [ ] Verified ADR never names files to delete or code to replace (code removal comes from code review, not ADRs)
- [ ] Required changes listed concisely
- [ ] Decision clearly stated (APPROVED/REJECTED)

_Review with authority from expertise. Be concise and direct._

</success_criteria>
```
