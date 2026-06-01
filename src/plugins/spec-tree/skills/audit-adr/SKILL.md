---
name: audit-adr
description: Use when asked by the user to invoke the ADR audit skill
allowed-tools: Read, Grep, Glob, Bash
---

<objective>

Audit whether an ADR declares a well-formed architecture decision whose compliance rules carry valid per-rule evidence modes and flow into spec assertions with sufficient evidence. Four properties must hold — section structure, atemporal voice, per-rule mode validity, downstream sufficiency — checked in strict order. An ADR failing any property is a malformed or unenforced architecture decision.

Language-specific ADR concerns — testability-in-Compliance (dependency injection, no-mocking), execution-level accuracy — stay in `/auditing-{lang}-architecture`, not here.

</objective>

<quick_start>

**PREREQUISITE**: Invoke `/contextualizing` on the ADR's parent directory.

1. Read the ADR under audit
2. Check four properties in order: structure → voice → mode validity → downstream sufficiency
3. First property failure = REJECT (skip remaining properties)
4. All four properties hold = APPROVED

</quick_start>

<essential_principles>

**ARCHITECTURE BY DEFINITION.**

An ADR's content is architecture — technology choices, data structures, implementation approaches. NEVER classify ADR content as product-behavior-versus-architecture; that classification is the PDR audit's concern. Audit the ADR's form and enforcement, not whether its content belongs elsewhere.

**MODE VALIDITY IS PRESENCE, NOT RE-DERIVATION.**

Each Compliance MUST/NEVER rule carries one evidence-mode tag naming one of the five claim shapes (scenario, mapping, conformance, property, compliance). Verify the tag is present and names a real mode. NEVER re-derive the mode — mode selection is `/testing`'s authority. A missing tag, a bare mechanism tag (`[review]`/`[test]`/`[eval]`) in place of a mode, or more than one tag is a finding.

**DOWNSTREAM SUFFICIENCY, NOT MERE PRESENCE.**

A compliance rule's downstream spec assertion must carry evidence at or above the rule's declared mode. A `property`-floor rule enforced only by a `scenario` assertion is a finding — sufficiency, not presence, is the bar.

**ATEMPORAL VOICE.**

ADRs state architecture truth. "The build emits one wheel per plugin" — not "We switched to per-plugin wheels because the monolith broke."

**BINARY VERDICT.**

APPROVED or REJECT. No middle ground.

</essential_principles>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualizing` on the directory containing the ADR. This loads the product spec, ancestor decisions, and lower-index siblings that constrain the ADR.

Do not proceed without the `<SPEC_TREE_CONTEXT>` marker.

</step>

<step name="read_adr">

**Step 2: Read the ADR**

Read the ADR under audit. Identify its sections: Purpose, Context, Decision, Rationale, Trade-offs, Invariants (optional), Compliance.

</step>

<step name="audit_structure">

**Step 3a: Section structure**

Verify the required sections are present: Purpose, Context, Decision, Rationale, Trade-offs, Compliance. Invariants appears only when the decision establishes algebraic properties.

**Any required section missing → REJECT — "missing-section."**

</step>

<step name="audit_voice">

**Step 3b: Atemporal voice**

Check EVERY section for temporal language.

| Temporal (REJECT)                     | Atemporal (correct)             |
| ------------------------------------- | ------------------------------- |
| "We decided to use X because Y broke" | "X governs Z"                   |
| "Currently the build does X"          | "The build does X"              |
| "After profiling, we added caching"   | "Caching reduces latency for Z" |

**Any temporal language in any section → REJECT — "temporal-voice."**

</step>

<step name="audit_mode_validity">

**Step 3c: Per-rule mode validity**

For each Compliance MUST/NEVER rule, verify it carries exactly one evidence-mode tag naming one of `scenario`, `mapping`, `conformance`, `property`, `compliance`. Do not re-derive the mode — only validate the tag.

**A rule with no mode tag, a bare mechanism tag in place of a mode, or more than one tag → REJECT — "invalid-mode-tag."**

</step>

<step name="audit_downstream_sufficiency">

**Step 3d: Downstream sufficiency**

For each Compliance rule, search the governed subtree for the spec assertion(s) enforcing it. Compare each enforcing assertion's evidence against the rule's declared mode.

| Outcome                                                                        | Finding                      |
| ------------------------------------------------------------------------------ | ---------------------------- |
| No downstream assertion                                                        | "unenforced-rule"            |
| Downstream evidence below the declared mode (e.g. `scenario` under `property`) | "insufficient-evidence-mode" |
| Downstream evidence at or above the declared mode                              | PASS                         |

**Any rule unenforced or under-enforced → REJECT.**

</step>

<step name="verdict">

**Step 4: Issue verdict**

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
  "target": "<adr-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "section-structure", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "mode-validity", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "downstream-sufficiency", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` field carries the violation pattern (`missing-section`, `temporal-voice`, `invalid-mode-tag`, `unenforced-rule`, `insufficient-evidence-mode`); the `message` field carries the one-line detail.

</verdict_format>

<success_criteria>

Audit is complete when:

- [ ] `/contextualizing` invoked — `<SPEC_TREE_CONTEXT>` marker present
- [ ] ADR read — all sections identified
- [ ] Section structure: required sections present
- [ ] Atemporal voice: every section checked for temporal language
- [ ] Per-rule mode validity: each Compliance rule's mode tag validated against the five modes
- [ ] Downstream sufficiency: each rule's enforcing assertion checked at or above the declared mode
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has property, category, and detail

</success_criteria>
