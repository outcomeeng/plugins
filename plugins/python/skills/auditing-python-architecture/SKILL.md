---
name: auditing-python-architecture
description: >-
  ALWAYS invoke this skill when auditing ADRs for Python or after writing an ADR.
  NEVER implement from an unaudited ADR.
allowed-tools: Read, Grep
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-python-architecture/SKILL.md" || echo "standardizing-python-architecture not found — invoke python:standardizing-python-architecture manually"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. `python:standardizing-python-architecture`

</codex_fallback>

<objective>
Review ADRs against `/standardizing-python-architecture` conventions, `/testing` principles, atemporal voice rules, and applicable PDR constraints. Produce a structured verdict per concern. This skill is read-only -- it produces verdicts, not code changes.

**Standards are pre-loaded above.** It defines the canonical ADR sections, how testability appears in Compliance rules, and what does NOT belong in an ADR.
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

1. **Standards are pre-loaded above.** Read repo-local `spx/local/python-architecture.md` if present.
2. **Read `/testing`** for methodology (5 stages, 5 factors, 7 exceptions)
3. **Verify an ADR exists.** If the module makes architectural decisions (module layout, library choice, DI patterns) without an ADR, the absence is the violation — REJECT immediately. Do not treat missing ADRs as N/A.
4. **Read the ADR** completely
5. **Check section structure** -- only authoritative sections allowed (Purpose, Context, Decision, Rationale, Trade-offs accepted, Invariants, Compliance). Flag phantom sections (Testing Strategy, Status, etc.)
6. **Check EVERY section for temporal language** -- reject any reference to current code, existing files, or migration plans
7. **Check Compliance section** -- must include testability constraints as MUST/NEVER rules; must NOT include level assignment tables
8. **Check for mocking language** -- reject unittest.mock.patch, respx.mock, "mock at boundary" in any section
9. **Verify level accuracy** -- SaaS services jump `l1` to `l3` (no `l2`)
10. **Check test double usage** -- must document which `/testing` exception case applies
11. **Identify all violations** and classify per concern
12. **Output structured verdict** -- APPROVED or REJECTED with per-concern table

</process>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Accepted temporal language because it was in the Rationale section.** The auditor assumed Rationale was exempt from atemporal voice because it explains "why." It is not exempt. "After evaluating options, we decided..." narrates decision history. Atemporal: "X was rejected because Y violates Z." The atemporal voice rule applies to ALL sections, no exceptions.

**Approved ADR with "DI Protocol" but no testing strategy in Compliance.** The auditor saw a Protocol definition in the Decision section and assumed testing was covered. The ADR had no Compliance rules enabling specific levels -- the Protocol existed but nothing mandated its use. A Protocol definition is not a testability constraint; a MUST rule requiring it as a parameter is.

**Missed "respx.mock" in a code example.** The ADR's Compliance section showed mocking in a code block illustrating the "correct approach." The auditor only checked prose for mocking language, not code examples. Check ALL content -- prose and code blocks.

**Accepted `l2` for a SaaS service.** The auditor didn't verify the "SaaS services jump `l1` to `l3`" rule and accepted `l2` for Trakt.tv API testing. SaaS services cannot run locally -- there is no `l2`. This is one of the most commonly violated principles.

**Flagged a phantom section but missed the real problem.** The auditor correctly rejected a Testing Strategy section but didn't check whether the Compliance section had equivalent testability constraints. Removing a phantom section is not enough -- the testability constraints must appear somewhere in the ADR (in Compliance).

**Confused `sys.path` manipulation with a real import.** A test fixture inserted a fake module into `sys.path`, making it appear as a real dependency. The auditor missed this because they only checked `import` statements, not runtime path manipulation. When reviewing ADR examples that reference imports, check for `sys.path` and `importlib` tricks.

</failure_modes>

<principles_to_enforce>

All canonical conventions are in `/standardizing-python-architecture`. Read it first. The audit checks these specific concerns:

**1. Section structure** -- Only authoritative sections from the ADR template. See `<adr_sections>` in `/standardizing-python-architecture` for the complete list. Flag any section not in that list.

**2. Testability in Compliance** -- The Compliance section must include MUST/NEVER rules that enable appropriate testing. See `<testability_in_compliance>` in `/standardizing-python-architecture` for the correct pattern. Level assignment tables and Testing Strategy sections are violations.

**3. Atemporal voice** -- ADRs state architectural truth in ALL sections. See `<atemporal_voice>` in `/standardizing-python-architecture` for temporal patterns to reject and rewrite examples.

**4. Mocking prohibition** -- No mocking language anywhere in the ADR. See `<di_patterns>` in `/standardizing-python-architecture` for what to check and correct ADR language.

**5. Level accuracy** -- When the Compliance section references testing levels, verify against `/testing` definitions. See `<level_context>` in `/standardizing-python-architecture`. Key rule: SaaS services (Trakt, GitHub API, Stripe, Auth0) jump `l1` to `l3` (no `l2`).

**6. Anti-patterns** -- Check for content that does not belong in an ADR. See `<anti_patterns>` in `/standardizing-python-architecture` for the full table. Note Python-specific anti-pattern: `src.*` import examples should use `product.*` / `product_testing.*`.

**7. Test double exception cases** -- Any test double usage must document which of the 7 `/testing` Stage 5 exceptions applies. No exception = no doubles.

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

```python
{Show what the architecture should be}
```

---

{Repeat for each violation}

---

## Required Changes

{Concise list of what must change}

---

## References

- /standardizing-python-architecture: {section name}
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

- Reference `/standardizing-python-architecture` section names (e.g., `<testability_in_compliance>`, `<atemporal_voice>`)
- Reference `/testing` section names for level rules (e.g., "Stage 2 Five Factors", "Cardinal Rule")
- Reference `/standardizing-python-tests` for Python-specific Protocol patterns
- Show correct architecture with code examples
- Be direct about violations
- Reject temporal language in ANY section -- Context, Decision, Rationale, Compliance
- Show the atemporal rewrite alongside each temporal violation

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-review.md` for a complete REJECTED review showing all concern types: SaaS `l2` violation, mocking language, missing testability in Compliance, and temporal voice violations.
</example_review>

<success_criteria>
Review is complete when:

- [ ] Read `/standardizing-python-architecture` before starting review
- [ ] Checked section structure against authoritative ADR template
- [ ] Checked ALL sections for temporal language -- Context, Decision, Rationale, Compliance
- [ ] Verified Compliance section includes testability constraints (MUST/NEVER for DI, no mocking)
- [ ] Verified no phantom sections (Testing Strategy, Status, etc.)
- [ ] Verified no mocking language anywhere in ADR (prose AND code examples)
- [ ] Verified level assignments -- no `l2` for SaaS services
- [ ] Verified test double usage has documented exception case
- [ ] Verified ADR never names files to delete or code to replace
- [ ] Output follows format with section references (not line numbers)
- [ ] Structured verdict table with per-concern status
- [ ] Correct approach shown with code examples for each violation
- [ ] Decision clearly stated (APPROVED/REJECTED)

</success_criteria>
