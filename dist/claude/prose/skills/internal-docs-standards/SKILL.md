---
name: internal-docs-standards
user-invocable: false
description: >-
  Catalog of anti-patterns and positive patterns for internal team documents (Notion pages, runbooks, scorecards, hiring rubrics, internal policies, competency models, team decision records, design specs). Reference skill loaded by the composed internal-doc skills, not invoked directly. Reached through author-prose and the dispatched prose-auditor agent for the internal-docs kind.
allowed-tools: Read
---

<objective>
The catalog of conventions for internal team documents, extending `/prose-standards`.
</objective>

<reference_note>
This is a reference skill. Composing internal-doc skills load these standards explicitly before writing or auditing. It is not a standalone workflow.
</reference_note>

<scope>
USE this catalog for internal team docs that live in the workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, competency models, onboarding guides, status pages, internal wiki content. Decision records and design specs belong here only as workspace-native documents that no repository or domain workflow already governs.

DO NOT use this catalog for repository-governed engineering artifacts. `CLAUDE.md`, spec-tree specs, ADRs, PDRs, `PLAN.md`, `ISSUES.md`, and `SKILL.md` carry dedicated domain workflows that own their structure, voice, and required sections. Follow the governing repository skill and apply its conventions. This catalog states no authoring rules for those artifacts and never substitutes for that workflow.

DO NOT use this catalog for external-facing prose. For READMEs published to GitHub, blog posts, web copy, customer-facing release notes, marketing material, or other prose written for strangers, use `/prose-standards` instead.

The dividing line has two tests, applied in order. Ownership first: when a repository or domain workflow governs the artifact, that workflow wins regardless of who reads it — audience never overrides ownership. Audience second, among documents no such workflow governs: internal docs assume the reader has context, can skim, and may return to a specific section later, while external prose assumes the reader is meeting the content for the first time and reads top-to-bottom.
</scope>

<inherited_rules>
The following anti-patterns from `/prose-standards` apply unchanged, condensed here to their names and briefest cues. Composing skills invoke `/prose-standards` through the runtime's skill-composition surface when they need the full descriptions and examples behind these names.

Word choice. Avoid significance adverbs ("quietly", "deeply", "fundamentally"), authenticity adverbs ("genuinely", "truly", "actually"), overused vocabulary ("delve", "leverage" as a verb, "robust", "harness"), ornate nouns ("tapestry", "landscape", "paradigm"), and pompous verbs ("serves as", "stands as").

Sentence structure. Avoid negative parallelism ("It's not X — it's Y"), stacked negations, rhetorical self-answers ("The result? Devastating."), anaphora abuse, tricolon stacking, filler transitions ("It's worth noting"), tacked-on significance ("highlighting its importance"), false ranges, gerund fragment litanies, tautological definitions.

Paragraph structure. Avoid short punchy fragments used as standalone paragraphs to manufacture emphasis ("He published this. Openly. In a book."), and avoid the listicle in a trench coat: a list disguised as prose by opening each item with "The first...", "The second...", "The third...". Internal docs reach for lists and tables often, and `<additional_rules>` governs their shape; the anti-pattern here is prose impersonating a list, and the fix is to write the list.

Tone. No false-suspense transitions ("Here's the kicker"), no unnecessary metaphors ("Think of it as..."), no hypothetical openers ("Imagine a world where..."), no performed vulnerability, no asserting clarity ("The truth is simple"), no grandiose stakes inflation, no teacher-student condescension ("Let's break this down"), no vague attributions ("experts argue"), no invented concept labels.

Composition. No fractal summaries, no dead metaphors, no historical analogy stacking, no one-point dilution, no content duplication, no signposted conclusions ("In conclusion..."), no dismissive optimism ("Despite its challenges...").

Formatting. Em-dash overuse remains forbidden. Use em dashes sparingly. The `<title> — <text>` pattern almost always reads better as `<title>: <text>` or as two sentences. Unicode decoration remains forbidden; use plain ASCII equivalents.
</inherited_rules>

<overrides>
The following rules from `/prose-standards` are RELAXED for internal docs.

Bold-first table cells are allowed. External prose forbids bold-first bullets. Internal docs use bold for column-one row labels in tables when those labels function as the section identifier or row key. Competency matrices, scoring rubrics, comparison grids, and most structured tables benefit from bold left-column labels. The reader is scanning the table for a specific row, and bold labels accelerate that.

Parentheses are allowed when they aid clarity. External prose discourages parentheses as decoration. Internal docs use parentheses for three legitimate purposes.

First, to define acronyms on first introduction. Example: "engineering management (EM)". Define only if the acronym will be reused at least twice in the document.

Second, to wrap a clarifying list when the inline form would create comma ambiguity. Example: "the recruiting process (intro call, blank-paper exercise, paid test-drive) produces enough signal." Without the parens, the list runs together with the surrounding sentence and the reader can't tell where the list ends.

Third, for formal notation that doesn't read as prose. Example: "Score 1 to 4 (no neutral midpoint)" or "The set is {a, b, c}."

Parentheses remain forbidden for emphasis ("important", "this is what many miss"), for redundant explanation, and for asides that should be their own sentences carrying their own weight. The test: does the parenthetical content add information the surrounding sentence depends on? If yes, keep. If it's just punch or restatement, cut.

Bold inline labels for paragraph introducers are allowed. External prose forbids bold-first bullets. Internal docs allow bold (or plain) inline labels at the start of paragraphs in procedure docs or structured-reference docs, when each paragraph addresses a distinct labeled topic. Example: "Hiring. Levels are assessed against the same four dimensions. Promotion. Engineers are promoted after they have already operated at the next level."

Italics for structural labels in repeated patterns are allowed. When a document has a repeated structure (every principle has a Lives-it / Fails-it / Probe), the labels can be italicized inline. Example: "*Lives it.* Cares about getting things right. *Fails it.* Defends positions to save face."
</overrides>

<additional_rules>
Rules specific to internal docs.

Lead with the gist. Open every internal doc with the substantive lead sentence. Not metadata, not a "what this page is about" boilerplate, not a fractal summary. The first sentence is the first thing the page says about its actual subject. "Living document. Status: DRAFT. Owner: ..." at the top of a page is the canonical violation.

Status, owner, and dates belong in document metadata. Notion has page properties for these. Other tools have frontmatter, headers, or sidebar metadata. Put status, owner, and last-updated date in the platform-native metadata, not in the opening prose. When they must stay visible in-document, use a small structured callout that a reader can skim past.

Headings are sentence case with no end punctuation. "How this layer is used" is correct. "How This Layer Is Used:" is title-cased and ends with a colon, both of which are wrong. Exceptions are proper nouns that retain their canonical capitalization, e.g., "Have Backbone; Disagree and Commit" as an Amazon Leadership Principle.

Don't repeat the parent page's title in child page headings. If the parent is "Recruiting" and the child is about the hiring scorecard, the child page is titled "Hiring scorecard", not "Recruiting hiring scorecard".

Bold for inline key terms on first introduction. When a section introduces a key term that the reader might want to scan for, bold the term on its first appearance in that section. Don't repeat the bold on subsequent mentions. Don't use bold as general emphasis ("the **most important** thing"); the catalog rule against significance markers still applies.

Avoid: "This is the **most important** part of the loop." Prefer: "A **scorecard** collects one rating per competency."

Italics for terms being defined and document titles. Italics belong on the first introduction of a term being defined, on foreign or unusual words, and on titles of referenced documents. Italics are not a substitute for bold or for general emphasis.

Avoid: "*Do not* skip this step." Prefer: "A *blank-paper exercise* asks the candidate to design a system from scratch." and "The rubric lives in *Hiring scorecard*."

Acronyms are defined on first introduction and reused. Define an acronym with the parenthesis form on first use. Reuse it at least twice afterward, or spell out the full phrase throughout instead. Single-use acronyms add cognitive load without saving space.

Cross-references go inline as hyperlinks. When the doc mentions a concept that has a canonical home in the workspace, link to that home inline on first mention. Don't duplicate the canonical content; link and summarize only what's relevant.

Avoid: "Our levelling framework defines four dimensions (see the Recruiting section for details)." Prefer: "Our [levelling framework](link) defines four dimensions."

Use a "Sources" or "References" section only for repeat citations. When the doc cites the same external source multiple times, or when the citation needs structured fields (author, year, page), collect those citations at the bottom. A "References" section is not a substitute for inline hyperlinks; it's a complement when the inline form would force the same long URL to repeat or when the citation carries metadata the inline link can't.

Avoid: a "References" section listing the three workspace pages the doc already links inline. Prefer: a "Sources" section when one paper is cited in four places, or when the citation carries author, year, and page.

Lists pick the right shape for the content. Numbered lists when order matters or items will be referenced by number ("see step 3"). Bulleted lists when items are parallel and order is incidental. Definition lists, with a short label on the left and an explanation on the right, when each item is identified by a short name and described by a longer body. Definition lists are the recommended alternative to bold-first bullet lists, which the inherited rules forbid as a default pattern.

Avoid: "**Intro call.** Thirty minutes. **Blank-paper exercise.** Ninety minutes." as a bold-first bullet list. Prefer: a definition list with each stage as the label, or a numbered list when a later section says "see step 3".

Tables for structured comparisons. Use a table when two or more dimensions cross. Keep cells concise. If a cell wants to be a paragraph, the content probably wants to live outside the table. Header rows must be visually distinct.

Avoid: a two-column table whose right column runs three sentences per row. Prefer: a table where level crosses dimension and each cell holds a phrase, with the reasoning in prose beneath it.

Callouts sparingly. Reserve callouts for warnings, content that doesn't fit the main flow, or short structured asides. One or two callouts per document. More than that becomes noise. Never use a callout for metadata.

Avoid: five callouts on one page, one of them carrying the owner and last-updated date. Prefer: a single callout warning that the rubric never feeds promotion decisions.

Decisive language for decisions. Internal docs encode decisions. Use decisive language: "We do X" or "The bar is Y". Avoid hedge constructions ("It might be considered to do X", "It could be argued that..."). When the doc documents reasoning, present the reasoning, then state the decision.

Action labels in procedures. In procedure documents, lead each step with the action: "Open the file..." not "First, you'll need to open the file...". The action verb tells the reader what to do; everything before it is overhead.
</additional_rules>

<positive_patterns>
Things internal docs should do.

Scannable hierarchy. Headings, bold key terms, tables, and lists carry the visible structure. A returning reader should find a specific section in five seconds. Walls of unbroken prose hide structure even when the structure is there.

Concrete examples. When stating a rule or convention, give a concrete example that demonstrates it. Internal-doc readers retrieve documents to apply them; examples make the rule applicable.

Per-section context. When sections of the doc cover separate concerns, the first sentence of each section orients the reader to that section's specific concern.
</positive_patterns>

<success_criteria>
The catalog itself is sound when every rule in `<inherited_rules>`, `<overrides>`, and `<additional_rules>` carries its name and rule text, and every override and every example-bearing additional rule carries at least one worked example.

Before declaring a doc finished, check:

The opening sentence is substantive, not boilerplate or metadata.

Every key term the reader might scan for is bolded on first introduction.

Every acronym is defined on first introduction and reused at least twice.

Every concept with a canonical home is linked to that home.

Status, owner, and dates live in document properties or a small structured metadata callout, not in opening prose.

Headings are sentence case with no end punctuation, and don't repeat the parent's title.

Parentheses appear only for acronym definitions, clarifying lists with ambiguity risk, or formal notation. Other parentheticals are either rewritten as separate sentences or cut.

Em dashes appear at most two or three times in the entire document.

Tables have bold left-column labels where appropriate, no paragraph-sized cells, and visually distinct header rows.
</success_criteria>
