---
name: author-internal-docs
user-invocable: false
description: >-
  Internal-doc authoring guidance — Notion pages, runbooks, scorecards, policies, onboarding guides, and team decision records — composed by author-prose for the internal-docs kind. Reached only through author-prose, never matched directly.
allowed-tools: Read, Edit, Write, Glob, Grep, Skill
---

Invoke the `prose:internal-docs-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

Internal team documents that are scannable, decisive, and durable.

</objective>

<why_internal_docs_are_different>

A colleague returning to a hiring scorecard for the third time doesn't want to re-read the introduction. They want to find their section in five seconds. Bold key terms, tables, definition lists, and inline cross-references are worth the visual weight because they accelerate that retrieval, and the same patterns read as noise in prose a stranger meets once.

The `/internal-docs-standards` catalog encodes the calibration: inherited rules for what is unambiguously bad writing, overrides for what the base catalog forbids that internal docs need.

</why_internal_docs_are_different>

<workflow>

1. Identify the document type — process documentation, ungoverned team decision record, ungoverned design spec, reference page, competency model, scorecard, onboarding guide, status page. Each type has its own conventions in `<doc_type_conventions>`.

2. Identify canonical homes. For each concept the document will reference, locate its canonical home — a workspace page or a repository document. Plan inline hyperlinks to those homes; don't restate canonical content.

3. Draft lead-first. Open with the substantive lead sentence — not metadata, not boilerplate. Scaffold the rest of the document below the lead.

4. Apply the positive patterns: scannable headings, concrete examples, decisive language, action labels, cross-links to canonical sources.

5. Apply the formatting overrides where they help. `/internal-docs-standards` `<overrides>` carries them with worked examples; each one relaxes a base rule that internal docs need back.

</workflow>

<doc_type_conventions>

Ungoverned team decision records. Lead with the decision in one sentence. Then context, options considered, reasoning, consequences. Decisive language throughout; the doc encodes a decision that's been made. These conventions cover only decision records no repository or domain workflow governs — kind detection routed a governed ADR or PDR away before this skill loaded.

Ungoverned design specs. Lead with what the design produces and for whom. Then the constraints it works within, the shape of the approach, and the open questions.

Hiring rubrics and scorecards. Lead with what the rubric measures. Then the scoring scale, then the items grouped by category. Each item has a behavioral indicator and a source; scoring guidance is concrete (1 means X, 2 means Y).

Process / runbook docs. Lead with what the procedure accomplishes. Then numbered steps, each leading with the action verb. Failure modes and rollback steps at the end.

Reference / competency model pages. Lead with the framework. Then a structured exposition — table or section per concept — with a definition and an example each, cross-linked to dependent concepts.

Onboarding guides. Lead with what the new person will know by the end. Then a numbered sequence of milestones with concrete deliverables.

Status pages. Lead with the current status in one sentence. Then context, then next actions. Update from the top; don't append-only.

</doc_type_conventions>

<success_criteria>

The opening sentence is the substantive lead, not metadata or boilerplate.

Headings are sentence case with no end punctuation, and don't repeat the parent page's title.

Every key term a reader might scan for is bolded on first introduction, and every acronym is defined on first introduction and reused at least twice.

Every concept with a canonical home — a workspace page or a repository document — is hyperlinked to that home inline; metadata lives in document properties or a small structured callout.

</success_criteria>
