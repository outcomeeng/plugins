# Documentation style layer

The style rules for the documentation kind — a page in a document set: product documentation, wiki pages, runbooks, reference, policies, rubrics, onboarding guides, READMEs. The base catalog and the voice canon bind except where the overrides below relax them. The reader scans the page and enters it at a point, which is what every relaxation and cap below serves. Structural conventions for the kind — page types, lead-first openings, heading hierarchy, cross-link topology — live in the matching `/prose-architecture-standards` reference.

## Contents

- Overrides
- Sentence shape
- Typography
- Lists and callouts
- Decisive language

## Overrides

The following base rules are RELAXED for a documentation page.

Numbered-step imperatives stand alone. The base rule against listicles governs a prose argument. A procedure is a numbered list by design, and each step is an imperative sentence that would read as a commanding fragment in an essay. The instruction pack governs what those steps say.

Bold table cells are allowed for row keys. External prose forbids bold-first bullets. A documentation page uses bold for column-one row labels when those labels are the row key the reader scans for. Example: a levelling matrix whose first column reads "**Ownership**", "**Craft**", "**Communication**".

Parentheses are allowed when they aid clarity, for three purposes. First, to define an acronym on first introduction: "engineering management (EM)". Second, to wrap a clarifying list when the inline form would create comma ambiguity: "the recruiting process (intro call, blank-paper exercise, paid test-drive) produces enough signal." Third, for formal notation that does not read as prose: "Score 1 to 4 (no neutral midpoint)".

Parentheses remain forbidden for emphasis, for redundant explanation, and for asides that should be their own sentences. The test: does the parenthetical carry information the surrounding sentence depends on? If yes, keep it. If it is punch or restatement, cut it.

Bold inline labels for paragraph introducers are allowed in a procedure or structured-reference page, when each paragraph addresses a distinct labeled topic. Example: "**Hiring.** Levels are assessed against the same four dimensions. **Promotion.** Engineers are promoted after they have already operated at the next level."

Italics for structural labels in repeated patterns are allowed. When a page has a repeated structure — every principle carries a Lives-it, a Fails-it, and a Probe — the labels can be italicized inline. Example: "*Lives it.* Cares about getting things right. *Fails it.* Defends positions to save face."

## Sentence shape

A descriptive sentence caps at 25 words and splits over the cap. Simple tenses only: present for facts, imperative for instructions, simple past for a prerequisite already performed. No perfect tenses and no progressive forms. No verbal "-ing" clauses: "the command exits and prints a summary", never "the command exits, printing a summary" — nouns ending in -ing ("the setting", "a warning") are words, not violations. Noun clusters cap at three nouns; break a longer one with a preposition. Paragraphs cap at six sentences and carry one topic.

## Typography

**Bold for inline key terms on first introduction.** When a section introduces a key term the reader might scan for, bold it on first appearance in that section. Don't repeat the bold afterward, and don't use bold as general emphasis.

Avoid: "This is the **most important** part of the loop." Prefer: "A **scorecard** collects one rating per competency."

**Italics for terms being defined and for document titles.** Italics belong on the first introduction of a term being defined, on foreign or unusual words, and on titles of referenced documents. Italics never substitute for bold or for general emphasis.

Avoid: "*Do not* skip this step." Prefer: "A *blank-paper exercise* asks the candidate to design a system from scratch."

**Acronyms are defined on first introduction and reused.** Define with the parenthesis form on first use, then reuse at least twice, or spell out the full phrase throughout instead. A single-use acronym costs the reader more than it saves.

## Lists and callouts

Lists pick the shape the content has. Numbered when order matters or items will be referenced by number. Bulleted when items are parallel and order is incidental. A definition list — short label left, explanation right — when each item is identified by a short name and described by a longer body. Definition lists are the alternative to the bold-first bullet list the base catalog forbids.

Avoid: "**Intro call.** Thirty minutes. **Blank-paper exercise.** Ninety minutes." as a bold-first bullet list. Prefer: a definition list with each stage as the label.

Callouts sparingly. Reserve them for warnings, content that does not fit the main flow, or short structured asides. One or two per page; more becomes noise. Never use a callout for metadata.

Every rule carries an example. When the page states a rule or convention, give an example that demonstrates it. Documentation readers retrieve pages to apply them, and the example is what makes the rule applicable.

## Decisive language

A page that encodes a decision states it: "We do X" or "The bar is Y". Avoid hedge constructions. Present the reasoning, then state the decision.
