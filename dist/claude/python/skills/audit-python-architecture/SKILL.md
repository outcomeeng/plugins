---
name: audit-python-architecture
description: >-
  Python-specific ADR architecture audit — dependency injection, no-mocking, level accuracy — composed by the generic adr-auditor agent for the Python concerns in scope.
  Reached only through a dispatched auditor agent, never the main conversation.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

Invoke the `python:python-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<dispatch_gate>

This audit runs inside a dispatched auditor's verifier context — the generic `adr-auditor` composing this skill for the Python concerns in scope, or a generic `/audit`-family agent — isolated from the author context that produced the work under audit. This skill judges only Python-specific concerns: dependency injection, no-mocking, and execution-level accuracy. Section structure, atemporal voice, and tag validity are owned by the composing `adr-auditor` reading the canonical template and are never judged here; a structural, voice, or tag finding from this skill is out of scope. When this skill loads in the author/main conversation rather than inside a dispatched auditor agent, STOP — the audit must run in that verifier context.

</dispatch_gate>

<objective>
A structured verdict on an ADR's Python-specific architecture concerns — testability in Verification (dependency injection), the mocking prohibition, execution-level accuracy, Python anti-patterns, and test-double exception cases.
</objective>

<audit_workflow>
**For spec-tree work items: the composing auditor has already loaded the ADR/PDR hierarchy.**

When this skill is composed for a spec-tree work item (enabler/outcome), the dispatching `adr-auditor` has already invoked `spec-tree:contextualize` on the node and loaded the complete ADR/PDR hierarchy. Use that loaded context:

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Target node spec with typed assertions

**Python review focus:**

- Does the ADR's `## Verification` (`### Audit`) include testability constraints (DI, no mocking)?
- Does the ADR use any mocking language anywhere (prose or code examples)?
- Are execution levels accurate (SaaS services jump `l1` to `l3`, no `l2`)?
- Does any test-double usage document which `/test` exception case applies?
- Does the ADR contradict any ancestor ADR/PDR decision on a Python-architecture concern?

**Procedure:**

1. **Standards are pre-loaded above.** Read repo-local `spx/local/python-architecture.md` if present; an overlay routes skill behavior to the product's governing specs and decisions and supplements skill behavior without declaring product truth.
2. **Read `/test`** for methodology (5 stages, 5 factors, 7 exceptions)
3. **Read the ADR** completely, focusing on the Python-specific concerns below
4. **Check `## Verification`** — must include testability constraints as ALWAYS/NEVER rules under `### Audit`; must NOT include level assignment tables
5. **Check for mocking language** — reject `unittest.mock.patch`, `respx.mock`, "mock at boundary" in any section, prose AND code examples
6. **Verify level accuracy** — SaaS services jump `l1` to `l3` (no `l2`)
7. **Check test double usage** — must document which `/test` exception case applies
8. **Check Python anti-patterns** — `src.*` import examples should use `product.*` / `product_testing.*`
9. **Identify all Python-architecture violations** and classify per concern
10. **Output structured verdict** — APPROVED or REJECTED with per-concern table

</audit_workflow>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved ADR with "DI Protocol" but no testing strategy in Verification.** Claude saw a Protocol definition in the decision statement and assumed testing was covered. The ADR had no Verification rules enabling specific levels — the Protocol existed but nothing mandated its use. A Protocol definition is not a testability constraint; an ALWAYS rule requiring it as a parameter is.

**Missed "respx.mock" in a code example.** The ADR's `## Verification` rules showed mocking in a code block illustrating the "correct approach." Claude only checked prose for mocking language, not code examples. Check ALL content — prose and code blocks.

**Accepted `l2` for a SaaS service.** Claude didn't verify the "SaaS services jump `l1` to `l3`" rule and accepted `l2` for Trakt.tv API testing. SaaS services cannot run locally — there is no `l2`. This is one of the most commonly violated principles.

**Confused `sys.path` manipulation with a real import.** A test fixture inserted a fake module into `sys.path`, making it appear as a real dependency. Claude missed this because it only checked `import` statements, not runtime path manipulation. When reviewing ADR examples that reference imports, check for `sys.path` and `importlib` tricks.

**Re-judged section structure or temporal voice.** Claude flagged a phantom section or temporal sentence. Those concerns belong to the composing `adr-auditor` reading the canonical template; a structural or voice finding from this skill is out of scope and must be dropped.

</failure_modes>

<principles_to_enforce>

All canonical conventions are in `/python-architecture-standards`. Read it first. This skill checks only the Python-specific concerns:

**1. Testability in Verification** — The `## Verification` section must include ALWAYS/NEVER rules under `### Audit` that enable appropriate testing. See `<testability_in_verification>` in `/python-architecture-standards` for the correct pattern. Level assignment tables are violations.

**2. Mocking prohibition** — No mocking language anywhere in the ADR. See `<di_patterns>` in `/python-architecture-standards` for what to check and correct ADR language.

**3. Level accuracy** — When the `## Verification` rules reference testing levels, verify against `/test` definitions. See `<level_context>` in `/python-architecture-standards`. Key rule: SaaS services (Trakt, GitHub API, Stripe, Auth0) jump `l1` to `l3` (no `l2`).

**4. Python anti-patterns** — Check for Python-specific content that does not belong in an ADR. See `<anti_patterns>` in `/python-architecture-standards`. Note Python-specific anti-pattern: `src.*` import examples should use `product.*` / `product_testing.*`.

**5. Test double exception cases** — Any test double usage must document which of the 7 `/test` Stage 5 exceptions applies. No exception = no doubles.

Section structure, atemporal voice, and per-rule tag validity are NOT this skill's concern — the composing `adr-auditor` owns them from the canonical template.

</principles_to_enforce>

<verdict_format>

Emit the verdict as JSON conforming to the canonical audit-verdict schema consumed by the composing audit workflow. The skill's entire output is the JSON verdict. The composing audit workflow records and renders the verdict through the audit journal path.

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "audit-python-architecture",
  "target": "<adr-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "testability-in-verification", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "mocking-prohibition", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "level-accuracy", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "anti-patterns", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "ancestor-consistency", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` carries the violation pattern (e.g., `missing-testability`, `mocking-language`, `saas-l2`); `file` is the ADR path; `message` carries the one-line "why this fails". Include the correct-approach code sample and required-changes summary directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</verdict_format>

<what_to_avoid>

**Don't:**

- Judge section structure, atemporal voice, or per-rule tag validity — those belong to the composing `adr-auditor`
- Reference specific line numbers (they change) — use section names or quoted text
- Provide grep commands — focus on principles, not tooling
- Approve an ADR just because a Protocol is defined — check that an ALWAYS rule mandates it

**Do:**

- Reference `/python-architecture-standards` section names (e.g., `<testability_in_verification>`, `<di_patterns>`)
- Reference `/test` section names for level rules (e.g., "Stage 2 Five Factors", "Cardinal Rule")
- Reference `/python-test-standards` for Python-specific Protocol patterns
- Show correct architecture with code examples
- Be direct about violations

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-audit.md` for a complete REJECTED review showing the Python concern types: SaaS `l2` violation, mocking language, and missing testability in `## Verification`.
</example_review>

<success_criteria>
Review is complete when:

- [ ] Read `/python-architecture-standards` before starting review
- [ ] Verified `## Verification` includes testability constraints (ALWAYS/NEVER for DI, no mocking)
- [ ] Verified no mocking language anywhere in ADR (prose AND code examples)
- [ ] Verified level assignments — no `l2` for SaaS services
- [ ] Verified test double usage has documented exception case
- [ ] Verified Python anti-patterns (`src.*` import examples use `product.*` / `product_testing.*`)
- [ ] Did NOT judge section structure, atemporal voice, or tag validity — those are the composing adr-auditor's concern
- [ ] Output follows format with section references (not line numbers)
- [ ] Structured verdict table with per-concern status
- [ ] Decision clearly stated (APPROVED/REJECTED)

</success_criteria>
