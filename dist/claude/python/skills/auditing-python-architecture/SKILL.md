---
name: auditing-python-architecture
description: Use when asked by the user to invoke the Python architecture audit skill
allowed-tools: Read, Grep
---

Invoke the `python:standardizing-python-architecture` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Review ADRs against `/standardizing-python-architecture` conventions, `/testing` principles, atemporal voice rules, and applicable PDR constraints. Produce a structured verdict per concern. This skill is read-only -- it produces verdicts, not code changes.

**Standards are pre-loaded above.** It defines the canonical ADR sections, how testability appears in Verification rules, and what does NOT belong in an ADR.
</objective>

<context_loading>
**For spec-tree work items: Load complete ADR/PDR hierarchy before reviewing.**

When reviewing ADRs for a spec-tree work item (enabler/outcome), ensure complete architectural context is loaded:

1. **Invoke `spec-tree:contextualizing`** with the node path
2. **Verify all ancestor ADRs/PDRs are loaded** -- must check for consistency with decision hierarchy
3. **Verify ADR references ancestor decisions** -- node ADRs should reference relevant ancestor ADRs/PDRs

**The `spec-tree:contextualizing` skill provides:**

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- TRD with technical requirements
- Target node spec with typed assertions

**Review focus:**

- Does ADR contradict any ancestor ADR/PDR decisions?
- Does the ADR's `## Verification` (`### Audit`) include testability constraints (DI, no mocking)?
- Does ADR use only the authoritative sections (no phantom sections)?
- Does ADR honor atemporal voice in ALL sections?
- Does ADR document trade-offs and consequences?

**If NOT working on spec-tree work item**: Proceed directly with ADR review using provided architectural decision.

</context_loading>

<process>

1. **Standards are pre-loaded above.** Read repo-local `spx/local/python-architecture.md` if present; an overlay routes skill behavior to the product's governing specs and decisions and supplements skill behavior without declaring product truth.
2. **Read `/testing`** for methodology (5 stages, 5 factors, 7 exceptions)
3. **Verify an ADR exists.** If the module makes architectural decisions (module layout, library choice, DI patterns) without an ADR, the absence is the violation — REJECT immediately. Do not treat missing ADRs as N/A.
4. **Read the ADR** completely
5. **Check section structure** -- only authoritative sections allowed (title + decision stated directly, Rationale, Invariants, Verification). Flag phantom sections (Purpose, Context, Trade-offs, Testing Strategy, Status, etc.)
6. **Check EVERY section for temporal language** -- reject any reference to current code, existing files, or migration plans
7. **Check `## Verification`** -- must include testability constraints as ALWAYS/NEVER rules under `### Audit`; must NOT include level assignment tables
8. **Check for mocking language** -- reject unittest.mock.patch, respx.mock, "mock at boundary" in any section
9. **Verify level accuracy** -- SaaS services jump `l1` to `l3` (no `l2`)
10. **Check test double usage** -- must document which `/testing` exception case applies
11. **Identify all violations** and classify per concern
12. **Output structured verdict** -- APPROVED or REJECTED with per-concern table

</process>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Accepted temporal language because it was in the Rationale section.** The auditor assumed Rationale was exempt from atemporal voice because it explains "why." It is not exempt. "After evaluating options, we decided..." narrates decision history. Atemporal: "X was rejected because Y violates Z." The atemporal voice rule applies to ALL sections, no exceptions.

**Approved ADR with "DI Protocol" but no testing strategy in Verification.** The auditor saw a Protocol definition in the decision statement and assumed testing was covered. The ADR had no Verification rules enabling specific levels -- the Protocol existed but nothing mandated its use. A Protocol definition is not a testability constraint; an ALWAYS rule requiring it as a parameter is.

**Missed "respx.mock" in a code example.** The ADR's `## Verification` rules showed mocking in a code block illustrating the "correct approach." The auditor only checked prose for mocking language, not code examples. Check ALL content -- prose and code blocks.

**Accepted `l2` for a SaaS service.** The auditor didn't verify the "SaaS services jump `l1` to `l3`" rule and accepted `l2` for Trakt.tv API testing. SaaS services cannot run locally -- there is no `l2`. This is one of the most commonly violated principles.

**Flagged a phantom section but missed the real problem.** The auditor correctly rejected a Testing Strategy section but didn't check whether `## Verification` had equivalent testability constraints. Removing a phantom section is not enough -- the testability constraints must appear somewhere in the ADR (under `### Audit`).

**Confused `sys.path` manipulation with a real import.** A test fixture inserted a fake module into `sys.path`, making it appear as a real dependency. The auditor missed this because they only checked `import` statements, not runtime path manipulation. When reviewing ADR examples that reference imports, check for `sys.path` and `importlib` tricks.

</failure_modes>

<principles_to_enforce>

All canonical conventions are in `/standardizing-python-architecture`. Read it first. The audit checks these specific concerns:

**1. Section structure** -- Only authoritative sections from the ADR template. See `<adr_sections>` in `/standardizing-python-architecture` for the complete list. Flag any section not in that list.

**2. Testability in Verification** -- The `## Verification` section must include ALWAYS/NEVER rules under `### Audit` that enable appropriate testing. See `<testability_in_verification>` in `/standardizing-python-architecture` for the correct pattern. Level assignment tables and Testing Strategy sections are violations.

**3. Atemporal voice** -- ADRs state architectural truth in ALL sections. See `<atemporal_voice>` in `/standardizing-python-architecture` for temporal patterns to reject and rewrite examples.

**4. Mocking prohibition** -- No mocking language anywhere in the ADR. See `<di_patterns>` in `/standardizing-python-architecture` for what to check and correct ADR language.

**5. Level accuracy** -- When the `## Verification` rules reference testing levels, verify against `/testing` definitions. See `<level_context>` in `/standardizing-python-architecture`. Key rule: SaaS services (Trakt, GitHub API, Stripe, Auth0) jump `l1` to `l3` (no `l2`).

**6. Anti-patterns** -- Check for content that does not belong in an ADR. See `<anti_patterns>` in `/standardizing-python-architecture` for the full table. Note Python-specific anti-pattern: `src.*` import examples should use `product.*` / `product_testing.*`.

**7. Test double exception cases** -- Any test double usage must document which of the 7 `/testing` Stage 5 exceptions applies. No exception = no doubles.

</principles_to_enforce>

<output_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/auditing/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "auditing-python-architecture",
  "target": "<adr-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "section-structure", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "testability-in-verification", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "mocking-prohibition", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "level-accuracy", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "anti-patterns", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "ancestor-consistency", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` carries the violation pattern (e.g., `phantom-section`, `temporal-voice`, `mocking-language`); `file` is the ADR path; `message` carries the one-line "why this fails". Include the correct-approach code sample and required-changes summary directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</output_format>

<what_to_avoid>

**Don't:**

- Reference specific line numbers (they change) -- use section names or quoted text
- Provide grep commands -- focus on principles, not tooling
- Explain the same principle multiple times -- be concise
- Approve an ADR just because it removed a phantom section -- check that testability constraints moved to `## Verification`

**Do:**

- Reference `/standardizing-python-architecture` section names (e.g., `<testability_in_verification>`, `<atemporal_voice>`)
- Reference `/testing` section names for level rules (e.g., "Stage 2 Five Factors", "Cardinal Rule")
- Reference `/standardizing-python-tests` for Python-specific Protocol patterns
- Show correct architecture with code examples
- Be direct about violations
- Reject temporal language in ANY section -- the decision statement, Rationale, Verification
- Show the atemporal rewrite alongside each temporal violation

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-audit.md` for a complete REJECTED review showing all concern types: SaaS `l2` violation, mocking language, missing testability in `## Verification`, and temporal voice violations.
</example_review>

<success_criteria>
Review is complete when:

- [ ] Read `/standardizing-python-architecture` before starting review
- [ ] Checked section structure against authoritative ADR template
- [ ] Checked ALL sections for temporal language -- the decision statement, Rationale, Verification
- [ ] Verified `## Verification` includes testability constraints (ALWAYS/NEVER for DI, no mocking)
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
