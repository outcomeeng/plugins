---
name: auditing-internal-docs
description: >-
  ALWAYS invoke this skill when auditing or reviewing internal team documents for cleanup. Use this whenever the user asks to review, audit, clean up, or check the writing of a Notion page, runbook, hiring rubric, scorecard, internal policy, decision record, design spec, competency model, onboarding guide, or any other doc that lives in a workspace and is read by colleagues. NEVER invoke for external-facing prose like READMEs, blog posts, web copy, customer release notes, or marketing material — use auditing-prose for those instead. NEVER invoke for responses to the user, including long research summaries delivered in chat, or for agent-facing instructions like SKILL.md and AGENTS.md.
allowed-tools: Read, Glob, Grep, Bash
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-internal-docs/SKILL.md" || echo "standardizing-internal-docs not found — invoke skill prose:standardizing-internal-docs now"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke this skill now before proceeding:

1. Skill `prose:standardizing-internal-docs`

</codex_fallback>

<objective>
Detect anti-patterns in internal documents and propose concrete rewrites. Flag specific violations with category and pattern name; show the fix.
</objective>

<workflow>
1. Read `/standardizing-internal-docs` for the catalog.

2. Read the document being reviewed.

3. Flag each violation. Name the specific pattern and the category it belongs to. The category labels match the catalog sections: inherited word choice, inherited sentence structure, inherited tone, inherited composition, inherited formatting, internal-doc heading rules, internal-doc metadata rules, internal-doc cross-reference rules, internal-doc list and table rules.

4. Propose a concrete rewrite for each flag. Don't just say "avoid X" — show the fixed text. The rewrite makes the suggestion actionable and lets the user accept or modify it directly.

5. Summarize. Total violation count, most frequent category, overall assessment of doc quality. The summary lets the user prioritize their attention.

</workflow>

<what_to_check>
Apply the catalog systematically.

Inherited rules from `/standardizing-prose`. Word choice anti-patterns (significance adverbs, authenticity adverbs, overused vocabulary, ornate nouns, pompous verbs). Sentence-structure anti-patterns (negative parallelism, stacked negations, rhetorical self-answers, anaphora abuse, tricolon stacking, filler transitions, gerund fragment litanies). Tone anti-patterns (false suspense, unnecessary metaphors, hypothetical openers, asserted clarity, grandiose stakes inflation, teacher-student condescension). Composition anti-patterns (fractal summaries, dead metaphors, signposted conclusions, dismissive optimism). Formatting anti-patterns: em-dash overuse remains forbidden, unicode decoration remains forbidden.

Internal-doc-specific rules from `/standardizing-internal-docs`. The opening sentence must be the substantive lead, not metadata or boilerplate. Headings must be sentence case with no end punctuation. Acronyms must be defined on first introduction and reused at least twice. Concepts with canonical homes must be linked inline. Metadata must live in document properties, not opening prose. Bold must mark inline key terms on first introduction, not act as general emphasis. Italics must mark defined terms and document titles, not substitute for bold.

Internal-doc-specific overrides. Don't flag a parens-clarification that the override allows. Don't flag a bold table-cell label that the override allows. Don't flag an italic structural label in a repeated pattern that the override allows. The internal-doc catalog explicitly permits these patterns; flagging them would be a mistake.
</what_to_check>

<success_criteria>
The review is complete when:

Every flagged violation names the specific pattern and the category.

Every flag includes a concrete rewrite, not just a label or instruction.

The summary gives a count, identifies the most frequent category, and assesses overall doc quality.

Co-occurring patterns in a single sentence are flagged as highest priority. A sentence that contains an em-dash, a significance adverb, and a parenthetical aside used for emphasis is three violations in one place and deserves explicit attention.

The audit applies the internal-doc overrides correctly. Parens that aid clarity are not flagged. Bold table-cell labels are not flagged. Italic structural labels in repeated patterns are not flagged.

The audit covers the `<success_criteria>` items from `/standardizing-internal-docs` as a minimum.
</success_criteria>

<reference_index>

| Skill                          | When to read                                 |
| ------------------------------ | -------------------------------------------- |
| `/standardizing-internal-docs` | Always, before auditing                      |
| `/writing-internal-docs`       | When the user wants the rewritten version    |
| `/standardizing-prose`         | For inherited rules                          |
| `/auditing-prose`              | For external-facing prose, not internal docs |

</reference_index>
