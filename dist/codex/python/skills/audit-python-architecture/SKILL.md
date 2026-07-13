---
name: audit-python-architecture
model: sonnet
description: >-
  Python-specific architecture audit — dependency injection, no-mocking, level accuracy — composed by generic artifact-type auditors for the Python concerns in scope.
  Reached only through a dispatched auditor agent, never the main conversation.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

<dispatch_gate>

This audit runs inside a dispatched artifact-type auditor's verifier context — `implementation-auditor` composing this skill for Python implementation architecture scope, or `adr-auditor` composing it for a Python ADR's language-specific architecture concerns — isolated from the author context that produced the work under audit. This skill judges only Python-specific architecture concerns: dependency injection, no-mocking, execution-level accuracy, Python anti-patterns, and test-double exception cases. Generic decision-record structure, atemporal voice, and tag validity are owned by the composing `adr-auditor` when the target is an ADR and are never judged here; a structural, voice, or tag finding from this skill is out of scope. When this skill loads in the author/main conversation rather than inside a dispatched auditor agent, STOP — the audit must run in that verifier context.

</dispatch_gate>

<prerequisites>
Invoke the `python:python-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.
</prerequisites>

<objective>
A JSON verdict on a Python architecture scope — `APPROVED`, or `REJECTED` with concern rows for dependency injection testability, mocking prohibition, execution-level accuracy, Python anti-patterns, ancestor consistency, and test-double exception cases.
</objective>

<constraints>

- MUST remain read-only over the audited repository; NEVER edit files, stage changes, commit, or open pull requests.
- MUST produce only the JSON verdict described in `<verdict_format>`; finding messages state the violated rule and consequence, while corrective examples remain in references and standards.
- MUST judge only Python-specific architecture concerns; generic decision-record section structure, atemporal voice, and per-rule tag validity are owned by the composing artifact-type auditor when the target is an ADR.
- MUST use `PASS | FAIL | NOT_APPLICABLE` as the only row vocabulary for this skill; the composing verification workflow maps the JSON verdict into the enclosing `spx verification run` projection.

</constraints>

<audit_workflow>
**For spec-tree work items: the composing auditor has already loaded the governing context.**

When this skill is composed for a spec-tree work item (enabler/outcome), the dispatching artifact-type auditor has already invoked `spec-tree:contextualize` on the node and loaded the complete governing context. Use that loaded context:

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Target node spec with typed assertions
- Implementation files, changed-file partition, or ADR path supplied by the composing auditor

**Python review focus:**

- For implementation targets, do the changed Python files conform to loaded architecture decisions for dependency injection, no mocking, level accuracy, and test-double exception cases?
- For ADR targets, does `## Verification` (`### Audit`) include testability constraints (DI, no mocking)?
- Does the target use any mocking language anywhere (implementation, prose, or code examples)?
- Are execution levels accurate (SaaS services jump `l1` to `l3`, no `l2`)?
- Does any test-double usage document which `/test` exception case applies?
- Does the target contradict any ancestor ADR/PDR decision on a Python-architecture concern?

**Procedure:**

1. **Load the required standards first.** Proceed only after every prerequisite declaration above succeeds. Read repo-local `spx/local/python-architecture.md` if present; an overlay routes skill behavior to the product's governing specs and decisions and supplements skill behavior without declaring product truth.
2. **Read repo-local test overlay** `spx/local/python-tests.md` if present before judging level references or test-double exception cases.
3. **Read `/test`** for methodology (5 stages, 5 factors, 7 exceptions)
4. **Read the architecture target** completely: implementation files for implementation-auditor composition, or the ADR for adr-auditor composition
5. **Check testability constraints** — ADR targets express them in `## Verification` / `### Audit`; implementation targets must conform to the loaded architecture decisions' DI and no-mocking constraints
6. **Check for mocking language** — reject `unittest.mock.patch`, `respx.mock`, "mock at boundary" in any section, prose AND code examples
7. **Verify level accuracy** — SaaS services jump `l1` to `l3` (no `l2`)
8. **Check test double usage** — must document which `/test` exception case applies
9. **Check Python anti-patterns** — `src.*` import examples should use `<package>.*` / `<package>_testing.*`
10. **Identify all Python-architecture violations** and classify per concern
11. **Output the JSON verdict** with `overall` set to `APPROVED` or `REJECTED` and every concern row populated

</audit_workflow>

<principles_to_enforce>

All canonical conventions are in `/python-architecture-standards`. Read it first. This skill checks only the Python-specific concerns:

**1. Testability constraints** — ADR targets must include ALWAYS/NEVER rules under `## Verification` / `### Audit` that enable appropriate testing; implementation targets must comply with the loaded architecture decisions' testability constraints. See `<testability_in_verification>` in `/python-architecture-standards` for the correct ADR pattern. Level assignment tables are violations.

**2. Mocking prohibition** — No mocking language anywhere in the architecture target. See `<di_patterns>` in `/python-architecture-standards` for what to check and correct ADR language.

**3. Level accuracy** — When the architecture target references testing levels, verify against `/test` definitions. See `<level_context>` in `/python-architecture-standards`. Key rule: SaaS services (Trakt, GitHub API, Stripe, Auth0) jump `l1` to `l3` (no `l2`).

**4. Python anti-patterns** — Check for Python-specific architecture anti-patterns. See `<anti_patterns>` in `/python-architecture-standards`. Note Python-specific anti-pattern: `src.*` import examples should use `<package>.*` / `<package>_testing.*`.

**5. Test double exception cases** — Any test double usage must document which of the 7 `/test` Stage 5 exceptions applies. No exception = no doubles.

Section structure, atemporal voice, and per-rule tag validity are NOT this skill's concern — the composing `adr-auditor` owns them from the canonical template.

</principles_to_enforce>

<verdict_format>

Emit a structured verdict consumed by the composing verification workflow. The skill's entire output is the verdict payload. The composing workflow records findings, terminal state, and rendered projection through `spx verification run`.

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

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved ADR with "DI Protocol" but no testing strategy in Verification.** What happened: Claude approved a Protocol definition without a Verification rule requiring its use. Why it failed: a design element was mistaken for an enforceable testability constraint. How to avoid: require an ALWAYS rule that binds the Protocol to the relevant parameter boundary.

**Missed "respx.mock" in a code example.** What happened: Claude checked prose and missed mocking in a code block. Why it failed: the architecture screen did not cover the complete artifact. How to avoid: inspect prose and code examples for the same mocking prohibition.

**Accepted `l2` for a SaaS service.** What happened: Claude accepted local-infrastructure classification for a remote SaaS API. Why it failed: execution level was assigned from convenience instead of operational reality. How to avoid: apply the rule that remote SaaS services jump from `l1` to `l3`.

**Confused `sys.path` manipulation with a real import.** What happened: Claude accepted a fake module inserted through `sys.path` as a real dependency. Why it failed: import statements were inspected without runtime path manipulation. How to avoid: inspect `sys.path` and `importlib` behavior in architecture examples.

**Re-judged section structure or temporal voice.** What happened: Claude emitted structural or voice findings from the Python concern. Why it failed: generic ADR responsibilities were duplicated inside the language partition. How to avoid: leave template structure and atemporal voice to the composing `adr-auditor`.

</failure_modes>

<what_to_avoid>

**Don't:**

- Judge section structure, atemporal voice, or per-rule tag validity — those belong to the composing `adr-auditor`
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

<example_review>
Read `${SKILL_DIR}/references/example-audit.md` for a complete ADR-target `REJECTED` JSON verdict showing the Python concern types: SaaS `l2` violation, mocking language, and missing testability in `## Verification`.
</example_review>

<success_criteria>
The verdict is sound when:

- Every applicable Python architecture concern row is evaluated, with inapplicable concerns marked `NOT_APPLICABLE` and explained rather than skipped.
- `overall` is `REJECTED` when any concern row is `FAIL` and `APPROVED` when every concern row is `PASS` or explained `NOT_APPLICABLE`; missing required context produces a failing row and `REJECTED`.
- Each rejecting finding names the relevant implementation file or ADR path, violated rule and consequence in `message`, and concrete evidence in `observed` and `expected`.
- No finding judges generic ADR structure, atemporal voice, or per-rule tag validity.
- The same architecture scope and governing context produce the same JSON verdict.

</success_criteria>
