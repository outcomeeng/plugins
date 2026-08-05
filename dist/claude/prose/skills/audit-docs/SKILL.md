---
name: audit-docs
user-invocable: false
description: >-
  Docs audit methodology — judges documentation against the base anti-pattern catalog and the simplified ASD-STE100 structural rules, checking every cap by count and producing findings that carry pattern, category, quote, and rewrite.
model: sonnet
allowed-tools: Read, Glob, Grep, Skill
---

Invoke the `prose:docs-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

Findings on documentation — each carrying pattern, category, quote, and rewrite — for `/audit-prose` to assemble into its verdict.

</objective>

<constraints>

- NEVER modify the document under review.
- NEVER flag a numbered-step imperative as a fragment or listicle — the docs override permits it. Every other base match stays a finding.
- NEVER wave a sentence past a cap by judgment — the caps are counts, so count.

</constraints>

<audit_workflow>

1. Sweep the `/docs-standards` `<additional_rules>` sentence by sentence: word counts against the 20/25 caps, one instruction per sentence, active voice, simple tenses, verbal "-ing" clauses, should/would/may/might, condition ordering, noun clusters over three, paragraphs over six sentences, dropped articles, term-to-concept mapping across the set.
2. Sweep the base categories against the full `/prose-standards` descriptions, applying the numbered-step override.
3. Return each finding with the pattern name, its category, the offending quote verbatim, and a concrete rewrite. A sentence with co-occurring patterns yields one finding naming every pattern present.

</audit_workflow>

<success_criteria>

- Every structural rule was checked by count where it is a count, on every sentence.
- The numbered-step override produced no false-positive findings.
- Every finding carries pattern, category, quote, and rewrite, with rewrites showing fixed text.

</success_criteria>
