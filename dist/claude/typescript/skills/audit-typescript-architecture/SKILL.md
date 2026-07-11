---
name: audit-typescript-architecture
description: >-
  TypeScript-specific architecture audit — dependency injection, no-mocking, level accuracy — composed by generic artifact-type auditors for the TypeScript concerns in scope.
  Reached only through a dispatched auditor agent, never the main conversation.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

Invoke the `typescript:typescript-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<dispatch_gate>

This audit runs inside a dispatched artifact-type auditor's verifier context — `implementation-auditor` composing this skill for TypeScript implementation architecture scope, or `adr-auditor` composing it for a TypeScript ADR's language-specific architecture concerns — isolated from the author context that produced the work under audit. This skill judges only TypeScript-specific architecture concerns: dependency injection, no-mocking, execution-level accuracy, TypeScript anti-patterns, and ancestor consistency. Generic decision-record structure, atemporal voice, and tag validity are owned by the composing `adr-auditor` when the target is an ADR and are never judged here; a structural, voice, or tag finding from this skill is out of scope. When this skill loads in the author/main conversation rather than inside a dispatched auditor agent, STOP — the audit must run in that verifier context.

</dispatch_gate>

<objective>
A JSON verdict on a TypeScript architecture scope — `APPROVED`, or `REJECTED` with concern rows for dependency injection testability, mocking prohibition, execution-level accuracy, TypeScript anti-patterns, and ancestor consistency.
</objective>

<constraints>

- Read-only over the audited repository. Never edit files, stage changes, commit, or open pull requests.
- Produce only the JSON verdict described in `<verdict_format>`; finding messages state the violated rule and consequence, while corrective examples remain in references and standards.
- Judge only TypeScript-specific architecture concerns. Generic decision-record section structure, atemporal voice, and per-rule tag validity are owned by the composing artifact-type auditor when the target is an ADR.
- Treat `PASS | FAIL | NOT_APPLICABLE` as the only row vocabulary for this skill. The composing verification workflow maps the JSON verdict into the enclosing `spx verification run` projection.

</constraints>

<audit_workflow>
**For spec-tree work items: the composing auditor has already loaded the governing context.**

When this skill is composed for a spec-tree work item (enabler/outcome), the dispatching artifact-type auditor has already invoked `spec-tree:contextualize` on the node and loaded the complete governing context. Use that loaded context:

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Target node spec with typed assertions
- Implementation files, changed-file partition, or ADR path supplied by the composing auditor

**TypeScript review focus:**

- For implementation targets, do the changed TypeScript files conform to loaded architecture decisions for dependency injection, no mocking, and level accuracy?
- For ADR targets, does `## Verification` (`### Audit`) include testability constraints (DI, no mocking)?
- Does the target use mocking, stub, or fake language without tying any test double to a `/test` exception case?
- Are execution levels accurate (SaaS services jump `l1` to `l3`, no `l2`)?
- Does the target contradict any ancestor ADR/PDR decision on a TypeScript-architecture concern?

**Procedure:**

1. **Read `/typescript-architecture-standards`**, then `spx/local/typescript-architecture.md` if present, for canonical conventions
2. **Read repo-local test overlay** `spx/local/typescript-tests.md` if present before judging level references or test-double exception cases.
3. **Read the architecture target** completely: implementation files for implementation-auditor composition, or the ADR for adr-auditor composition
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

**Claude re-judged section structure and atemporal voice.** Claude flagged a phantom section and a temporal sentence. Why it failed: those concerns belong to the composing `adr-auditor` reading the canonical template, not this skill. How to avoid: drop any structural, voice, or tag finding — this skill judges only TypeScript-specific concerns.

</failure_modes>

<principles_to_enforce>

All canonical conventions are in `/typescript-architecture-standards`. Read it first. This skill checks only the TypeScript-specific concerns:

**1. Testability constraints** — ADR targets must include ALWAYS/NEVER rules under `## Verification` / `### Audit` that enable appropriate testing; implementation targets must comply with the loaded architecture decisions' testability constraints. See `<testability_in_verification>` in `/typescript-architecture-standards` for the correct ADR pattern. Level assignment tables are violations.

**2. Mocking prohibition** — No mocking language anywhere in the architecture target; reject "stub" or "fake" unless tied to a `/test` exception case. See `<di_patterns>` in `/typescript-architecture-standards` for what to check and correct ADR language.

**3. Level accuracy** — When the architecture target references testing levels, verify against `/test` definitions. See `<level_context>` in `/typescript-architecture-standards`. Key rule: SaaS services jump `l1` to `l3` (no `l2`).

**4. TypeScript anti-patterns** — Check for TypeScript-specific architecture anti-patterns. See `<anti_patterns>` in `/typescript-architecture-standards` for the full table.

Section structure, atemporal voice, and per-rule tag validity are NOT this skill's concern — the composing `adr-auditor` owns them from the canonical template.

</principles_to_enforce>

<verdict_format>

Emit a structured verdict consumed by the composing verification workflow. The skill's entire output is the verdict payload. The composing workflow records findings, terminal state, and rendered projection through `spx verification run`.

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

- Judge section structure, atemporal voice, or per-rule tag validity — those belong to the composing `adr-auditor`
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
