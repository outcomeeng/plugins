---
name: document-standards
user-invocable: false
description: >-
  Standards for the document kind — a page in a document set: product documentation, wiki pages, runbooks, reference, policies, rubrics, onboarding guides, READMEs. Reference skill loaded by the composed document skills, not invoked directly.
allowed-tools: Read
---

<objective>
The document kind's standards layer over `/prose-standards` — the shared voice canon, inherited rules, the typographic overrides a scanned page needs, and the page-architecture and sentence rules for a page a reader enters at a point.
</objective>

<reference_note>
This is a reference skill. `/author-document` and `/audit-document` load it; the routers reach it only through them. Its `<voice_canon>` renders from the same authored fragment as the plugin's shipped `prose` output style and every other kind layer, so a change to that canon changes every voice the plugin ships.
</reference_note>

<voice_canon>
The shared voice rules, transcluded from the authored canon every kind and the shipped output style render from — one source, every surface.

{!% include 'prose/voice/fragment.md' %!}

</voice_canon>

<inherited_rules>
Every `/prose-standards` anti-pattern applies unchanged except where `<overrides>` relaxes it, condensed here to names and briefest cues. Composing skills load `/prose-standards` for the full descriptions and examples.

Word choice. Avoid significance adverbs ("quietly", "deeply", "fundamentally"), authenticity adverbs ("genuinely", "truly", "actually"), overused vocabulary ("delve", "leverage" as a verb, "robust", "harness"), ornate nouns ("tapestry", "landscape", "paradigm"), and pompous verbs ("serves as", "stands as").

Sentence structure. Avoid negative parallelism, stacked negations, rhetorical self-answers, anaphora abuse, tricolon stacking, filler transitions, tacked-on significance, false ranges, gerund fragment litanies, tautological definitions, redundant paired examples.

Paragraph structure. Avoid punchy fragments used as standalone paragraphs to manufacture emphasis. Avoid the listicle in a trench coat: a list disguised as prose by opening each item with "The first...", "The second...". Documents reach for lists and tables often, and `<additional_rules>` governs their shape; the anti-pattern is prose impersonating a list, and the fix is to write the list.

Tone. No false-suspense transitions, no unnecessary metaphors, no hypothetical openers, no performed vulnerability, no asserted clarity, no stakes inflation, no teacher-student condescension, no vague attributions, no invented concept labels.

Composition. No fractal summaries, no dead metaphors, no historical analogy stacking, no one-point dilution, no content duplication, no signposted conclusions, no dismissive optimism.

Formatting. Em-dash overuse remains forbidden. The `<title> — <text>` pattern almost always reads better as `<title>: <text>` or as two sentences. Unicode decoration remains forbidden; use plain ASCII equivalents.

Rule packs. The `/prose-standards` `<rule_packs>` bind wherever their feature appears in the page — the instruction pack on every procedure, the table pack on every table.
</inherited_rules>

<overrides>
The following base rules are RELAXED for a document, because the reader scans it and enters it at a point.

Numbered-step imperatives stand alone. The base rule against listicles governs a prose argument. A procedure is a numbered list by design, and each step is an imperative sentence that would read as a commanding fragment in an essay. The instruction pack governs what those steps say.

Bold table cells are allowed for row keys. External prose forbids bold-first bullets. A document uses bold for column-one row labels when those labels are the row key the reader scans for. Example: a levelling matrix whose first column reads "**Ownership**", "**Craft**", "**Communication**".

Parentheses are allowed when they aid clarity, for three purposes. First, to define an acronym on first introduction: "engineering management (EM)". Second, to wrap a clarifying list when the inline form would create comma ambiguity: "the recruiting process (intro call, blank-paper exercise, paid test-drive) produces enough signal." Third, for formal notation that does not read as prose: "Score 1 to 4 (no neutral midpoint)".

Parentheses remain forbidden for emphasis, for redundant explanation, and for asides that should be their own sentences. The test: does the parenthetical carry information the surrounding sentence depends on? If yes, keep it. If it is punch or restatement, cut it.

Bold inline labels for paragraph introducers are allowed in a procedure or structured-reference page, when each paragraph addresses a distinct labeled topic. Example: "**Hiring.** Levels are assessed against the same four dimensions. **Promotion.** Engineers are promoted after they have already operated at the next level."

Italics for structural labels in repeated patterns are allowed. When a page has a repeated structure — every principle carries a Lives-it, a Fails-it, and a Probe — the labels can be italicized inline. Example: "*Lives it.* Cares about getting things right. *Fails it.* Defends positions to save face."
</overrides>

<additional_rules>
Rules specific to a page in a document set. The `<voice_canon>` above already governs word choice, active voice, and one-term-one-meaning; these add what a scanned page needs beyond it.

**Sentence shape.** A descriptive sentence caps at 25 words and splits over the cap. Simple tenses only: present for facts, imperative for instructions, simple past for a prerequisite already performed. No perfect tenses and no progressive forms. No verbal "-ing" clauses: "the command exits and prints a summary", never "the command exits, printing a summary" — nouns ending in -ing ("the setting", "a warning") are words, not violations. Noun clusters cap at three nouns; break a longer one with a preposition. Paragraphs cap at six sentences and carry one topic.

**Lead with the gist.** Open with the substantive lead sentence. Not metadata, not a "what this page is about" boilerplate, not a fractal summary. The first sentence is the first thing the page says about its actual subject. "Living document. Status: DRAFT. Owner: ..." at the top of a page is the canonical violation.

**Status, owner, and dates belong in metadata.** Page properties, frontmatter, headers, or sidebar metadata carry them. When they must stay visible in-document, use a small structured callout a reader can skim past.

**Headings are sentence case with no end punctuation.** "How this layer is used" is correct. "How This Layer Is Used:" is title-cased and ends with a colon, both wrong. Proper nouns keep their canonical capitalization.

**A child page heading does not repeat its parent's title.** Under a parent named "Recruiting", the child about the hiring scorecard is titled "Hiring scorecard", not "Recruiting hiring scorecard".

**Bold for inline key terms on first introduction.** When a section introduces a key term the reader might scan for, bold it on first appearance in that section. Don't repeat the bold afterward, and don't use bold as general emphasis.

Avoid: "This is the **most important** part of the loop." Prefer: "A **scorecard** collects one rating per competency."

**Italics for terms being defined and for document titles.** Italics belong on the first introduction of a term being defined, on foreign or unusual words, and on titles of referenced documents. Italics never substitute for bold or for general emphasis.

Avoid: "*Do not* skip this step." Prefer: "A *blank-paper exercise* asks the candidate to design a system from scratch."

**Acronyms are defined on first introduction and reused.** Define with the parenthesis form on first use, then reuse at least twice, or spell out the full phrase throughout instead. A single-use acronym costs the reader more than it saves.

**Cross-references go inline as hyperlinks.** When the page mentions a concept with a canonical home — another page in the set or a repository document — link to that home inline on first mention. Link and summarize what is relevant; never duplicate the canonical content.

Avoid: "Our levelling framework defines four dimensions (see the Recruiting section for details)." Prefer: "Our [levelling framework](link) defines four dimensions."

**A "Sources" or "References" section is for repeat citations only.** Collect citations at the bottom when the same external source is cited several times, or when the citation carries structured fields the inline link cannot. It never substitutes for inline hyperlinks.

**Lists pick the shape the content has.** Numbered when order matters or items will be referenced by number. Bulleted when items are parallel and order is incidental. A definition list — short label left, explanation right — when each item is identified by a short name and described by a longer body. Definition lists are the alternative to the bold-first bullet list the inherited rules forbid.

Avoid: "**Intro call.** Thirty minutes. **Blank-paper exercise.** Ninety minutes." as a bold-first bullet list. Prefer: a definition list with each stage as the label.

**Callouts sparingly.** Reserve them for warnings, content that does not fit the main flow, or short structured asides. One or two per page; more becomes noise. Never use a callout for metadata.

**Decisive language for decisions.** A page that encodes a decision states it: "We do X" or "The bar is Y". Avoid hedge constructions. Present the reasoning, then state the decision.

**Structure carries the hierarchy.** Headings, bold key terms, tables, and lists make the shape visible, and a returning reader finds a specific section in five seconds. Walls of unbroken prose hide structure even when the structure is there.

**Every rule carries an example.** When the page states a rule or convention, give an example that demonstrates it. Document readers retrieve pages to apply them, and the example is what makes the rule applicable.

**Each section orients in its first sentence.** When sections cover separate concerns, the opening sentence of each names that section's concern.
</additional_rules>

<success_criteria>
The catalog itself is sound when every rule in `<inherited_rules>`, `<overrides>`, and `<additional_rules>` carries its name and rule text, and every override carries at least one worked example.

A document meets this layer when:

The opening sentence is substantive, not boilerplate or metadata.

Every descriptive sentence is inside the 25-word cap, in a simple tense, with no verbal "-ing" clause; noun clusters and paragraphs are inside their caps.

Every key term the reader might scan for is bolded on first introduction, and every acronym is defined on first introduction and reused at least twice.

Every concept with a canonical home is linked to that home inline.

Status, owner, and dates live in page metadata or a small structured callout, not in opening prose.

Headings are sentence case with no end punctuation, and do not repeat the parent's title.

Parentheses appear only for acronym definitions, clarifying lists with ambiguity risk, or formal notation.

Em dashes appear at most two or three times in the whole page.

Every triggered rule pack was applied: the instruction pack on each procedure, the table pack on each table.
</success_criteria>
