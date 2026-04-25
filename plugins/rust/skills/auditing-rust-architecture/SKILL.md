---
name: auditing-rust-architecture
description: ALWAYS invoke this skill when auditing ADRs for Rust or after writing an ADR. NEVER implement from an unaudited ADR.
allowed-tools: Read, Grep, Glob, Bash
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust/SKILL.md"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust-architecture/SKILL.md"`

<objective>
Review ADRs against `/standardizing-rust`, `/standardizing-rust-architecture`, `/testing` principles, atemporal voice rules, and applicable PDR constraints. Produce a structured verdict per concern. This skill is read-only.

Read `/standardizing-rust`, then `/standardizing-rust-architecture`, before reviewing any ADR.
</objective>

<context_loading>
For spec-tree work items, load full ADR/PDR hierarchy first with `spec-tree:contextualizing`, then review the target ADR against that hierarchy.

After loading the shared Rust standards, check for `spx/local/rust.md`, `spx/local/rust-architecture.md`, and `spx/local/rust-tests.md` at the repository root. Read each file that exists and enforce it as the repo-local specialization.
</context_loading>

<process>

1. Read `/standardizing-rust`, then `/standardizing-rust-architecture`
2. Read repo-local Rust, Rust architecture, and Rust test overlays when present
3. Verify an ADR exists for any real architectural choice
4. Read the ADR completely
5. Check section structure against the authoritative ADR template
6. Check every section for temporal language
7. Check Compliance for real testability constraints and absence of level tables
8. Check for mocking language or invalid DI claims
9. Check consistency with ancestor ADRs/PDRs when applicable
10. Output APPROVED or REJECTED with a concern table

</process>

<principles_to_enforce>

1. Section structure
2. Testability in Compliance
3. Atemporal voice
4. Mocking prohibition
5. Level accuracy when testing levels are mentioned
6. Anti-patterns
7. Ancestor consistency for spec-tree work

</principles_to_enforce>

<failure_modes>

- Vague Compliance rules that cannot falsify non-conforming code
- False positives on DI parameters that belong to a real seam
- "Dependency injection" paired with generated mocks
- Temporal rationale that narrates decision history
- Phantom sections removed without moving testability constraints into Compliance

</failure_modes>

<output_format>

````markdown
ARCHITECTURE REVIEW

**Decision:** [APPROVED | REJECTED]

Verdict

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

Violations

Violation: {Violation name}

**Where:** {section or quoted text}
**Concern:** {concern name}
**Why this fails:** {direct explanation}

**Correct approach:**

```rust
{show the architectural shape or ADR wording that would conform}
```

---

Required Changes

{concise list}

---

References

- /standardizing-rust-architecture: {section name}
- /standardizing-rust: {section name if applicable}
- /testing: {section name if applicable}

---

{If REJECTED: "Revise and resubmit."}
{If APPROVED: "Architecture meets standards."}
````

</output_format>

<example_reference>

Read `references/example-review.md` for a complete rejected architecture review in Rust terms.

</example_reference>

<success_criteria>

- `/standardizing-rust` was read before `/standardizing-rust-architecture`
- repo-local Rust test overlays were applied to level accuracy checks
- every ADR section was checked for temporal language
- Compliance contains real DI and no-mocking constraints
- phantom sections were rejected
- the verdict is structured and binary

</success_criteria>
