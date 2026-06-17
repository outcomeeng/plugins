---
name: write-internal-docs
description: >-
  ALWAYS invoke this skill when writing or editing internal team documents that live in a workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, decision records, design specs, competency models, onboarding guides, status pages, internal wiki content. Use this skill whenever the user is creating a doc intended for colleagues who already have context, not for strangers reading it for the first time. NEVER invoke for external-facing prose like READMEs, blog posts, web copy, customer release notes, or marketing material — use write-prose for those instead. NEVER invoke for chat replies, commit messages, code comments, or agent-facing instructions like SKILL.md and AGENTS.md.
allowed-tools: Read, Edit, Write, Glob, Grep
---

Invoke the `prose:internal-doc-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Write internal team documents that are scannable, decisive, and durable. Apply the catalog from `/internal-doc-standards`, which inherits the prose rules and overrides or extends them where internal-doc conventions differ.
</objective>

<why_internal_docs_are_different>
External prose optimizes for first-read comprehension by a stranger. Internal docs optimize for repeated retrieval by colleagues who already have context. That changes what's helpful.

A colleague returning to a hiring scorecard for the third time doesn't want to re-read the introduction. They want to find their section in five seconds. Bold key terms, tables, definition lists, and inline cross-references earn their keep in internal docs because they accelerate retrieval. The same patterns can read as AI noise in external prose where the reader is meeting the content for the first time.

The `/internal-doc-standards` catalog encodes this calibration. The inherited prose rules still apply for things that are unambiguously bad writing (em-dash overuse, significance adverbs, false suspense). The overrides apply for things prose-skills forbid that internal docs need.
</why_internal_docs_are_different>

<workflow>
1. Read `/internal-doc-standards` for the catalog of conventions and anti-patterns.

2. Understand the document's purpose. Internal docs come in identifiable types: process documentation, decision record, reference page, competency model, scorecard, onboarding guide, status page. Each type has its own conventions. Identify the type before drafting.

3. Identify canonical homes. For each concept the document will reference, locate its canonical home in the workspace. Plan inline hyperlinks to those homes; don't restate canonical content.

4. Draft lead-first. Open with the substantive lead sentence. Not metadata, not boilerplate. Scaffold the rest of the document below the lead.

5. Apply the positive patterns. Scannable headings, concrete examples, decisive language, action labels, cross-links to canonical sources.

6. Apply the formatting overrides where they help. Bold for inline key terms on first introduction. Parens for acronym definitions and clarifying lists. Definition lists instead of bold-first bullets. Italics for terms being defined and document titles.

7. Audit before publishing. Run `/audit-internal-docs` on the draft. Fix flagged violations. The catalog's `<success_criteria>` section is the minimum check.

</workflow>

<doc_type_conventions>
Brief conventions for common internal-doc types.

Decision records. Lead with the decision in one sentence. Then context, options considered, reasoning, consequences. Decisive language throughout; the doc encodes a decision that's been made.

Hiring rubrics and scorecards. Lead with what the rubric measures. Then the scoring scale, then the items. Items are grouped by category. Each item has a behavioral indicator and a source. Scoring guidance is concrete (1 means X, 2 means Y, etc.).

Process / runbook docs. Lead with what the procedure accomplishes. Then a numbered list of steps. Each step leads with the action verb. Failure modes and rollback steps at the end.

Reference / competency model pages. Lead with the framework. Then a structured exposition (table or section per concept). Each concept gets a definition and an example. Cross-link to dependent concepts.

Onboarding guides. Lead with what the new person will know by the end. Then a numbered sequence of milestones with concrete deliverables.

Status pages. Lead with the current status in one sentence. Then context, then next actions. Update from the top; don't append-only.
</doc_type_conventions>

<success_criteria>
The doc is complete when:

The opening sentence is the substantive lead, not metadata or boilerplate.

Headings are sentence case with no end punctuation, and don't repeat the parent page's title.

Every key term that a reader might scan for is bolded on first introduction.

Every acronym is defined on first introduction and reused at least twice in the document.

Every concept with a canonical home in the workspace is hyperlinked to that home inline.

Metadata lives in document properties or a small structured callout, not in opening prose.

The document survives an `/audit-internal-docs` pass with no flagged violations.
</success_criteria>

<reference_index>

| Skill                     | When to read                                 |
| ------------------------- | -------------------------------------------- |
| `/internal-doc-standards` | Always, before writing                       |
| `/audit-internal-docs`    | When the draft is ready for review           |
| `/prose-standards`        | When you need the inherited rules            |
| `/write-prose`            | For external-facing prose, not internal docs |

</reference_index>
