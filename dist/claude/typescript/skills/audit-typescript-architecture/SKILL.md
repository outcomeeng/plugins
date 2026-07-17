---
name: audit-typescript-architecture
description: >-
  TypeScript-specific architecture audit — judges the TypeScript architecture
  target in scope for dependency injection, mocking prohibition, execution-level
  accuracy, TypeScript anti-patterns, and ancestor consistency.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash, Skill
---

Invoke the `typescript:typescript-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A JSON verdict on a TypeScript architecture scope — `APPROVED`, or `REJECTED` with concern rows for dependency injection testability, mocking prohibition, execution-level accuracy, TypeScript anti-patterns, and ancestor consistency.
</objective>

<constraints>

- Read-only over the audited repository. Never edit files, stage changes, commit, or open pull requests.
- Produce only the JSON verdict described in `<verdict_format>`; finding messages state the violated rule and consequence, while corrective examples remain in references and standards.
- Judge only TypeScript-specific architecture concerns: dependency injection, no-mocking, execution-level accuracy, TypeScript anti-patterns, and ancestor consistency. Generic decision-record section structure, atemporal voice, and per-rule tag validity are outside this subject — a structural, voice, or tag finding is out of scope even when the target is an ADR.
- Treat `PASS | FAIL | NOT_APPLICABLE` as the only row vocabulary for this skill.

</constraints>

<audit_workflow>
**Inputs.** This audit judges the target it is given, against the governing context already loaded when it runs:

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Target node spec with typed assertions
- The architecture target: implementation files, a changed-file partition, or an ADR path

**TypeScript review focus:**

- For implementation targets, do the changed TypeScript files conform to loaded architecture decisions for dependency injection, no mocking, and level accuracy?
- For ADR targets, does `## Verification` (`### Audit`) include testability constraints (DI, no mocking)?
- Does the target use mocking, stub, or fake language without tying any test double to a `/test` exception case?
- Are execution levels accurate (SaaS services jump `l1` to `l3`, no `l2`)?
- Does the target contradict any ancestor ADR/PDR decision on a TypeScript-architecture concern?

**Procedure:**

1. **Read `/typescript-architecture-standards`**, then `spx/local/typescript-architecture.md` if present, for canonical conventions
2. **Read repo-local test overlay** `spx/local/typescript-tests.md` if present before judging level references or test-double exception cases.
3. **Read the architecture target** completely — the implementation files or the ADR supplied as the target
4. **Check testability constraints** — ADR targets express them in `## Verification` / `### Audit`; implementation targets must conform to the loaded architecture decisions' DI and no-mocking constraints
5. **Check for mocking and unjustified test-double language** — reject `vi.mock()`, `jest.mock()`, "mock at boundary", or "stub"/"fake" without a `/test` exception case in any section, prose AND code examples
6. **Verify level accuracy** — SaaS services jump `l1` to `l3` (no `l2`)
7. **Check TypeScript anti-patterns** — architecture target content that violates `<anti_patterns>`
8. **Identify all TypeScript-architecture violations** and classify per concern
9. **Output the JSON verdict** with `overall` set to `APPROVED` or `REJECTED` and every concern row populated

</audit_workflow>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Claude approved a Verification rule that cannot falsify non-conforming code.** The ADR mandated DI for all external calls, but the Verification rules were so vague ("use good practices") that they couldn't catch anything. Why it failed: a rule that cannot reject a violating example is not a rule. How to avoid: require each Verification rule to name a concrete pattern a test or review can falsify.

**Claude rejected an ADR for a false positive.** Claude flagged a parameter in a DI interface as "dead code" because it wasn't used in the example. Why it failed: the parameter was required by an interface contract other implementations rely on. How to avoid: before flagging a dead parameter in an interface, check whether the interface is implemented elsewhere.

**Claude missed mocking hidden behind DI.** The ADR said "dependency injection" but injected `vi.fn()` as the controlled implementation. Why it failed: DI is the delivery mechanism, but `vi.fn()` is still a mock. How to avoid: require DI to inject a controlled *real* implementation (a simple function or object), not a mock framework spy.

**Claude accepted `l2` for a SaaS service.** Why it failed: SaaS services cannot run locally — there is no `l2`; they jump `l1` to `l3`. How to avoid: reject `l2` whenever the dependency is a SaaS API.

**Claude re-judged section structure and atemporal voice.** Claude flagged a phantom section and a temporal sentence. Why it failed: those concerns are judged against the canonical decision template, outside this skill's subject. How to avoid: drop any structural, voice, or tag finding — this skill judges only TypeScript-specific concerns.

</failure_modes>

<principles_to_enforce>

All canonical conventions are in `/typescript-architecture-standards`. Read it first. This skill checks only the TypeScript-specific concerns:

**1. Testability constraints** — ADR targets must include ALWAYS/NEVER rules under `## Verification` / `### Audit` that enable appropriate testing; implementation targets must comply with the loaded architecture decisions' testability constraints. See `<testability_in_verification>` in `/typescript-architecture-standards` for the correct ADR pattern. Level assignment tables are violations.

**2. Mocking prohibition** — No mocking language anywhere in the architecture target; reject "stub" or "fake" unless tied to a `/test` exception case. See `<di_patterns>` in `/typescript-architecture-standards` for what to check and correct ADR language.

**3. Level accuracy** — When the architecture target references testing levels, verify against `/test` definitions. See `<level_context>` in `/typescript-architecture-standards`. Key rule: SaaS services jump `l1` to `l3` (no `l2`).

**4. TypeScript anti-patterns** — Check for TypeScript-specific architecture anti-patterns. See `<anti_patterns>` in `/typescript-architecture-standards` for the full table.

Section structure, atemporal voice, and per-rule tag validity are NOT this skill's concern — they are judged against the canonical decision template, outside this TypeScript-architecture subject.

</principles_to_enforce>

<verdict_format>

Emit a structured verdict. The skill's entire output is the verdict payload.

The skill's `overall` is `APPROVED` iff every concern row is `PASS` or `NOT_APPLICABLE`; it is `REJECTED` if any concern is `FAIL`. Every `NOT_APPLICABLE` row explains why its concern does not apply. An unavailable required inspection is `FAIL`, never `NOT_APPLICABLE`. Findings use severity `blocking` or `debt`.

```json
{
  "schema_version": 1,
  "skill": "audit-typescript-architecture",
  "target": "<architecture-scope>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    { "name": "testability-in-verification", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "mocking-prohibition", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "level-accuracy", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "anti-patterns", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "ancestor-consistency", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` field carries the violation pattern (e.g., `missing-testability`, `mocking-language`, `saas-l2`); `file` is the relevant implementation file or ADR path; `message` carries the one-line violated rule and consequence, while `observed` and `expected` carry the evidence. Corrective examples and remediation narrative stay in the referenced example and standards files rather than the verdict.

</verdict_format>

<what_to_avoid>

**Don't:**

- Judge section structure, atemporal voice, or per-rule tag validity — those are outside this skill's TypeScript-architecture subject
- Reference specific line numbers (they change) — use section names or quoted text
- Provide grep commands — focus on principles, not tooling
- Approve an architecture target just because a Protocol is defined — check that an ALWAYS rule mandates it for ADR targets or that implementation code follows the loaded architecture constraint

**Do:**

- Reference `/typescript-architecture-standards` section names (e.g., `<testability_in_verification>`, `<di_patterns>`)
- Reference `/test` methodology by its real heading, `Stage 2: At what level does that evidence live?`, for level rules
- Keep corrective architecture examples in the referenced standards and example files, never in the emitted verdict
- Be direct about violations

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-audit.md` for a complete ADR-target `REJECTED` JSON verdict showing the TypeScript concern types: missing testability in `## Verification`, mocking language, unjustified test-double language, and SaaS `l2` violation.
</example_review>

<success_criteria>
The verdict is sound when:

- Every applicable TypeScript architecture concern row is evaluated, with inapplicable concerns marked `NOT_APPLICABLE` and explained rather than skipped.
- `overall` is `REJECTED` when any concern row is `FAIL` and `APPROVED` when every concern row is `PASS` or explained `NOT_APPLICABLE`; missing required context produces a failing row and `REJECTED`.
- Each rejecting finding names the relevant implementation file or ADR path, violated rule and consequence in `message`, and concrete evidence in `observed` and `expected`.
- No finding judges generic ADR structure, atemporal voice, or per-rule tag validity.
- The same architecture scope and governing context produce the same JSON verdict.

</success_criteria>
