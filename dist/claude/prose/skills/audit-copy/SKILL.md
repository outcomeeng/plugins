---
name: audit-copy
user-invocable: false
description: >-
  Copy audit methodology — judges self-contained pieces against the base anti-pattern catalog and the copy composition layer, producing findings that carry pattern, category, quote, and rewrite.
model: "opus"
allowed-tools: Read, Glob, Grep, Skill
---

Invoke the `prose:copy-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

Findings on a self-contained piece — each carrying pattern, category, quote, and rewrite — for `/audit-prose` to assemble into its verdict.

</objective>

<constraints>

- NEVER modify the document under review.
- NEVER excuse a base-catalog match — copy declares no overrides, so every match is a finding.

</constraints>

<audit_workflow>

1. Sweep every base category — word choice, sentence structure, paragraph structure, tone, formatting, composition — against the full `/prose-standards` descriptions.
2. Sweep the `/copy-standards` `<additional_rules>`: paragraph progression, example development, single-use rhetorical devices, length against substance, unannounced ending, tradeoffs in place.
3. Return each finding with the pattern name, its category, the offending quote verbatim, and a concrete rewrite. A sentence with co-occurring patterns yields one finding naming every pattern present.

</audit_workflow>

<success_criteria>

- Every base category and every copy composition rule was swept, none skipped as unlikely.
- Every finding carries pattern, category, quote, and rewrite, with rewrites showing fixed text.

</success_criteria>
