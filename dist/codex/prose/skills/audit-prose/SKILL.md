---
name: audit-prose
description: >-
  Prose audit methodology — judges human-facing text against the base anti-pattern catalog and the detected kind's standards layer, emitting a structured verdict whose findings carry pattern, category, quote, rewrite, and kind.
model: "gpt-5.5"
allowed-tools: Read, Glob, Grep, Skill
---

Invoke the `prose:prose-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

A structured verdict on human-facing text — `APPROVED`, or `REJECTED` with findings carrying pattern, category, quote, rewrite, and detected kind.

</objective>

<constraints>

- NEVER modify the document under review — this audit produces a verdict only.
- NEVER flag a pattern the resolved kind's overrides explicitly permit — the overrides are the catalog's decision, not an oversight.
- NEVER excuse a base-catalog match as "single use" or "it works here" — every match outside an override is a finding.
- NEVER guess an ambiguous kind — honor a dispatch-declared kind only for text the detection procedure leaves ambiguous; when none is declared, report the ambiguity in the verdict and audit the plausible kinds' shared rules only.

</constraints>

<workflow>

1. Read the text under audit — whatever the dispatch names, pastes, or points to.

2. Classify it through `/prose-standards` `<kind_detection>` — pre-loaded above. The ownership test always runs first; a kind the dispatch declares resolves only text the procedure otherwise leaves ambiguous — a dispatch line such as `Kind: docs (user-selected) for guide.md` fixes that file's kind without asking the user, never bypassing ownership. A document whose parts differ in kind receives per-part classification; each finding names its part's kind.

3. Invoke the resolved kind's composed audit skill via the Skill tool: `prose:audit-copy`, `prose:audit-interface`, `prose:audit-docs`, or `prose:audit-internal-docs`. That skill loads the kind's standards and sweeps its categories; collect its findings.

4. Emit the structured verdict in the `<verdict_format>` shape as the final message — no prose outside the JSON object.

</workflow>

<verdict_format>

```json
{
  "schema_version": 1,
  "skill": "audit-prose",
  "overall": "APPROVED",
  "kinds": ["copy"],
  "findings": [],
  "summary": { "violations": 0, "most_frequent_category": null }
}
```

- `overall` is `REJECTED` when at least one finding exists; `APPROVED` means zero findings.
- Each finding carries `kind`, `pattern` (the catalog anti-pattern name), `category` (its catalog section), `quote` (the offending text verbatim), and `rewrite` (fixed text ready to accept).
- `kinds` lists every kind the classification resolved, in document order.
- A sentence carrying multiple co-occurring patterns produces one finding naming every pattern present, listed before single-pattern findings.
- When ownership routes the document away, `overall` is `REJECTED` with a single finding whose `pattern` is `governed-elsewhere` naming the governing workflow.

</verdict_format>

<success_criteria>

- The final message is exactly the `<verdict_format>` JSON object.
- Every finding carries all five fields, and the rewrite shows fixed text rather than an instruction.
- `summary.violations` equals the findings count, and `most_frequent_category` is the category those findings carry most often.
- Kind overrides produced no false-positive findings.

</success_criteria>

<failure_modes>

**A caller check survived a description-only fix.**

Claude removed dispatch language from this skill's description to satisfy the audit-description standard, but left a dispatch gate in the body and a dispatch-tool grant in the frontmatter — the same caller-coupling defect in two other places. A skill never detects, constrains, or branches on the context that invokes it; context placement and dispatch policy belong to the caller. When removing caller coupling, check the description, the frontmatter grants, and the body together — the pattern recurs across all three surfaces.

</failure_modes>
