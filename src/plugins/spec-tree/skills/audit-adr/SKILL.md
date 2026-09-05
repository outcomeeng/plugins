---
name: audit-adr
description: >-
  ADR audit methodology — judges one ADR against the ADR evidence model,
  covering section structure, atemporal voice, and per-rule tag validity.
model: sonnet
allowed-tools: Read, Grep, Glob, Skill, Bash(git branch --show-current:*)
---

<objective>

A verdict on one ADR against the ADR evidence model — APPROVED, or REJECTED with each finding naming the section, the violated rule, and the evidence. Findings fall in three native categories: section structure, atemporal voice, and per-rule tag validity and assertion-type fit.

</objective>

<essential_principles>

**ARCHITECTURE BY DEFINITION.**

An ADR's content is architecture — technology choices, data structures, implementation approaches. NEVER classify ADR content as product-behavior-versus-architecture; that classification is the PDR audit's concern. Audit the ADR's form, not whether its content belongs elsewhere.

**ASSERTION TYPE MUST MATCH THE CLAIM.**

Each rule under `## Verification` carries one tag matching its subsection — `### Testing` → an assertion type (scenario, mapping, conformance, property, compliance); `### Eval` → `[eval]`; `### Audit` → `[audit]`. `/verify` selects the verification type, then `/test` selects the assertion type for a Testing rule; this audit verifies both selections fit the claim. The decisive assertion-type check is the quantifier: a universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") is never `scenario`, because a scenario proves one case and cannot establish a claim about every case; `scenario` fits only a single existential interaction. A missing tag, an unsupported bare mechanism tag, a tag disagreeing with its subsection, more than one tag, or an assertion type the `/test` router would not produce for the claim is a finding.

**ATEMPORAL VOICE.**

ADRs state architecture truth. "The build emits one wheel per plugin" — not "We switched to per-plugin wheels because the monolith broke."

**BINARY VERDICT.**

`APPROVED` or `REJECTED`. An unavailable required inspection is a rejection with evidence naming the blocked inspection; it never becomes an approval through an unevaluated row.

**LANGUAGE COMPOSITION BOUNDARY.**

Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are composed from `/audit-<lang>-architecture` in Step 5b. The language skill judges only those concerns; this skill owns section structure, atemporal voice, and tag validity from the canonical template.

</essential_principles>

<constraints>

- NEVER modify the ADR under audit or any other file — this audit produces a verdict, never a fix or a commit.
- ALWAYS derive the valid section set from the canonical ADR template before judging structure — never from memory.
- ALWAYS name the section, the violated rule, and the evidence in every REJECT finding.
- NEVER issue a finding the cited rule or canonical template does not support — drop an unbacked finding rather than reject the ADR for it.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent. Record the base directory exposed by that invocation and read its bundled canonical ADR template at `templates/decisions/decision-name.adr.md`; the template remains owned by `/understand` and is never copied into this skill. Then invoke `/contextualize` on the directory containing the ADR. Run `git branch --show-current` to populate verdict metadata without granting broader shell authority.

Do not proceed without the canonical ADR template content and live `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers.

</step>

<step name="read_adr">

**Step 2: Read the ADR**

Read the ADR under audit. Identify its sections: the opening decision statement, Rationale (optional), Invariants (optional), and Verification.

</step>

<step name="audit_structure">

**Step 3: Section structure**

Use the canonical ADR template guidance loaded in Step 1 to derive the valid section set in full — never from memory or a transcribed copy. A structural finding that contradicts the canonical template is unbacked: drop it rather than rejecting the ADR. If the template guidance cannot be loaded, reject with `template-missing` and name the blocked read.

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

**Step 5: Per-rule tag validity and assertion-type fit**

Rules live under `## Verification`, grouped into `### Testing`, `### Eval`, and `### Audit` subsections by verification type. For each rule:

1. The tag is valid for its subsection:
   - under `### Testing` → one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])`;
   - under `### Audit` → `([audit])`.
2. Under `### Testing`, the assertion type fits the claim's shape per the `/test` router. Read the claim's quantifier: a universal (ALWAYS / NEVER / "for all" / "for every" / "no input") takes `mapping`, `conformance`, `compliance`, or `property` — never `scenario`; a single existential interaction takes `scenario`. Within the universal branch the router yields one type by domain shape (finite source-owned → `mapping`; external/internal contract → `conformance`; rule exercised against violating cases → `compliance`; open or infinite → `property`). Reject a type the router would not produce for the claim; do not relitigate a choice the router leaves open between equally-valid types.

An unsupported bare mechanism tag, a tag disagreeing with its subsection, a missing tag, more than one tag, or an assertion type that contradicts the claim's shape (a universal tagged `scenario` is the clearest case) is invalid.

**A rule with no subsection tag, a tag disagreeing with its subsection, a bare mechanism tag in place of an assertion type, or more than one tag → REJECT — "invalid-tag." An assertion type that contradicts the claim's shape → REJECT — "assertion-type-mismatch."**

</step>

<step name="compose_language">

**Step 5b: Compose language-specific architecture concerns**

This skill owns section structure, atemporal voice, and tag validity from the canonical template. Language-specific architecture concerns — dependency injection, no-mocking, execution-level accuracy — are owned by the language audit skill, not by this one.

Read the supplied scope classification first. When it classifies the ADR as language-neutral, skip composition. For every declared implementation-language partition, require the matching `audit-<lang>-architecture` skill and invoke it through the Skill tool. Append its distinct rows (`testability-in-verification`, `mocking-prohibition`, `level-accuracy`, …) to this verdict's `rows` array; the language skill judges only language-specific concerns and never re-judges section structure, voice, or tags. When a language-specific ADR has no reliable partition or the required skill cannot load, append a `FAIL` row named `language-routing-unavailable` or `language-skill-unavailable` with a blocking finding instead of guessing or approving incomplete coverage. One case is not a composition failure. When the changeset under audit itself ships the ADR's language plugin, unpublished and uninstalled in this session, no `audit-<lang>-architecture` skill can exist yet. The caller classifies that ADR language-neutral for composition and states the reason. Judge the decision directly against the skill files its rules name and the cross-language decisions, and record a row named `language-skill-unpublished` as `NOT_APPLICABLE` with that explanation, so the row name alone distinguishes this expected case from a genuine load failure.

</step>

<step name="verdict">

**Step 6: Issue verdict**

Scan all findings and native or composed rows. If any row is `FAIL`, issue `REJECTED`; otherwise issue `APPROVED`.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as a single JSON object. This JSON is the skill's entire output; never a prose or markdown verdict.

The `overall` is `APPROVED` iff every native and composed row is `PASS` or `NOT_APPLICABLE`; otherwise it is `REJECTED`. Every `NOT_APPLICABLE` row explains why its concern does not apply. A required property that cannot be evaluated is a `FAIL` row with a blocking finding naming the unavailable inspection. Findings use the audit-run severities `blocking` or `debt`; this binary ADR gate emits `blocking` for every finding that rejects the ADR.

```json
{
  "schema_version": 1,
  "skill": "audit-adr",
  "target": "<adr-file-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    { "name": "section-structure", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "tag-validity", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding carries `rule`, `severity: "blocking"`, `location`, `message`, `observed`, and `expected`. The `rule` field carries the violation pattern (`missing-section`, `temporal-voice`, `invalid-tag`, `assertion-type-mismatch`, `template-missing`, `language-routing-unavailable`, or `language-skill-unavailable`).

</verdict_format>

<failure_modes>

**Failure 1: Imported the PDR content gate into an ADR audit**

Claude flagged "uses PostgreSQL with row-level locking" as architecture content that does not belong — in an ADR. An ADR's content is architecture by definition; there is no product-versus-architecture classification to run. The PDR audit's content gate has no place here.

How to avoid: The ADR audit checks form — structure, voice, tag validity. Content classification is the PDR audit's concern only.

**Failure 2: Passed a universal rule tagged `scenario`**

Claude saw a `### Testing` rule — a universal ALWAYS/NEVER claim — tagged `([scenario])`, and passed it because a tag was present and named one of the five assertion types. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified — phantom green. The quantifier mismatch is a deterministic error, not a matter of taste.

How to avoid: Step 5 verifies the assertion type fits the claim's shape per the `/test` router. Reject a universal tagged `scenario` (and any type the router would not produce for the claim). The one line the audit does not cross is relitigating a choice the router leaves open between equally-valid types — that, and only that, is `/test`'s to decide.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every ADR rule was judged with none skipped — section structure, atemporal voice, and per-rule tag validity and assertion-type fit; when a language is in scope, the composed `/audit-<lang>-architecture` rows are judged too (coverage-complete).
- The verdict states one `APPROVED` or `REJECTED` overall determination, every native and composed row carrying `PASS`, `FAIL`, or explained `NOT_APPLICABLE`, with no rule left unevaluated.
- Each REJECT finding is falsifiable: it names the section, the violated rule, and the evidence — the missing section, the temporal phrase, or the mismatched tag.
- The same ADR yields the same verdict.

</success_criteria>
