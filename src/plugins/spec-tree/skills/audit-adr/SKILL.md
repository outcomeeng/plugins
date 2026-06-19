---
name: audit-adr
description: >-
  ADR audit methodology preloaded by the adr-auditor agent. Dispatch adr-auditor
  to audit an ADR; the main conversation reaches this audit only through that agent.
allowed-tools: Read, Grep, Glob, Bash
---

<dispatch_gate>

This audit runs in the adr-auditor agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch the adr-auditor agent instead of running this audit here. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

Audit an ADR for its structure, atemporal voice, and strict conformance to the ADR evidence model.

Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — stay in `/audit-{lang}-architecture`, not here.

</objective>

<essential_principles>

**ARCHITECTURE BY DEFINITION.**

An ADR's content is architecture — technology choices, data structures, implementation approaches. NEVER classify ADR content as product-behavior-versus-architecture; that classification is the PDR audit's concern. Audit the ADR's form, not whether its content belongs elsewhere.

**EVIDENCE TYPE MUST MATCH THE CLAIM.**

Each rule under `## Verification` carries one tag matching its subsection — `### Testing` → an evidence type (scenario, mapping, conformance, property, compliance); `### Eval` → `[eval]`; `### Audit` → `[audit]`. `/test` selects the type; this audit verifies the selection is correct against the claim's shape — an audit that accepts any present tag verifies nothing, and the evidence type is the assertion's whole worth. The decisive check is the quantifier: a universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") is never `scenario`, because a scenario proves one case and cannot establish a claim about every case; `scenario` fits only a single existential interaction. A missing tag, a bare mechanism tag (`[review]`/`[test]`), a tag disagreeing with its subsection, more than one tag, or an evidence type the `/test` router would not produce for the claim is a finding.

**ATEMPORAL VOICE.**

ADRs state architecture truth. "The build emits one wheel per plugin" — not "We switched to per-plugin wheels because the monolith broke."

**BINARY VERDICT.**

`APPROVED` or `REJECT`. No middle ground.

</essential_principles>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualize` on the directory containing the ADR.

Do not proceed without the `<SPEC_TREE_CONTEXT>` marker for the ADR directory.

</step>

<step name="read_adr">

**Step 2: Read the ADR**

Read the ADR under audit. Identify its sections: the opening decision statement, Rationale (optional), Invariants (optional), and Verification.

</step>

<step name="audit_structure">

**Step 3: Section structure**

Read the canonical ADR template at `${CLAUDE_SKILL_DIR}/../understand/templates/decisions/decision-name.adr.md` and derive the valid section set from it in full — never from memory or a transcribed copy. A structural finding that contradicts the canonical template is unbacked: drop it rather than rejecting the ADR. If the template cannot be read, report the section-structure property as UNKNOWN — "template-missing" — and issue no structural finding.

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

**Step 5: Per-rule tag validity and evidence-type fit**

Rules live under `## Verification`, grouped into `### Testing`, `### Eval`, and `### Audit` subsections by verification type. For each rule:

1. The tag is valid for its subsection:
   - under `### Testing` → one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])`;
   - under `### Audit` → `([audit])`.
2. Under `### Testing`, the evidence type fits the claim's shape per the `/test` router. Read the claim's quantifier: a universal (ALWAYS / NEVER / "for all" / "for every" / "no input") takes `mapping`, `conformance`, `compliance`, or `property` — never `scenario`; a single existential interaction takes `scenario`. Within the universal branch the router yields one type by domain shape (finite source-owned → `mapping`; external/internal contract → `conformance`; rule exercised against violating cases → `compliance`; open or infinite → `property`). Reject a type the router would not produce for the claim; do not relitigate a choice the router leaves open between equally-valid types.

A bare mechanism tag (`([review])`/`([test])`), a tag disagreeing with its subsection, a missing tag, more than one tag, or an evidence type that contradicts the claim's shape (a universal tagged `scenario` is the clearest case) is invalid.

**A rule with no subsection tag, a tag disagreeing with its subsection, a bare mechanism tag in place of an evidence type, or more than one tag → REJECT — "invalid-tag." An evidence type that contradicts the claim's shape → REJECT — "evidence-type-mismatch."**

</step>

<step name="verdict">

**Step 6: Issue verdict**

Scan all findings. If any property fails: REJECT. Otherwise: APPROVED.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

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
    { "name": "tag-validity", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` field carries the violation pattern (`missing-section`, `temporal-voice`, `invalid-tag`, `evidence-type-mismatch`); the `message` field carries the one-line detail.

</verdict_format>

<failure_modes>

**Failure 1: Imported the PDR content gate into an ADR audit**

Claude flagged "uses PostgreSQL with row-level locking" as architecture content that does not belong — in an ADR. An ADR's content is architecture by definition; there is no product-versus-architecture classification to run. The PDR audit's content gate has no place here.

How to avoid: The ADR audit checks form — structure, voice, tag validity. Content classification is the PDR audit's concern only.

**Failure 2: Passed a universal rule tagged `scenario`**

Claude saw a `### Testing` rule — a universal ALWAYS/NEVER claim — tagged `([scenario])`, and passed it because a tag was present and named one of the five evidence types. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified — phantom green. The quantifier mismatch is a deterministic error, not a matter of taste.

How to avoid: Step 5 verifies the evidence type fits the claim's shape per the `/test` router. Reject a universal tagged `scenario` (and any type the router would not produce for the claim). The one line the audit does not cross is relitigating a choice the router leaves open between equally-valid types — that, and only that, is `/test`'s to decide.

</failure_modes>

<success_criteria>

Audit is complete when:

- [ ] `/contextualize` invoked — `<SPEC_TREE_CONTEXT>` marker present
- [ ] ADR read — all sections identified
- [ ] Section structure: decision stated in the opening and `## Verification` present
- [ ] Atemporal voice: every section checked for temporal language
- [ ] Per-rule tag validity and evidence-type fit: each rule's tag validated against its Verification subsection (Testing → one of the five evidence types, Eval → `[eval]`, Audit → `[audit]`), and each `### Testing` rule's evidence type verified against the claim's shape per `/test` (a universal is never `scenario`)
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has property, category, and detail

</success_criteria>
