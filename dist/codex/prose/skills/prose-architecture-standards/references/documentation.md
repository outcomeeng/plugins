# Documentation structure

The structural conventions for the documentation kind — a page in a document set. A prose ADR for a document set selects from these shapes and binds them as rules; the page's writer complies.

## Contents

- Set architecture
- Page types
- Page architecture
- Cross-link topology

## Set architecture

`documentation-set-home`: A document set has one canonical home per concept. Each shared concept is defined on exactly one page; every other page links to that home and summarizes only what its own reader needs. The set's terminology is collected before a page is structured, and the ADR records which page is each concept's home. One term per concept is the voice canon's rule; what the ADR decides is where each term lives.

`documentation-set-sequencing`: Sequencing across pages is a set-level decision. Which page precedes which, which pages are siblings, and where a new page enters the hierarchy are decided in the governing ADR, not improvised per page.

`documentation-child-heading`: A child page heading does not repeat its parent's title. Under a parent named "Recruiting", the child about the hiring scorecard is titled "Hiring scorecard", not "Recruiting hiring scorecard".

## Page types

Each page type carries its own shape. The ADR names each artifact's type; the shapes are:

`documentation-page-procedure`: Procedure and runbook pages. Lead with what the procedure accomplishes. Then numbered steps under the instruction pack. Failure modes and rollback steps at the end.

`documentation-page-reference`: Reference pages. Lead with what the reference covers. Then a parallel structure — one section or row per entry — each carrying a definition and an example, cross-linked to dependent concepts.

`documentation-page-concept`: Conceptual guides. Lead with the idea the reader will hold at the end. Then develop it. The page is read through more than entered, so composition matters more here than anywhere else in the kind.

`documentation-page-tutorial`: Tutorials. Lead with what the reader will have built. Then a numbered sequence under the instruction pack, each step producing something the reader can see.

`documentation-page-policy`: Policies and ungoverned team decision records. Lead with the decision or the rule in one sentence. Then context, options considered, reasoning, consequences. Decisive language throughout. This covers only records no repository or domain workflow governs — a governed ADR or PDR never enters the prose surface.

`documentation-page-design-spec`: Ungoverned design specs. Lead with what the design produces and for whom. Then the constraints it works within, the shape of the approach, and the open questions.

`documentation-page-rubric`: Rubrics and scorecards. Lead with what the rubric measures. Then the scoring scale, then the items grouped by category. Each item carries a behavioral indicator and a source; scoring guidance is concrete.

`documentation-page-competency-model`: Competency models. Lead with the framework. Then a table or section per concept, cross-linked to dependent concepts.

`documentation-page-onboarding`: Onboarding guides. Lead with what the new person will know by the end. Then a numbered sequence of milestones with concrete deliverables.

`documentation-page-status`: Status pages. Lead with the current status in one sentence. Then context, then next actions. Update from the top; never append-only.

## Page architecture

`documentation-page-lead`: Lead with the gist. The page opens with the substantive lead sentence — not metadata, not a "what this page is about" boilerplate, not a fractal summary. "Living document. Status: DRAFT. Owner: ..." at the top of a page is the canonical violation.

`documentation-page-metadata`: Status, owner, and dates belong in metadata. Page properties, frontmatter, headers, or sidebar metadata carry them. When they must stay visible in-document, use a small structured callout a reader can skim past.

`documentation-section-orientation`: Each section orients in its first sentence. When sections cover separate concerns, the opening sentence of each names that section's concern.

`documentation-visible-hierarchy`: Structure carries the hierarchy. Headings, bold key terms, tables, and lists make the shape visible, and a returning reader finds a specific section in five seconds. Walls of unbroken prose hide structure even when the structure is there.

## Cross-link topology

`documentation-inline-links`: Cross-references go inline as hyperlinks. When the page mentions a concept with a canonical home — another page in the set or a repository document — link to that home inline on first mention. Link and summarize what is relevant; never duplicate the canonical content.

Avoid: "Our levelling framework defines four dimensions (see the Recruiting section for details)." Prefer: "Our [levelling framework](link) defines four dimensions."

`documentation-sources-section`: A "Sources" or "References" section is for repeat citations only. Collect citations at the bottom when the same external source is cited several times, or when the citation carries structured fields the inline link cannot. It never substitutes for inline hyperlinks.
