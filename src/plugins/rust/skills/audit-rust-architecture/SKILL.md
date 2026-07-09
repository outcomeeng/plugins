---
name: audit-rust-architecture
description: >-
  Rust-specific architecture audit — dependency injection, no-mocking, level accuracy — composed by generic artifact-type auditors for the Rust concerns in scope.
  Reached only through a dispatched auditor agent, never the main conversation.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

{!% require_skill 'rust:rust-standards' %!}

{!% require_skill 'rust:rust-architecture-standards' %!}

<dispatch_gate>

This audit runs inside a dispatched artifact-type auditor's verifier context — `implementation-auditor` composing this skill for Rust implementation architecture scope, or `adr-auditor` composing it for a Rust ADR's language-specific architecture concerns — isolated from the author context that produced the work under audit. This skill judges only Rust-specific architecture concerns: dependency injection, no-mocking, execution-level accuracy, Rust anti-patterns, and ancestor consistency. Generic decision-record structure, atemporal voice, and tag validity are owned by the composing `adr-auditor` when the target is an ADR and are never judged here; a structural, voice, or tag finding from this skill is out of scope. When this skill loads in the author/main conversation rather than inside a dispatched auditor agent, STOP — the audit must run in that verifier context.

</dispatch_gate>

<objective>
A JSON verdict on a Rust architecture scope — implementation architecture or ADR language concerns — with concern rows for dependency injection testability, mocking prohibition, execution-level accuracy, Rust anti-patterns, and ancestor consistency.
</objective>

<constraints>

- Read-only over the audited repository. Never edit files, stage changes, commit, or open pull requests.
- Produce only the JSON verdict described in `<verdict_format>`; fixes and prose remediation belong in finding messages, not in repository mutations.
- Judge only Rust-specific architecture concerns. Generic decision-record section structure, atemporal voice, and per-rule tag validity are owned by the composing artifact-type auditor when the target is an ADR.
- Treat `PASS | FAIL | UNKNOWN` as the only verdict vocabulary for this skill. The composing verification workflow maps the JSON verdict into the enclosing `spx verification run` projection.

</constraints>

<audit_workflow>
When this skill is composed for a spec-tree work item, the dispatching artifact-type auditor has already invoked `spec-tree:contextualize` and loaded the full governing context; review the target implementation architecture scope or ADR's Rust concerns against that hierarchy.

After loading the shared Rust standards, check for `spx/local/rust.md`, `spx/local/rust-architecture.md`, and `spx/local/rust-tests.md` at the repository root. Read each file that exists and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.

**Procedure:**

1. Read repo-local Rust overlays when present (`spx/local/rust.md`, `spx/local/rust-architecture.md`, `spx/local/rust-tests.md`)
2. Read the architecture target completely: implementation files for implementation-auditor composition, or the ADR for adr-auditor composition
3. Check testability constraints — ADR targets express them in `## Verification` / `### Audit`; implementation targets must conform to the loaded architecture decisions' DI and no-mocking constraints
4. Check for mocking language or invalid DI claims
5. Verify level accuracy when testing levels are mentioned
6. Check Rust anti-patterns
7. Check consistency with ancestor ADRs/PDRs when applicable
8. Output the JSON verdict with `overall` set to `PASS`, `FAIL`, or `UNKNOWN` and every concern row populated

</audit_workflow>

<principles_to_enforce>

This skill checks only the Rust-specific concerns:

1. Testability constraints: ADR targets express DI seams in `## Verification` / `### Audit`; implementation targets conform to loaded architecture decisions.
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

<verdict_format>

Emit a structured verdict consumed by the composing verification workflow. The skill's entire output is the verdict payload. The composing workflow records findings, terminal state, and rendered projection through `spx verification run`.

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "audit-rust-architecture",
  "target": "<architecture-scope>",
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

Each finding's `rule` carries the violation pattern (e.g., `missing-testability`, `mocking-language`, `saas-l2`); `file` is the relevant implementation file or ADR path; `message` carries the one-line "why this fails". Include the correct-approach Rust sample and required-changes summary directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</verdict_format>

<example_reference>

Read `${CLAUDE_SKILL_DIR}/references/example-audit.md` for a complete rejected architecture review in Rust terms.

</example_reference>

<success_criteria>

The verdict is sound when:

- Every applicable Rust architecture concern row is evaluated, with inapplicable concerns marked `UNKNOWN` rather than skipped.
- `overall` is `FAIL` when any concern row is `FAIL`, `PASS` when every concern row is `PASS` or `UNKNOWN`, and `UNKNOWN` only when missing context prevents a definitive judgment.
- Each rejecting finding names the relevant implementation file or ADR path, violated rule, evidence, and required correction in the JSON `message`.
- No finding judges generic ADR structure, atemporal voice, or per-rule tag validity.
- The same architecture scope and governing context produce the same JSON verdict.

</success_criteria>
