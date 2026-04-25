---
name: auditing-typescript-architecture
description: >-
  ALWAYS invoke this skill when auditing ADRs for TypeScript or after writing or editing one.
  NEVER implement from an unaudited ADR.
allowed-tools: Read, Grep
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript-architecture/SKILL.md"`

<objective>
Review ADRs against `/standardizing-typescript-architecture` conventions, `/testing` principles, atemporal voice rules, and applicable PDR constraints. Produce a structured verdict per concern. This skill is read-only -- it produces verdicts, not code changes.

**Read `/standardizing-typescript-architecture` before reviewing any ADR.** It defines the canonical ADR sections, how testability appears in Compliance rules, and what does NOT belong in an ADR.

After reading `/standardizing-typescript-architecture`, check for `spx/local/typescript-architecture.md` at the repository root. Read that file if it exists and apply it as the repo-local specialization.
</objective>

<context_loading>
**For spec-tree work items: Load complete ADR/PDR hierarchy before reviewing.**

If you're reviewing ADRs for a spec-tree work item (enabler/outcome), ensure complete architectural context is loaded:

1. **Invoke `spec-tree:contextualizing`** with the node path
2. **Verify all ancestor ADRs/PDRs are loaded** -- must check for consistency with decision hierarchy
3. **Verify ADR references ancestor decisions** -- node ADRs should reference relevant ancestor ADRs/PDRs

**The `spec-tree:contextualizing` skill provides:**

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- TRD with technical requirements
- Target node spec with typed assertions

**Review focus:**

- Does ADR contradict any ancestor ADR/PDR decisions?
- Does ADR Compliance section include testability constraints (DI, no mocking)?
- Does ADR use only the authoritative sections (no phantom sections)?
- Does ADR honor atemporal voice in ALL sections?
- Does ADR document trade-offs and consequences?

**If NOT working on spec-tree work item**: Proceed directly with ADR review using provided architectural decision.

</context_loading>

<process>

1. **Read `/standardizing-typescript-architecture`**, then `spx/local/typescript-architecture.md` if present, for canonical conventions
2. **Verify an ADR exists.** If the module makes architectural decisions (module layout, library choice, DI patterns) without an ADR, the absence is the violation — REJECT immediately. Do not treat missing ADRs as N/A.
3. **Read the ADR** completely
4. **Check section structure** -- only authoritative sections allowed (Purpose, Context, Decision, Rationale, Trade-offs accepted, Invariants, Compliance). Flag phantom sections (Testing Strategy, Status, etc.)
5. **Check EVERY section for temporal language** -- reject any reference to current code, existing files, or migration plans
6. **Check Compliance section** -- must include testability constraints as MUST/NEVER rules; must NOT include level assignment tables
7. **Check for mocking language** -- reject vi.mock(), jest.mock(), "mock at boundary" in any section
8. **Identify all violations** and classify per concern
9. **Output structured verdict** -- APPROVED or REJECTED with per-concern table

</process>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved code that passed linters but had a design flaw.** The auditor trusted the tooling output (Phase 1 equivalent) and skimmed the Compliance section. The ADR mandated DI for all external calls, but the Compliance rules were so vague ("use good practices") that they couldn't catch anything. A Compliance rule that cannot falsify non-conforming code is not a rule.

**Rejected an ADR for a false positive.** The auditor flagged a parameter in a DI interface as "dead code" because it wasn't used in the example. The parameter was required by a Protocol contract that other implementations relied on. Before flagging dead parameters in interfaces, check if the interface is implemented elsewhere.

**Missed mocking hidden behind DI.** The ADR said "dependency injection" but described injecting `vi.fn()` as the controlled implementation. This is still mocking -- DI is the delivery mechanism, but `vi.fn()` is a mock. Correct DI injects a controlled *real* implementation (a simple function or object), not a mock framework spy.

**Distracted by style while missing a logic flaw.** The auditor spent review time on naming conventions and formatting while a branch condition in the Compliance rules was inverted -- the MUST and NEVER were swapped. Comprehension (understanding what the ADR actually says) must come before style concerns.

**Accepted temporal language because it was in the Rationale section.** The auditor assumed Rationale was exempt from atemporal voice because it explains "why." It is not exempt. "After evaluating options, we decided..." narrates decision history. Atemporal: "X was rejected because Y violates Z."

**Flagged a phantom section but missed the real problem.** The auditor correctly rejected a Testing Strategy section but didn't check whether the Compliance section had equivalent testability constraints. Removing a phantom section is not enough -- the testability constraints must appear somewhere in the ADR (in Compliance).

</failure_modes>

<principles_to_enforce>

All canonical conventions are in `/standardizing-typescript-architecture`. Read it first. The audit checks these specific concerns:

**1. Section structure** -- Only authoritative sections from the ADR template. See `<adr_sections>` in `/standardizing-typescript-architecture` for the complete list. Flag any section not in that list.

**2. Testability in Compliance** -- The Compliance section must include MUST/NEVER rules that enable appropriate testing. See `<testability_in_compliance>` in `/standardizing-typescript-architecture` for the correct pattern. Level assignment tables and Testing Strategy sections are violations.

**3. Atemporal voice** -- ADRs state architectural truth in ALL sections. See `<atemporal_voice>` in `/standardizing-typescript-architecture` for temporal patterns to reject and rewrite examples.

**4. Mocking prohibition** -- No mocking language anywhere in the ADR. See `<di_patterns>` in `/standardizing-typescript-architecture` for what to check and correct ADR language.

**5. Level accuracy** -- When the Compliance section references testing levels, verify against `/testing` definitions. See `<level_context>` in `/standardizing-typescript-architecture`. Key rule: SaaS services jump `l1` to `l3` (no `l2`).

**6. Anti-patterns** -- Check for content that does not belong in an ADR. See `<anti_patterns>` in `/standardizing-typescript-architecture` for the full table.

</principles_to_enforce>

<output_format>

````markdown
# ARCHITECTURE REVIEW

**Decision:** [APPROVED | REJECTED]

## Verdict

| # | Concern               | Status            | Detail            |
| - | --------------------- | ----------------- | ----------------- |
| 1 | Section structure     | {PASS/REJECT}     | {one-line detail} |
| 2 | Testability in Compl. | {PASS/REJECT}     | {one-line detail} |
| 3 | Atemporal voice       | {PASS/REJECT}     | {one-line detail} |
| 4 | Mocking prohibition   | {PASS/REJECT}     | {one-line detail} |
| 5 | Level accuracy        | {PASS/REJECT}     | {one-line detail} |
| 6 | Anti-patterns         | {PASS/REJECT}     | {one-line detail} |
| 7 | Ancestor consistency  | {PASS/REJECT/N/A} | {one-line detail} |

---

## Violations

### {Violation name}

**Where:** {Section name or quoted text identifying the location}
**Concern:** {Which concern from the verdict table}
**Why this fails:** {Direct explanation}

**Correct approach:**

```typescript
{Show what the architecture should be}
```

---

{Repeat for each violation}

---

## Required Changes

{Concise list of what must change}

---

## References

- /standardizing-typescript-architecture: {section name}
- /testing: {section name if applicable}

---

{If REJECTED: "Revise and resubmit."}
{If APPROVED: "Architecture meets standards."}
````

</output_format>

<what_to_avoid>

**Don't:**

- Reference specific line numbers (they change) -- use section names or quoted text
- Provide grep commands -- focus on principles, not tooling
- Explain the same principle multiple times -- be concise
- Approve an ADR just because it removed a phantom section -- check that testability constraints moved to Compliance

**Do:**

- Reference `/standardizing-typescript-architecture` section names (e.g., `<testability_in_compliance>`, `<atemporal_voice>`)
- Reference `/testing` section names for level rules (e.g., "Stage 2 Five Factors")
- Show correct architecture with code or markdown examples
- Be direct about violations
- Reject temporal language in ANY section -- Context, Decision, Rationale, Compliance
- Show the atemporal rewrite alongside each temporal violation

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-review.md` for a complete REJECTED review showing all concern types: phantom Testing Strategy section, missing testability in Compliance, mocking language, and temporal voice violations.
</example_review>

<success_criteria>
Review is complete when:

- [ ] Read `/standardizing-typescript-architecture` and `spx/local/typescript-architecture.md` (if present) before starting review
- [ ] Checked section structure against authoritative ADR template
- [ ] Checked ALL sections for temporal language -- Context, Decision, Rationale, Compliance
- [ ] Verified Compliance section includes testability constraints (MUST/NEVER for DI, no mocking)
- [ ] Verified no phantom sections (Testing Strategy, Status, etc.)
- [ ] Verified no mocking language anywhere in ADR
- [ ] Verified ADR never names files to delete or code to replace
- [ ] Structured verdict table with per-concern status
- [ ] Correct approach shown with code examples for each violation
- [ ] Required changes listed concisely
- [ ] Decision clearly stated (APPROVED/REJECTED)

</success_criteria>
