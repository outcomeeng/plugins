---
name: write-internal-docs
description: >-
  ALWAYS invoke this skill when writing or editing internal team documents that live in a workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, competency models, onboarding guides, status pages, internal wiki content, and team decision records and design specs. NEVER invoke for a doc a repository or domain workflow already owns — specs, ADRs, PDRs, PLAN.md, ISSUES.md, SKILL.md, CLAUDE.md — follow that workflow instead. NEVER invoke for writing aimed at outside readers even when it is drafted in the workspace — public status pages, release notes, marketing copy, READMEs, blog posts — use write-prose.
allowed-tools: Read, Edit, Write, Glob, Grep, Skill
---

Invoke the `prose:internal-doc-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Internal team documents that are scannable, decisive, and durable.
</objective>

<artifact_ownership>
Artifact ownership outranks audience. A document read only by colleagues still belongs to its governing workflow whenever a repository or domain owns it, so "it lives in a workspace" never routes an artifact here on its own.

Repository-governed engineering artifacts — `CLAUDE.md`, spec-tree specs, ADRs, PDRs, `PLAN.md`, `ISSUES.md`, `SKILL.md` — carry dedicated domain workflows that own their structure, voice, and required sections. Write those through the governing repository skill. This skill's conventions do not apply to them and never substitute for that workflow.

Apply two tests before drafting. Ownership first: when a repository or domain workflow governs the artifact, stop and route there. Audience second: when the writing addresses readers outside the team — a public status page, customer release notes, marketing copy — route to `/write-prose`, even though the draft lives in the workspace. Only a document that passes both tests is an internal doc.
</artifact_ownership>

<why_internal_docs_are_different>
External prose optimizes for first-read comprehension by a stranger. Internal docs optimize for repeated retrieval by colleagues who already have context. That changes what's helpful.

A colleague returning to a hiring scorecard for the third time doesn't want to re-read the introduction. They want to find their section in five seconds. Bold key terms, tables, definition lists, and inline cross-references are worth the visual weight in internal docs because they accelerate retrieval. The same patterns can read as AI noise in external prose where the reader is meeting the content for the first time.

The `/internal-doc-standards` catalog encodes this calibration. The inherited prose rules still apply for things that are unambiguously bad writing (em-dash overuse, significance adverbs, false suspense). The overrides apply for things prose-skills forbid that internal docs need.
</why_internal_docs_are_different>

<workflow>
1. Read `/internal-doc-standards` for the catalog of conventions and anti-patterns.

2. Confirm ownership before drafting. Apply the `<artifact_ownership>` test: when a repository or domain workflow governs the artifact, stop and route to that workflow. Then identify the type — process documentation, workspace-native decision record, reference page, competency model, scorecard, onboarding guide, status page. Each type has its own conventions.

3. Identify canonical homes. For each concept the document will reference, locate its canonical home in the workspace. Plan inline hyperlinks to those homes; don't restate canonical content.

4. Draft lead-first. Open with the substantive lead sentence. Not metadata, not boilerplate. Scaffold the rest of the document below the lead.

5. Apply the positive patterns. Scannable headings, concrete examples, decisive language, action labels, cross-links to canonical sources.

6. Apply the formatting overrides where they help. Bold for inline key terms on first introduction. Parens for acronym definitions and clarifying lists. Definition lists instead of bold-first bullets. Italics for terms being defined and document titles.

7. Audit before publishing. Run `/audit-internal-docs` on the draft. Fix flagged violations. The catalog's `<success_criteria>` section is the minimum check.

</workflow>

<doc_type_conventions>
Brief conventions for common internal-doc types.

Workspace-native decision records. Lead with the decision in one sentence. Then context, options considered, reasoning, consequences. Decisive language throughout; the doc encodes a decision that's been made. These conventions cover only decision records no repository or domain workflow governs — an ADR or PDR follows its governing repository skill, not this shape.

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

<failure_modes>
**The ownership test passed and the audience test never ran.**

Claude confirmed that no repository workflow governed a status page living in the workspace, then drafted it against this skill's conventions. The page addressed customers, so the prose skills owned it, and outward-facing copy inherited internal-doc formatting. Ownership alone never establishes that a document is an internal doc: apply both `<artifact_ownership>` tests, and route an outward-facing draft to `/write-prose` even when it lives in the workspace beside genuine internal docs.
</failure_modes>

<reference_index>

| Skill                     | When to read                                 |
| ------------------------- | -------------------------------------------- |
| `/internal-doc-standards` | Always, before writing                       |
| `/audit-internal-docs`    | When the draft is ready for review           |
| `/prose-standards`        | For the inherited rules                      |
| `/write-prose`            | For external-facing prose, not internal docs |

</reference_index>
