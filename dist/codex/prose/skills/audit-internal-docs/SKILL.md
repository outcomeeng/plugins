---
name: audit-internal-docs
description: >-
  ALWAYS invoke this skill when reviewing, auditing, or cleaning up the writing in internal team documents that live in a workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, competency models, onboarding guides, status pages, internal wiki content, and team decision records and design specs. NEVER invoke for a doc a repository or domain workflow already owns — specs, ADRs, PDRs, PLAN.md, ISSUES.md, SKILL.md, AGENTS.md — follow that workflow instead. NEVER invoke for writing aimed at outside readers even when it is drafted in the workspace — public status pages, release notes, marketing copy, READMEs, blog posts — use audit-prose.
model: sonnet
allowed-tools: Read, Glob, Grep, Bash, Skill
---

Invoke the `prose:internal-doc-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A list of internal-doc anti-patterns found, each flagged with its category and pattern name and paired with a concrete rewrite. A closing summary states the violation count, the most frequent category, and an overall quality assessment.
</objective>

<constraints>
NEVER modify the document under review — this skill produces flags and proposed rewrites, and the user applies them.
NEVER flag a pattern the internal-doc overrides explicitly permit — the overrides are the catalog's decision, not an oversight.
</constraints>

<artifact_ownership>
Reviewing a document follows the same ownership rules as writing it. Artifact ownership outranks audience, so "it lives in a workspace and colleagues read it" never routes a review here on its own.

Repository-governed engineering artifacts — `AGENTS.md`, spec-tree specs, ADRs, PDRs, `PLAN.md`, `ISSUES.md`, `SKILL.md` — carry dedicated domain workflows that own their structure, voice, and required sections. Route their review to the governing repository skill. Auditing them against this catalog would flag conventions their governing workflow requires.

Apply two tests before reviewing. Ownership first: when a repository or domain workflow governs the artifact, stop and route there. Audience second: when the document addresses readers outside the team — a public status page, customer release notes, marketing copy — route the review to `/audit-prose`, even though the draft lives in the workspace. Only a document that passes both tests is an internal doc.
</artifact_ownership>

<workflow>
1. Read `/internal-doc-standards` for the catalog.

2. Confirm ownership. Apply the `<artifact_ownership>` test: when a repository or domain workflow governs the document, stop and route the review to that workflow.

3. Read the document being reviewed.

4. Flag each violation. Name the specific pattern and the category it belongs to. The category labels match the catalog sections: inherited word choice, inherited sentence structure, inherited tone, inherited composition, inherited formatting, internal-doc heading rules, internal-doc metadata rules, internal-doc cross-reference rules, internal-doc list and table rules.

5. Propose a concrete rewrite for each flag. Don't just say "avoid X" — show the fixed text. The rewrite makes the suggestion actionable and lets the user accept or modify it directly.

6. Emit the flags and the closing summary in the shape `<verdict_format>` defines.

</workflow>

<verdict_format>
Report each violation as a flag carrying four parts:

- **Pattern** — the specific anti-pattern name from the catalog.
- **Category** — the catalog section it belongs to.
- **Quote** — the offending text as it appears in the document.
- **Rewrite** — the corrected text, ready to accept.

Close with a summary carrying the total violation count, the most frequent category, and an overall assessment of doc quality.

When the document is governed elsewhere per `<artifact_ownership>`, emit no flags: name the governing workflow and stop.
</verdict_format>

<what_to_check>
Apply the catalog systematically.

Inherited rules from `/prose-standards`. Word choice anti-patterns (significance adverbs, authenticity adverbs, overused vocabulary, ornate nouns, pompous verbs). Sentence-structure anti-patterns (negative parallelism, stacked negations, rhetorical self-answers, anaphora abuse, tricolon stacking, filler transitions, gerund fragment litanies). Tone anti-patterns (false suspense, unnecessary metaphors, hypothetical openers, asserted clarity, grandiose stakes inflation, teacher-student condescension). Composition anti-patterns (fractal summaries, dead metaphors, signposted conclusions, dismissive optimism). Formatting anti-patterns: em-dash overuse remains forbidden, unicode decoration remains forbidden.

Internal-doc-specific rules from `/internal-doc-standards`. The opening sentence must be the substantive lead, not metadata or boilerplate. Headings must be sentence case with no end punctuation. Acronyms must be defined on first introduction and reused at least twice. Concepts with canonical homes must be linked inline. Metadata must live in document properties, not opening prose. Bold must mark inline key terms on first introduction, not act as general emphasis. Italics must mark defined terms and document titles, not substitute for bold.

Internal-doc-specific overrides. Don't flag a parens-clarification that the override allows. Don't flag a bold table-cell label that the override allows. Don't flag an italic structural label in a repeated pattern that the override allows. The internal-doc catalog explicitly permits these patterns; flagging them would be a mistake.
</what_to_check>

<success_criteria>
The review is complete when:

Every flag carries all four `<verdict_format>` parts — Pattern, Category, Quote, and Rewrite — and the rewrite shows fixed text rather than an instruction.

The summary gives a count, identifies the most frequent category, and assesses overall doc quality.

Co-occurring patterns in a single sentence are flagged as highest priority. A sentence that contains an em-dash, a significance adverb, and a parenthetical aside used for emphasis is three violations in one place and deserves explicit attention.

The audit applies the internal-doc overrides correctly. Parens that aid clarity are not flagged. Bold table-cell labels are not flagged. Italic structural labels in repeated patterns are not flagged.

The audit covers the `<success_criteria>` items from `/internal-doc-standards` as a minimum.
</success_criteria>

<reference_index>

| Skill                     | When to read                                 |
| ------------------------- | -------------------------------------------- |
| `/internal-doc-standards` | Always, before auditing                      |
| `/write-internal-docs`    | When the user wants the rewritten version    |
| `/prose-standards`        | For inherited rules                          |
| `/audit-prose`            | For external-facing prose, not internal docs |

</reference_index>
