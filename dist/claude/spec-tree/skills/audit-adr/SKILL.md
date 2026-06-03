---
name: audit-adr
description: ALWAYS use when auditing an ADR or after making changes to an ADR
allowed-tools: Read, Grep, Glob, Bash
---

<objective>

Audit an ADR for its structure, atemporal voice, and strict conformance to the ADR evidence model.

Language-specific ADR concerns — testability-in-Compliance (dependency injection, no-mocking), execution-level accuracy — stay in `/auditing-{lang}-architecture`, not here.

</objective>

<essential_principles>

**ARCHITECTURE BY DEFINITION.**

An ADR's content is architecture — technology choices, data structures, implementation approaches. NEVER classify ADR content as product-behavior-versus-architecture; that classification is the PDR audit's concern. Audit the ADR's form, not whether its content belongs elsewhere.

**TAG VALIDITY IS PRESENCE, NOT RE-DERIVATION.**

Each rule under `## Verification` carries one tag matching its subsection — `### Testing` → an evidence type (scenario, mapping, conformance, property, compliance) chosen via `/testing`; `### Eval` → `[eval]`; `### Audit` → `[audit]`. Verify the tag is present and agrees with its subsection. NEVER re-derive a Testing rule's evidence type — that is `/testing`'s authority. A missing tag, a bare mechanism tag (`[review]`/`[test]`) in place of an evidence type, a tag disagreeing with its subsection, or more than one tag is a finding.

**ATEMPORAL VOICE.**

ADRs state architecture truth. "The build emits one wheel per plugin" — not "We switched to per-plugin wheels because the monolith broke."

**BINARY VERDICT.**

`APPROVED` or `REJECT`. No middle ground.

</essential_principles>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualizing` on the directory containing the ADR.

Do not proceed if you do not see the `<SPEC_TREE_CONTEXT>` marker for the ADR directory.

</step>

<step name="read_adr">

**Step 2: Read the ADR**

Read the ADR under audit. Identify its sections: the opening decision statement, Rationale (optional), Invariants (optional), and Verification.

</step>

<step name="audit_structure">

**Step 3: Section structure**

Verify the decision is stated in the opening (no "Purpose" preamble) and a `## Verification` section is present. Rationale and Invariants are optional — Invariants appears only when the decision establishes algebraic properties.

**No decision statement, or no Verification section → REJECT — "missing-section."**

</step>

<step name="audit_voice">

**Step 4: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (REJECT)                     | Atemporal (correct)             |
| ------------------------------------- | ------------------------------- |
| "We decided to use X because Y broke" | "X governs Z"                   |
| "Currently the build does X"          | "The build does X"              |
| "After profiling, we added caching"   | "Caching reduces latency for Z" |

**Any temporal language in any section → REJECT — "temporal-voice."**

</step>

<step name="audit_tag_validity">

**Step 5: Per-rule tag validity**

Rules live under `## Verification`, grouped into `### Testing`, `### Eval`, and `### Audit` subsections by verification type. For each rule, the tag is valid for its subsection:

- under `### Testing` → one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
- under `### Eval` → `([eval])`;
- under `### Audit` → `([audit])`.

A bare mechanism tag (`([review])`/`([test])`), a tag that disagrees with its subsection, a missing tag, or more than one tag is invalid. Do not re-derive the evidence type — only validate the tag against its subsection.

**A rule with no subsection tag, a tag disagreeing with its subsection, a bare mechanism tag in place of an evidence type, or more than one tag → REJECT — "invalid-mode-tag."**

</step>

<step name="verdict">

**Step 6: Issue verdict**

Scan all findings. If any property fails: REJECT. Otherwise: APPROVED.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/auditing/scripts/verdict.py`. The skill's entire output is the JSON verdict. The calling agent or orchestrator routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The `overall` is `PASS` iff every property row is `PASS`; `FAIL` if any row is `FAIL`; `UNKNOWN` if a property cannot be evaluated. Findings carry severity `REJECT` for blocking violations and `WARNING`/`INFO` otherwise.

```json
{
  "schema_version": 1,
  "skill": "audit-adr",
  "target": "<adr-file-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "section-structure", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "mode-validity", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` field carries the violation pattern (`missing-section`, `temporal-voice`, `invalid-mode-tag`); the `message` field carries the one-line detail.

</verdict_format>

<failure_modes>

**Failure 1: Imported the PDR content gate into an ADR audit**

Claude flagged "uses PostgreSQL with row-level locking" as architecture content that does not belong — in an ADR. An ADR's content is architecture by definition; there is no product-versus-architecture classification to run. The PDR audit's content gate has no place here.

How to avoid: The ADR audit checks form — structure, voice, tag validity. Content classification is the PDR audit's concern only.

**Failure 2: Re-derived a Testing rule's evidence type**

Claude saw a `### Testing` rule tagged `([scenario])`, judged it should be `[property]` because the rule read like an invariant, and rejected it. Evidence-type selection is `/testing`'s authority, exercised when the rule is authored. The audit validates that a tag is present and names one of the five evidence types — it does not second-guess the choice.

How to avoid: Step 5 validates tag presence and subsection agreement only. A present, valid evidence-type tag passes regardless of which evidence type the auditor would have picked.

</failure_modes>

<success_criteria>

Audit is complete when:

- [ ] `/contextualizing` invoked — `<SPEC_TREE_CONTEXT>` marker present
- [ ] ADR read — all sections identified
- [ ] Section structure: decision stated in the opening and `## Verification` present
- [ ] Atemporal voice: every section checked for temporal language
- [ ] Per-rule tag validity: each rule's tag validated against its Verification subsection (Testing → one of the five evidence types, Eval → `[eval]`, Audit → `[audit]`)
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has property, category, and detail

</success_criteria>
