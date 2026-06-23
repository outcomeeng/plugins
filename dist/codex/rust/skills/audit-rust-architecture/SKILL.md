---
name: audit-rust-architecture
description: >-
  Rust-specific ADR architecture audit — dependency injection, no-mocking, level accuracy — composed by the generic adr-auditor agent for the Rust concerns in scope.
  Reached only through a dispatched auditor agent, never the main conversation.
---

Invoke the `rust:rust-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `rust:rust-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<dispatch_gate>

This audit runs inside a dispatched auditor's verifier context — the generic `adr-auditor` composing this skill for the Rust concerns in scope, or a generic `/audit`-family agent — isolated from the author context that produced the work under audit. This skill judges only Rust-specific concerns: dependency injection, no-mocking, and execution-level accuracy. Section structure, atemporal voice, and tag validity are owned by the composing `adr-auditor` reading the canonical template and are never judged here; a structural, voice, or tag finding from this skill is out of scope. When this skill loads in the author/main conversation rather than inside a dispatched auditor agent, STOP — the audit must run in that verifier context.

</dispatch_gate>

<objective>
A structured verdict on an ADR's Rust-specific architecture concerns — testability in Verification (dependency injection), the mocking prohibition, execution-level accuracy, and Rust anti-patterns.
</objective>

<context_loading>
When this skill is composed for a spec-tree work item, the dispatching `adr-auditor` has already invoked `spec-tree:contextualize` and loaded the full ADR/PDR hierarchy; review the target ADR's Rust concerns against that hierarchy.

After loading the shared Rust standards, check for `spx/local/rust.md`, `spx/local/rust-architecture.md`, and `spx/local/rust-tests.md` at the repository root. Read each file that exists and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</context_loading>

<process>

1. Read repo-local Rust overlays when present (`spx/local/rust.md`, `spx/local/rust-architecture.md`, `spx/local/rust-tests.md`)
2. Read the ADR completely, focusing on the Rust-specific concerns below
3. Check `## Verification` (`### Audit`) for real testability constraints and absence of level tables
4. Check for mocking language or invalid DI claims
5. Verify level accuracy when testing levels are mentioned
6. Check Rust anti-patterns
7. Check consistency with ancestor ADRs/PDRs when applicable
8. Output APPROVED or REJECTED with a concern table

</process>

<principles_to_enforce>

This skill checks only the Rust-specific concerns:

1. Testability in Verification (DI seams)
2. Mocking prohibition
3. Level accuracy when testing levels are mentioned
4. Rust anti-patterns
5. Ancestor consistency for spec-tree work

Section structure, atemporal voice, and per-rule tag validity are NOT this skill's concern — the composing `adr-auditor` owns them from the canonical template.

</principles_to_enforce>

<failure_modes>

**Claude approved a Compliance rule that named no falsifiable condition.** The rule used adjectives ("clean", "well-structured") with no concrete code pattern. Why it failed: an adjective-only rule passes a surface reading but cannot reject non-conforming code. How to avoid: require each Compliance rule to name a concrete code pattern, API call, or seam that triggers rejection.

**Claude flagged a DI parameter as dead code.** The parameter was unused in the example but required by a trait the seam exposes. Why it failed: Claude judged the parameter from the example alone, not the seam contract. How to avoid: before flagging an unused DI parameter, check whether a trait or downstream implementation requires it.

**Claude accepted "dependency injection" paired with a generated mock.** The ADR injected a `mockall` double as the controlled implementation. Why it failed: DI is the delivery mechanism, but a generated mock is still a mock. How to avoid: require DI to inject a controlled real implementation (a simple struct or function), not a mock framework double.

**Claude re-judged section structure and atemporal voice.** Claude flagged a phantom section and a temporal sentence. Why it failed: those concerns belong to the composing `adr-auditor` reading the canonical template, not this skill. How to avoid: drop any structural, voice, or tag finding — this skill judges only Rust-specific concerns.

</failure_modes>

<output_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "audit-rust-architecture",
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

Each finding's `rule` carries the violation pattern (e.g., `missing-testability`, `mocking-language`, `saas-l2`); `file` is the ADR path; `message` carries the one-line "why this fails". Include the correct-approach Rust sample and required-changes summary directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</output_format>

<example_reference>

Read `references/example-audit.md` for a complete rejected architecture review in Rust terms.

</example_reference>

<success_criteria>

- `/rust-standards` was read before `/rust-architecture-standards`
- repo-local Rust test overlays were applied to level accuracy checks
- `## Verification` (`### Audit`) contains real DI and no-mocking constraints
- mocking language and invalid DI claims were rejected
- Rust anti-patterns were checked
- section structure, atemporal voice, and tag validity were NOT judged — those are the composing adr-auditor's concern
- the verdict is structured and binary

</success_criteria>
