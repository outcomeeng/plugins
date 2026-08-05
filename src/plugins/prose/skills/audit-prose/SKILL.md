---
name: audit-prose
description: >-
  Prose audit methodology preloaded by the prose-auditor agent. Dispatch prose-auditor to audit human-facing text; the main conversation reaches this audit only through that agent.
model: sonnet
allowed-tools: Read, Glob, Grep, Skill
---

{!% require_skill 'prose:prose-standards' %!}

<objective>

A structured verdict on human-facing text — `APPROVED`, or `REJECTED` with findings carrying pattern, category, quote, rewrite, and detected kind.

</objective>

<dispatch_gate>

STOP if this skill is running in the main conversation. The verdict is valid only from an isolated verifier context: dispatch the `prose-auditor` agent with the text or paths to audit and apply its final message. Producing the verdict in the authoring conversation reintroduces the bias the dispatched context removes.

</dispatch_gate>

<constraints>

- NEVER modify the document under review — this audit produces a verdict only.
- NEVER flag a pattern the resolved kind's overrides explicitly permit — the overrides are the catalog's decision, not an oversight.
- NEVER excuse a base-catalog match as "single use" or "it works here" — every match outside an override is a finding.
- NEVER guess an ambiguous kind — report the ambiguity in the verdict and audit the plausible kinds' shared rules only.

</constraints>

<workflow>

1. Read the text under audit — whatever the dispatch names, pastes, or points to.

2. Classify it through `/prose-standards` `<kind_detection>` — pre-loaded above. A document whose parts differ in kind receives per-part classification; each finding names its part's kind.

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
