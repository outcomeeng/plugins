---
name: audit-typescript-architecture
description: >-
  TypeScript-specific ADR architecture audit — dependency injection, no-mocking, level accuracy — composed by the generic adr-auditor agent for the TypeScript concerns in scope.
  Reached only through a dispatched auditor agent, never the main conversation.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

Invoke the `typescript:typescript-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<dispatch_gate>

This audit runs inside a dispatched auditor's verifier context — the generic `adr-auditor` composing this skill for the TypeScript concerns in scope, or a generic `/audit`-family agent — isolated from the author context that produced the work under audit. This skill judges only TypeScript-specific concerns: dependency injection, no-mocking, and execution-level accuracy. Section structure, atemporal voice, and tag validity are owned by the composing `adr-auditor` reading the canonical template and are never judged here; a structural, voice, or tag finding from this skill is out of scope. When this skill loads in the author/main conversation rather than inside a dispatched auditor agent, STOP — the audit must run in that verifier context.

</dispatch_gate>

<objective>
A structured verdict on an ADR's TypeScript-specific architecture concerns — testability in Verification (dependency injection), the mocking prohibition, execution-level accuracy, and TypeScript anti-patterns.
</objective>

<context_loading>
**For spec-tree work items: the composing auditor has already loaded the ADR/PDR hierarchy.**

When this skill is composed for a spec-tree work item (enabler/outcome), the dispatching `adr-auditor` has already invoked `spec-tree:contextualize` on the node and loaded the complete ADR/PDR hierarchy. Use that loaded context:

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Target node spec with typed assertions

**TypeScript review focus:**

- Does the ADR's `## Verification` (`### Audit`) include testability constraints (DI, no mocking)?
- Does the ADR use any mocking language anywhere (prose or code examples)?
- Are execution levels accurate (SaaS services jump `l1` to `l3`, no `l2`)?
- Does the ADR contradict any ancestor ADR/PDR decision on a TypeScript-architecture concern?

</context_loading>

<process>

1. **Read `/typescript-architecture-standards`**, then `spx/local/typescript-architecture.md` if present, for canonical conventions
2. **Read the ADR** completely, focusing on the TypeScript-specific concerns below
3. **Check `## Verification`** — must include testability constraints as ALWAYS/NEVER rules under `### Audit`; must NOT include level assignment tables
4. **Check for mocking language** — reject `vi.mock()`, `jest.mock()`, "mock at boundary" in any section, prose AND code examples
5. **Verify level accuracy** — SaaS services jump `l1` to `l3` (no `l2`)
6. **Check TypeScript anti-patterns** — content that does not belong in an ADR per `<anti_patterns>`
7. **Identify all TypeScript-architecture violations** and classify per concern
8. **Output structured verdict** — APPROVED or REJECTED with per-concern table

</process>

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

**1. Testability in Verification** — The `## Verification` section must include ALWAYS/NEVER rules under `### Audit` that enable appropriate testing. See `<testability_in_verification>` in `/typescript-architecture-standards` for the correct pattern. Level assignment tables are violations.

**2. Mocking prohibition** — No mocking language anywhere in the ADR. See `<di_patterns>` in `/typescript-architecture-standards` for what to check and correct ADR language.

**3. Level accuracy** — When the `## Verification` rules reference testing levels, verify against `/test` definitions. See `<level_context>` in `/typescript-architecture-standards`. Key rule: SaaS services jump `l1` to `l3` (no `l2`).

**4. TypeScript anti-patterns** — Check for content that does not belong in an ADR. See `<anti_patterns>` in `/typescript-architecture-standards` for the full table.

Section structure, atemporal voice, and per-rule tag validity are NOT this skill's concern — the composing `adr-auditor` owns them from the canonical template.

</principles_to_enforce>

<output_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "audit-typescript-architecture",
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

Each finding's `rule` field carries the violation pattern (e.g., `missing-testability`, `mocking-language`, `saas-l2`); `file` is the ADR path; `message` carries the one-line "why this fails". Include the correct-approach code sample and required-changes summary directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</output_format>

<what_to_avoid>

**Don't:**

- Judge section structure, atemporal voice, or per-rule tag validity — those belong to the composing `adr-auditor`
- Reference specific line numbers (they change) — use section names or quoted text
- Provide grep commands — focus on principles, not tooling
- Approve an ADR just because a Protocol is defined — check that an ALWAYS rule mandates it

**Do:**

- Reference `/typescript-architecture-standards` section names (e.g., `<testability_in_verification>`, `<di_patterns>`)
- Reference `/test` section names for level rules (e.g., "Stage 2 Five Factors")
- Show correct architecture with code or markdown examples
- Be direct about violations

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-audit.md` for a complete REJECTED review showing the TypeScript concern types: missing testability in `## Verification`, mocking language, and SaaS `l2` violation.
</example_review>

<success_criteria>
Review is complete when:

- [ ] Read `/typescript-architecture-standards` and `spx/local/typescript-architecture.md` (if present) before starting review
- [ ] Verified `## Verification` includes testability constraints (ALWAYS/NEVER for DI, no mocking)
- [ ] Verified no mocking language anywhere in ADR (prose AND code examples)
- [ ] Verified level assignments — no `l2` for SaaS services
- [ ] Verified TypeScript anti-patterns
- [ ] Did NOT judge section structure, atemporal voice, or tag validity — those are the composing adr-auditor's concern
- [ ] Structured verdict table with per-concern status
- [ ] Correct approach shown with code examples for each violation
- [ ] Decision clearly stated (APPROVED/REJECTED)

</success_criteria>
