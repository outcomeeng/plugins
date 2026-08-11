---
name: audit-document
user-invocable: false
description: >-
  Document audit methodology — judges a page in a document set against the base anti-pattern catalog, the document overrides, the page-architecture and sentence rules, and every triggered rule pack, producing findings that carry pattern, category, quote, and rewrite.
model: "opus"
allowed-tools: Read, Glob, Grep, Skill
---

Invoke the `prose:document-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

Findings on a page in a document set — each carrying pattern, category, quote, and rewrite — for `/audit-prose` to assemble into its verdict.

</objective>

<constraints>

- NEVER modify the page under review.
- NEVER flag a pattern the document overrides explicitly permit — an override is the catalog's decision, not an oversight. A use outside an override's bounds stays a finding.
- NEVER wave a sentence past a cap by judgment. A cap is a count, so count.
- NEVER skip a rule pack because the page's kind is not the pack's home. A pack binds on the feature, in every kind.

</constraints>

<what_to_check>

Sweep every category below. `/document-standards` and `/prose-standards` carry the rule text and the examples; this list names the categories so none goes unswept.

Inherited categories, from `/document-standards` `<inherited_rules>`: word choice, sentence structure, paragraph structure, tone, composition, formatting.

Voice canon, from `/document-standards` `<voice_canon>`: substance-first openings, plain words, filler words, unsupported assertion, one term one meaning, failure text, sentence case, punctuation.

Sentence shape, from `<additional_rules>`: the 25-word descriptive cap by count, simple tenses, verbal "-ing" clauses, noun clusters over three, paragraphs over six sentences.

Page architecture, from `<additional_rules>`: lead-first opening, heading case and parent-title repetition, metadata placement, key-term bolding, italic usage, acronym definition and reuse, cross-reference linking, list shape, callout density, decisive language.

Rule packs, from `/prose-standards` `<rule_packs>`: the instruction pack on every procedure — 20-word cap by count, one instruction per sentence, condition ordering, modal hedging, action-leading steps, dropped articles — and the table pack on every table.

Overrides, from `<overrides>`: numbered-step imperatives, bold table cells as row keys, parentheses that aid clarity, bold inline paragraph introducers, italic structural labels in repeated patterns. Read the override text before flagging any of these. Each is bounded — flag parentheses carrying emphasis or restatement, bold acting as general emphasis, and italics standing in for bold.

</what_to_check>

<workflow>

1. Sweep the inherited categories and the voice canon against the full `/prose-standards` descriptions, applying the document overrides.
2. Sweep sentence shape and page architecture from `<what_to_check>` against `/document-standards`, counting every cap that is a count.
3. Identify every feature that triggers a rule pack, then sweep each triggered pack over the passages carrying that feature.
4. Return each finding with the pattern name, its category, the offending quote verbatim, and a concrete rewrite. A sentence carrying co-occurring patterns yields one finding naming every pattern present, listed before single-pattern findings.

</workflow>

<success_criteria>

- Every inherited, voice, sentence-shape, and page-architecture category was swept, none skipped as unlikely.
- Every cap that is a count was checked by count, on every sentence.
- Every rule pack the page triggers was applied over the passages that trigger it.
- The overrides produced no false-positive findings, and out-of-bounds uses of them were still flagged.
- Every finding carries pattern, category, quote, and rewrite, with rewrites showing fixed text.

</success_criteria>
