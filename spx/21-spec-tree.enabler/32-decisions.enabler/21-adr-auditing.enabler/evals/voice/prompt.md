<!-- Generated from src/plugins/spec-tree/skills/audit-adr/SKILL.md, section audit_adr. -->

Apply the complete producer workflow below to the supplied ADR input. Treat the caller's scope classification as language-neutral; the supplied ADR content is the context for this curated eval case.

<step name="audit_adr">

<step name="load_context">

**Step 1: Load context**

Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent, then invoke `/contextualize` on the directory containing the ADR.

Do not proceed without live `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers.

</step>

<step name="read_adr">

**Step 2: Read the ADR**

Read the ADR under audit. Identify its sections: the opening decision statement, Rationale (optional), Invariants (optional), and Verification.

</step>

<step name="audit_native">

Audit every native ADR concern through the three steps below before composing language-specific rows.

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

</step>

<step name="compose_language">

**Step 5b: Compose language-specific architecture concerns**

This skill owns section structure, atemporal voice, and tag validity from the canonical template. Language-specific architecture concerns — dependency injection, no-mocking, execution-level accuracy — are owned by the language audit skill, not by this one.

Read the caller-provided scope classification first. When it classifies the ADR as language-neutral, skip composition. For every declared implementation-language partition, require the matching `audit-<lang>-architecture` skill and invoke it through the Skill tool. Append its distinct rows (`testability-in-verification`, `mocking-prohibition`, `level-accuracy`, …) to this verdict's `rows` array; the language skill judges only language-specific concerns and never re-judges section structure, voice, or tags. When a language-specific ADR has no reliable partition or the required skill cannot load, append a `FAIL` row named `language-routing-unavailable` or `language-skill-unavailable` with a blocking finding instead of guessing or approving incomplete coverage.

</step>

<step name="verdict">

**Step 6: Issue verdict**

Scan all findings and native or composed rows. If any row is `FAIL`, issue `REJECTED`; otherwise issue `APPROVED`.

</step>

</step>

The ADR input (JSON-encoded):

```json
{input_json}
```

Return only this `audit-adr` JSON shape, replacing placeholders and adding findings where a row fails:

```json
{
  "schema_version": 1,
  "skill": "audit-adr",
  "target": "<copy input target>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {"name": "section-structure", "status": "PASS | FAIL | NOT_APPLICABLE", "findings": []},
    {"name": "atemporal-voice", "status": "PASS | FAIL | NOT_APPLICABLE", "findings": []},
    {"name": "tag-validity", "status": "PASS | FAIL | NOT_APPLICABLE", "findings": []}
  ],
  "metadata": {"branch": "<branch>"}
}
```

Every finding has `rule`, `severity` (`blocking`), `location`, `message`, `observed`, and `expected`. The `rule` is exactly one of `missing-section`, `temporal-voice`, `invalid-tag`, `evidence-type-mismatch`, `template-missing`, `language-routing-unavailable`, or `language-skill-unavailable`.
