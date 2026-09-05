---
name: audit-python-architecture
description: >-
  Python-specific architecture audit — judges the Python architecture target in
  scope for dependency injection, mocking prohibition, execution-level accuracy,
  Python anti-patterns, and test-double exception cases.
model: sonnet
allowed-tools: Read, Grep, Glob, Skill
---

{!% require_skill 'python:python-architecture-standards' %!}

<objective>
A JSON verdict on a Python architecture scope — `APPROVED`, or `REJECTED` with concern rows for dependency injection testability, mocking prohibition, execution-level accuracy, Python anti-patterns, ancestor consistency, and test-double exception cases.
</objective>

<constraints>

- Read-only over the audited repository. Never edit files, stage changes, commit, or open pull requests.
- Produce only the JSON verdict described in `<verdict_format>`; finding messages state the violated rule and consequence, while corrective examples remain in references and standards.
- Judge only Python-specific architecture concerns: dependency injection, no-mocking, execution-level accuracy, Python anti-patterns, and test-double exception cases. Generic decision-record section structure, atemporal voice, and per-rule tag validity are outside this subject — a structural, voice, or tag finding is out of scope even when the target is an ADR.
- Treat `PASS | FAIL | NOT_APPLICABLE` as the only row vocabulary for this skill.

</constraints>

<audit_workflow>
**Inputs.** This audit judges the target it is given, against the governing context already loaded when it runs:

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Target node spec with typed assertions, for a spec-tree work item (enabler/outcome)
- The architecture target: implementation files, a changed-file partition, or an ADR path

**Python review focus:**

- For implementation targets, do the changed Python files conform to loaded architecture decisions for dependency injection, no mocking, level accuracy, and test-double exception cases?
- For ADR targets, does `## Verification` (`### Audit`) include testability constraints (DI, no mocking)?
- Does the target use any mocking language anywhere (implementation, prose, or code examples)?
- Are execution levels accurate (SaaS services jump `l1` to `l3`, no `l2`)?
- Does any test-double usage document which `/test` exception case applies?
- Does the target contradict any ancestor ADR/PDR decision on a Python-architecture concern?

**Procedure:**

1. **Standards are pre-loaded above.** Read repo-local `spx/local/python-architecture.md` if present; an overlay routes skill behavior to the product's governing specs and decisions and supplements skill behavior without declaring product truth.
2. **Read repo-local test overlay** `spx/local/python-tests.md` if present before judging level references or test-double exception cases.
3. **Read `/test`** for methodology (5 stages, 5 factors, 7 exceptions)
4. **Read the architecture target** completely — the implementation files or the ADR supplied as the target
5. **Check testability constraints** — ADR targets express them in `## Verification` / `### Audit`; implementation targets must conform to the loaded architecture decisions' DI and no-mocking constraints
6. **Check for mocking language** — reject `unittest.mock.patch`, `respx.mock`, "mock at boundary" in any section, prose AND code examples
7. **Verify level accuracy** — SaaS services jump `l1` to `l3` (no `l2`)
8. **Check test double usage** — must document which `/test` exception case applies
9. **Check Python anti-patterns** — `src.*` import examples should use `product.*` / `product_testing.*`
10. **Identify all Python-architecture violations** and classify per concern
11. **Output the JSON verdict** with `overall` set to `APPROVED` or `REJECTED` and every concern row populated

</audit_workflow>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved ADR with "DI Protocol" but no testing strategy in Verification.** Claude saw a Protocol definition in the decision statement and assumed testing was covered. The ADR had no Verification rules enabling specific levels — the Protocol existed but nothing mandated its use. A Protocol definition is not a testability constraint; an ALWAYS rule requiring it as a parameter is.

**Missed "respx.mock" in a code example.** The ADR's `## Verification` rules showed mocking in a code block illustrating the "correct approach." Claude only checked prose for mocking language, not code examples. Check ALL content — prose and code blocks.

**Accepted `l2` for a SaaS service.** Claude didn't verify the "SaaS services jump `l1` to `l3`" rule and accepted `l2` for Trakt.tv API testing. SaaS services cannot run locally — there is no `l2`. This is one of the most commonly violated principles.

**Confused `sys.path` manipulation with a real import.** A test fixture inserted a fake module into `sys.path`, making it appear as a real dependency. Claude missed this because it only checked `import` statements, not runtime path manipulation. When reviewing ADR examples that reference imports, check for `sys.path` and `importlib` tricks.

**Re-judged section structure or temporal voice.** Claude flagged a phantom section or temporal sentence. Those concerns are judged against the canonical decision template, not this skill's Python-architecture subject; a structural or voice finding from this skill is out of scope and must be dropped.

</failure_modes>

<principles_to_enforce>

All canonical conventions are in `/python-architecture-standards`. Read it first. This skill checks only the Python-specific concerns:

**1. Testability constraints** — ADR targets must include ALWAYS/NEVER rules under `## Verification` / `### Audit` that enable appropriate testing; implementation targets must comply with the loaded architecture decisions' testability constraints. See `<testability_in_verification>` in `/python-architecture-standards` for the correct ADR pattern. Level assignment tables are violations.

**2. Mocking prohibition** — No mocking language anywhere in the architecture target. See `<di_patterns>` in `/python-architecture-standards` for what to check and correct ADR language.

**3. Level accuracy** — When the architecture target references testing levels, verify against `/test` definitions. See `<level_context>` in `/python-architecture-standards`. Key rule: SaaS services (Trakt, GitHub API, Stripe, Auth0) jump `l1` to `l3` (no `l2`).

**4. Python anti-patterns** — Check for Python-specific architecture anti-patterns. See `<anti_patterns>` in `/python-architecture-standards`. Note Python-specific anti-pattern: `src.*` import examples should use `product.*` / `product_testing.*`.

**5. Test double exception cases** — Any test double usage must document which of the 7 `/test` Stage 5 exceptions applies. No exception = no doubles.

Section structure, atemporal voice, and per-rule tag validity are NOT this skill's concern — they are judged against the canonical decision template, outside this Python-architecture subject.

</principles_to_enforce>

<verdict_format>

Emit a structured verdict. The skill's entire output is the verdict payload.

The skill's `overall` is `APPROVED` iff every concern row is `PASS` or `NOT_APPLICABLE`; it is `REJECTED` if any concern is `FAIL`. Every `NOT_APPLICABLE` row explains why its concern does not apply. An unavailable required inspection is `FAIL`, never `NOT_APPLICABLE`. Findings use severity `blocking` or `debt`.

```json
{
  "schema_version": 1,
  "skill": "audit-python-architecture",
  "target": "<architecture-scope>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    { "name": "testability-in-verification", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "mocking-prohibition", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "level-accuracy", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "anti-patterns", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "ancestor-consistency", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "test-double-exception-cases", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` carries the violation pattern (e.g., `missing-testability`, `mocking-language`, `saas-l2`); `file` is the relevant implementation file or ADR path; `message` carries the one-line violated rule and consequence, while `observed` and `expected` carry the evidence. Corrective examples and remediation narrative stay in the referenced example and standards files rather than the verdict.

</verdict_format>

<what_to_avoid>

**Don't:**

- Judge section structure, atemporal voice, or per-rule tag validity — those are outside this skill's Python-architecture subject
- Reference specific line numbers (they change) — use section names or quoted text
- Provide grep commands — focus on principles, not tooling
- Approve an architecture target just because a Protocol is defined — check that an ALWAYS rule mandates it for ADR targets or that implementation code follows the loaded architecture constraint

**Do:**

- Reference `/python-architecture-standards` section names (e.g., `<testability_in_verification>`, `<di_patterns>`)
- Reference `/test` methodology by its real heading, `Stage 2: At what level does that evidence live?`, for level rules
- Reference `/python-architecture-standards` `<di_patterns>` for Python-specific Protocol patterns
- Keep corrective architecture examples in the referenced standards and example files, never in the emitted verdict
- Be direct about violations

</what_to_avoid>

<example_reference>
Read `${CLAUDE_SKILL_DIR}/references/example-audit.md` for a complete ADR-target `REJECTED` JSON verdict showing the Python concern types: SaaS `l2` violation, mocking language, and missing testability in `## Verification`.
</example_reference>

<success_criteria>
The verdict is sound when:

- Every applicable Python architecture concern row is evaluated, with inapplicable concerns marked `NOT_APPLICABLE` and explained rather than skipped.
- `overall` is `REJECTED` when any concern row is `FAIL` and `APPROVED` when every concern row is `PASS` or explained `NOT_APPLICABLE`; missing required context produces a failing row and `REJECTED`.
- Each rejecting finding names the relevant implementation file or ADR path, violated rule and consequence in `message`, and concrete evidence in `observed` and `expected`.
- No finding judges generic ADR structure, atemporal voice, or per-rule tag validity.
- The same architecture scope and governing context produce the same JSON verdict.

</success_criteria>
