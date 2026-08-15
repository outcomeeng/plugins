# Documentation structure

The structural conventions for the documentation kind — a page in a document set. A prose ADR for a document set selects from these shapes and binds them as rules; the page's writer complies.

## Contents

- Set architecture
- Page types
- Page architecture
- Cross-link topology

## Set architecture

A document set has one canonical home per concept. Each shared concept is defined on exactly one page; every other page links to that home and summarizes only what its own reader needs. The set's terminology is collected before a page is structured: a new page uses the set's established term for every concept it touches and introduces a new term only for a concept the set does not yet name.

Sequencing across pages is a set-level decision. Which page precedes which, which pages are siblings, and where a new page enters the hierarchy are decided in the governing ADR, not improvised per page.

A child page heading does not repeat its parent's title. Under a parent named "Recruiting", the child about the hiring scorecard is titled "Hiring scorecard", not "Recruiting hiring scorecard".

## Page types

Each page type carries its own shape. The ADR names each artifact's type; the shapes are:

Procedure and runbook pages. Lead with what the procedure accomplishes. Then numbered steps under the instruction pack. Failure modes and rollback steps at the end.

Reference pages. Lead with what the reference covers. Then a parallel structure — one section or row per entry — each carrying a definition and an example, cross-linked to dependent concepts.

Conceptual guides. Lead with the idea the reader will hold at the end. Then develop it. The page is read through more than entered, so composition matters more here than anywhere else in the kind.

Tutorials. Lead with what the reader will have built. Then a numbered sequence under the instruction pack, each step producing something the reader can see.

Policies and ungoverned team decision records. Lead with the decision or the rule in one sentence. Then context, options considered, reasoning, consequences. Decisive language throughout. This covers only records no repository or domain workflow governs — a governed ADR or PDR never enters the prose surface.

Ungoverned design specs. Lead with what the design produces and for whom. Then the constraints it works within, the shape of the approach, and the open questions.

Rubrics and scorecards. Lead with what the rubric measures. Then the scoring scale, then the items grouped by category. Each item carries a behavioral indicator and a source; scoring guidance is concrete.

Competency models. Lead with the framework. Then a table or section per concept, cross-linked to dependent concepts.

Onboarding guides. Lead with what the new person will know by the end. Then a numbered sequence of milestones with concrete deliverables.

Status pages. Lead with the current status in one sentence. Then context, then next actions. Update from the top; never append-only.

## Page architecture

Lead with the gist. The page opens with the substantive lead sentence — not metadata, not a "what this page is about" boilerplate, not a fractal summary. "Living document. Status: DRAFT. Owner: ..." at the top of a page is the canonical violation.

Status, owner, and dates belong in metadata. Page properties, frontmatter, headers, or sidebar metadata carry them. When they must stay visible in-document, use a small structured callout a reader can skim past.

Headings are sentence case with no end punctuation. "How this layer is used" is correct. "How This Layer Is Used:" is title-cased and ends with a colon, both wrong. Proper nouns keep their canonical capitalization.

Each section orients in its first sentence. When sections cover separate concerns, the opening sentence of each names that section's concern.

Structure carries the hierarchy. Headings, bold key terms, tables, and lists make the shape visible, and a returning reader finds a specific section in five seconds. Walls of unbroken prose hide structure even when the structure is there.

## Cross-link topology

Cross-references go inline as hyperlinks. When the page mentions a concept with a canonical home — another page in the set or a repository document — link to that home inline on first mention. Link and summarize what is relevant; never duplicate the canonical content.

Avoid: "Our levelling framework defines four dimensions (see the Recruiting section for details)." Prefer: "Our [levelling framework](link) defines four dimensions."

A "Sources" or "References" section is for repeat citations only. Collect citations at the bottom when the same external source is cited several times, or when the citation carries structured fields the inline link cannot. It never substitutes for inline hyperlinks.
