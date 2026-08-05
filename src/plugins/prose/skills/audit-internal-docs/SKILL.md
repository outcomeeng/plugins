---
name: audit-internal-docs
description: >-
  Internal-doc audit methodology — sweeps workspace documents against the base catalog, the internal-doc overrides, and the internal-doc rules — composed by audit-prose for the internal-docs kind. Reached only through the dispatched prose-auditor agent, never the main conversation.
model: sonnet
allowed-tools: Read, Glob, Grep, Skill
---

{!% require_skill 'prose:internal-doc-standards' %!}

<objective>

Findings on an internal team document — each carrying pattern, category, quote, and rewrite — for `/audit-prose` to assemble into its verdict.

</objective>

<constraints>

- NEVER modify the document under review.
- NEVER flag a pattern the internal-doc overrides explicitly permit — the overrides are the catalog's decision, not an oversight. Every use outside an override's bounds stays a finding.

</constraints>

<what_to_check>

Sweep every category below. `/internal-doc-standards` carries the rule text and the examples; this list names the categories so no section goes unswept.

Inherited categories, from that catalog's `<inherited_rules>`: word choice, sentence structure, paragraph structure, tone, composition, formatting.

Internal-doc categories, from its `<additional_rules>` and `<success_criteria>`: lead-first opening, heading case and parent-title repetition, metadata placement, acronym definition and reuse, cross-reference linking, bold and italic usage, list and table shape, callout density, decisive language and action labels.

Overrides, from its `<overrides>`: parens that aid clarity, bold table-cell labels, bold inline paragraph introducers, and italic structural labels in repeated patterns. Read the override text before flagging any of these. Each override is bounded — flag parens carrying emphasis or redundant restatement, bold acting as general emphasis, and italics standing in for bold.

</what_to_check>

<workflow>

1. Sweep the inherited categories against the full `/prose-standards` descriptions, applying the internal-doc overrides.
2. Sweep the internal-doc categories from `<what_to_check>` against `/internal-doc-standards`.
3. Return each finding with the pattern name, its category, the offending quote verbatim, and a concrete rewrite. A sentence carrying co-occurring patterns yields one finding naming every pattern present, listed before single-pattern findings.

</workflow>

<success_criteria>

- Every inherited and internal-doc category was swept, none skipped as unlikely.
- The overrides produced no false-positive findings, and out-of-bounds uses of them were still flagged.
- Every finding carries pattern, category, quote, and rewrite, with rewrites showing fixed text.

</success_criteria>
