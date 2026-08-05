---
name: audit-interface
description: >-
  Interface audit methodology — sweeps surface text against the base catalog, the fragment and consistency overrides, and the interface rules — composed by audit-prose for the interface kind. Reached only through the dispatched prose-auditor agent, never the main conversation.
model: sonnet
allowed-tools: Read, Glob, Grep, Skill
---

{!% require_skill 'prose:interface-standards' %!}

<objective>

Findings on surface text — each carrying pattern, category, quote, and rewrite — for `/audit-prose` to assemble into its verdict.

</objective>

<constraints>

- NEVER modify the text under review.
- NEVER flag a pattern the interface overrides permit — element fragments and parallel-element repetition are the catalog's decision. Every use outside those bounds stays a finding.

</constraints>

<workflow>

1. Sweep the base categories against the full `/prose-standards` descriptions, applying the two overrides: fragments pass for surface elements (not for body text inside them), and repetition passes across parallel elements (not within one element's prose).
2. Sweep the `/interface-standards` `<additional_rules>` per element type: action-led buttons and links, sentence case, brevity caps, one term per concept across the surface, error what-happened/what-next pairing, orienting empty states, consequence-naming confirmations, filler words.
3. Return each finding with the pattern name, its category, the offending quote verbatim, and a concrete rewrite. A sentence or element with co-occurring patterns yields one finding naming every pattern present.

</workflow>

<success_criteria>

- Every base category and every interface rule was swept per element type.
- The overrides produced no false-positive findings, and out-of-bounds uses of them were still flagged.
- Every finding carries pattern, category, quote, and rewrite, with rewrites showing fixed text.

</success_criteria>
