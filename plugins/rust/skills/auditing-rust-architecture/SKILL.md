---
name: auditing-rust-architecture
description: ALWAYS invoke this skill when auditing ADRs for Rust or after writing an ADR. NEVER implement from an unaudited ADR.
allowed-tools: Read, Grep, Glob, Bash
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust/SKILL.md" || echo "standardizing-rust not found — invoke rust:standardizing-rust manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust-architecture/SKILL.md" || echo "standardizing-rust-architecture not found — invoke rust:standardizing-rust-architecture manually"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. `rust:standardizing-rust`
2. `rust:standardizing-rust-architecture`

</codex_fallback>

<objective>
Review ADRs against `/standardizing-rust`, `/standardizing-rust-architecture`, `/testing` principles, atemporal voice rules, and applicable PDR constraints. Produce a structured verdict per concern. This skill is read-only.

**Standards are pre-loaded above.**
</objective>

<context_loading>
For spec-tree work items, load full ADR/PDR hierarchy first with `spec-tree:contextualizing`, then review the target ADR against that hierarchy.

After loading the shared Rust standards, check for `spx/local/rust.md`, `spx/local/rust-architecture.md`, and `spx/local/rust-tests.md` at the repository root. Read each file that exists and enforce it as the repo-local specialization.
</context_loading>

<process>

1. Read repo-local Rust overlays when present (`spx/local/rust.md`, `spx/local/rust-architecture.md`, `spx/local/rust-tests.md`)
2. Verify an ADR exists for any real architectural choice
3. Read the ADR completely
4. Check section structure against the authoritative ADR template
5. Check every section for temporal language
6. Check Compliance for real testability constraints and absence of level tables
7. Check for mocking language or invalid DI claims
8. Check consistency with ancestor ADRs/PDRs when applicable
9. Output APPROVED or REJECTED with a concern table

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

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/auditing/scripts/verdict.py`. Write the JSON to stdout; the calling workflow pipes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `reject` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "auditing-rust-architecture",
  "target": "<adr-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "section-structure", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "testability-in-compliance", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "mocking-prohibition", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "level-accuracy", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "anti-patterns", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "ancestor-consistency", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` carries the violation pattern (e.g., `phantom-section`, `temporal-voice`); `file` is the ADR path; `message` carries the one-line "why this fails". Include the correct-approach Rust sample and required-changes summary in supplementary markdown appended after the carrier when format is `markdown` or `markdown+json`.

</output_format>

<example_reference>

Read `references/example-audit.md` for a complete rejected architecture review in Rust terms.

</example_reference>

<success_criteria>

- `/standardizing-rust` was read before `/standardizing-rust-architecture`
- repo-local Rust test overlays were applied to level accuracy checks
- every ADR section was checked for temporal language
- Compliance contains real DI and no-mocking constraints
- phantom sections were rejected
- the verdict is structured and binary

</success_criteria>
