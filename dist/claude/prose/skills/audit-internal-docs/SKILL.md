---
name: audit-internal-docs
description: >-
  ALWAYS invoke this skill when reviewing, auditing, or cleaning up the writing in internal team documents that live in a workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, competency models, onboarding guides, status pages, internal wiki content, and team decision records and design specs. NEVER invoke for a doc a repository or domain workflow already owns — specs, ADRs, PDRs, PLAN.md, ISSUES.md, SKILL.md, CLAUDE.md — follow that workflow instead. NEVER invoke for writing aimed at outside readers even when it is drafted in the workspace — public status pages, release notes, marketing copy, READMEs, blog posts — use audit-prose.
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

Repository-governed engineering artifacts — `CLAUDE.md`, spec-tree specs, ADRs, PDRs, `PLAN.md`, `ISSUES.md`, `SKILL.md` — carry dedicated domain workflows that own their structure, voice, and required sections. Route their review to the governing repository skill. Auditing them against this catalog would flag conventions their governing workflow requires.

Apply two tests before reviewing. Ownership first: when a repository or domain workflow governs the artifact, stop and route there. Audience second: when the document addresses readers outside the team — a public status page, customer release notes, marketing copy — route the review to `/audit-prose`, even though the draft lives in the workspace. Only a document that passes both tests is an internal doc.
</artifact_ownership>

<workflow>
1. Read `/internal-doc-standards` for the catalog.

2. Confirm ownership. Apply the `<artifact_ownership>` test: when a repository or domain workflow governs the document, stop and route the review to that workflow.

3. Read the document under review — whatever the invoking turn names, pastes, or points to. When that turn names no document, ask which one before sweeping anything.

4. Flag each violation. Name the specific pattern and the category it belongs to, drawing the category from the `<what_to_check>` sweep list.

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
Sweep every category below. `/internal-doc-standards` carries the rule text and the examples; this list names the categories so no section goes unswept.

Inherited categories, from that catalog's `<inherited_rules>`:

- Word choice
- Sentence structure
- Paragraph structure
- Tone
- Composition
- Formatting

Internal-doc categories, from its `<additional_rules>` and `<success_criteria>`:

- Lead-first opening
- Heading case and parent-title repetition
- Metadata placement
- Acronym definition and reuse
- Cross-reference linking
- Bold and italic usage
- List and table shape
- Callout density
- Decisive language and action labels

Overrides, from its `<overrides>`: parens that aid clarity, bold table-cell labels, bold inline paragraph introducers, and italic structural labels in repeated patterns. Read the override text before flagging any of these — the catalog permits them deliberately, so a flag against one is a false positive.

Each override is bounded, and every use outside its bounds stays a violation to sweep. Flag parens carrying emphasis or redundant restatement, bold acting as general emphasis, and italics standing in for bold.
</what_to_check>

<success_criteria>
The review is complete when:

Every flag carries all four `<verdict_format>` parts — Pattern, Category, Quote, and Rewrite — and the rewrite shows fixed text rather than an instruction.

The summary's violation count matches the number of flags actually listed, and the category it names as most frequent is the one those flags carry most often.

A sentence carrying two or more co-occurring patterns produces one flag naming every pattern present, and those flags are listed before the single-pattern ones. A sentence with an em-dash, a significance adverb, and a parenthetical aside used for emphasis yields one flag naming all three, never three separate flags.

The audit applies the internal-doc overrides correctly. Parens that aid clarity are not flagged. Bold table-cell labels are not flagged. Italic structural labels in repeated patterns are not flagged.

The audit covers the `<success_criteria>` items from `/internal-doc-standards` as a minimum.
</success_criteria>

<failure_modes>
**The ownership test passed and the audience test never ran.**

Claude confirmed that no repository workflow governed a status page living in the workspace, then reviewed it against this catalog. The page addressed customers, so the prose skills owned its conventions, and the review applied internal-doc rules to outward-facing copy. Ownership alone never establishes that a document is an internal doc: apply both `<artifact_ownership>` tests, and route an outward-facing draft to `/audit-prose` even when it lives in the workspace beside genuine internal docs.
</failure_modes>

<reference_index>

| Skill                     | When to read                                 |
| ------------------------- | -------------------------------------------- |
| `/internal-doc-standards` | Always, before auditing                      |
| `/write-internal-docs`    | When the user wants the rewritten version    |
| `/prose-standards`        | For inherited rules                          |
| `/audit-prose`            | For external-facing prose, not internal docs |

</reference_index>
