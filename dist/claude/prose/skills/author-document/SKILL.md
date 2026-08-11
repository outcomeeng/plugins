---
name: author-document
user-invocable: false
description: >-
  Document authoring guidance — product documentation, wiki pages, runbooks, reference, policies, rubrics, onboarding guides, READMEs — composed by author-prose for the document kind. Reached only through author-prose, never matched directly.
allowed-tools: Read, Edit, Write, Glob, Grep, Skill
---

Invoke the `prose:document-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

A page in a document set that opens with its substance, is scannable at any entry point, and carries the rules of every feature it contains.

</objective>

<why_the_document_kind_is_shaped_this_way>

A colleague returning to a hiring scorecard for the third time does not re-read the introduction. They want their section in five seconds. A developer hitting an API reference page from a search result never sees the page above it. Bold key terms, tables, definition lists, and inline cross-references earn their visual weight because they accelerate that entry, and the same patterns read as noise in a piece a stranger meets once and reads through.

`/document-standards` encodes the calibration: the shared voice canon, inherited rules for what is unambiguously bad writing, and overrides for what the base catalog forbids that a scanned page needs back.

</why_the_document_kind_is_shaped_this_way>

<workflow>

1. Identify the page type — procedure or runbook, reference, conceptual guide, tutorial, policy, rubric, competency model, onboarding guide, status page, ungoverned team decision record, ungoverned design spec. Each carries its own shape in `<page_type_conventions>`.

2. Collect the set's established terms for every concept the page touches. The one-term-one-meaning rule in the voice canon binds new text to the existing vocabulary; introduce a new term only for a concept the set does not yet name.

3. Identify canonical homes. For each concept the page references, locate its canonical home — another page in the set or a repository document. Plan inline hyperlinks; never restate canonical content.

4. Draft lead-first. Open with the substantive lead sentence, then scaffold the rest below it.

5. Apply `/document-standards` `<additional_rules>` as the page takes shape: the sentence caps, heading case, key-term bolding, cross-links, list and callout shape, decisive language.

6. Apply each triggered rule pack from `/prose-standards` `<rule_packs>`. A procedure triggers the instruction pack — 20-word steps, one instruction each, condition first, action verb leading. A table triggers the table pack.

7. Apply the formatting overrides where they help. `/document-standards` `<overrides>` carries them with worked examples; each relaxes a base rule a scanned page needs back.

</workflow>

<page_type_conventions>

Procedure and runbook pages. Lead with what the procedure accomplishes. Then numbered steps under the instruction pack. Failure modes and rollback steps at the end.

Reference pages. Lead with what the reference covers. Then a parallel structure — one section or row per entry — each carrying a definition and an example, cross-linked to dependent concepts.

Conceptual guides. Lead with the idea the reader will hold at the end. Then develop it. The page is read through more than entered, so composition matters more here than anywhere else in the kind.

Tutorials. Lead with what the reader will have built. Then a numbered sequence under the instruction pack, each step producing something the reader can see.

Policies and ungoverned team decision records. Lead with the decision or the rule in one sentence. Then context, options considered, reasoning, consequences. Decisive language throughout. This covers only records no repository or domain workflow governs — a governed ADR or PDR never reaches this skill.

Ungoverned design specs. Lead with what the design produces and for whom. Then the constraints it works within, the shape of the approach, and the open questions.

Rubrics and scorecards. Lead with what the rubric measures. Then the scoring scale, then the items grouped by category. Each item carries a behavioral indicator and a source; scoring guidance is concrete.

Competency models. Lead with the framework. Then a table or section per concept, cross-linked to dependent concepts.

Onboarding guides. Lead with what the new person will know by the end. Then a numbered sequence of milestones with concrete deliverables.

Status pages. Lead with the current status in one sentence. Then context, then next actions. Update from the top; never append-only.

</page_type_conventions>

<success_criteria>

- The opening sentence is the substantive lead, not metadata or boilerplate.
- Every descriptive sentence is inside the 25-word cap, in a simple tense, with no verbal "-ing" clause.
- Every procedure obeys the instruction pack and every table obeys the table pack.
- Headings are sentence case with no end punctuation and do not repeat the parent's title.
- Every key term a reader might scan for is bolded on first introduction, and every acronym is defined on first introduction and reused at least twice.
- Every concept with a canonical home is hyperlinked to that home inline; metadata lives in page properties or a small structured callout.
- Zero instances of any `/prose-standards` pattern outside the declared overrides.

</success_criteria>
