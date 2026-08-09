---
name: author-prose
description: >-
  ALWAYS invoke this skill when writing or editing any text for human readers — documents, web pages, articles, product docs, UI text, error messages, notifications, emails, READMEs, release notes, marketing copy, and internal team pages. NEVER invoke for chat responses to the user (no matter how long), code comments, commit messages, or agent-facing instructions like SKILL.md.
allowed-tools: Read, Edit, Write, Glob, Grep, Skill,{!% if target == 'claude' %!} Agent{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}}{!% endif %!}
---

{!% require_skill 'prose:prose-standards' %!}

<objective>

Human-facing text drafted against its kind's standards and approved by a `prose-auditor` pass.

</objective>

<constraints>

- NEVER write the text before the kind is resolved — a draft against the wrong kind's standards reads wrong in ways later editing does not repair.
- NEVER guess an ambiguous kind or invent a style outside the taxonomy — ask the user to select a kind.
- NEVER author a repository- or domain-governed artifact here — ownership routes to the governing workflow before any other test runs.

</constraints>

<workflow>

1. Classify the text through `/prose-standards` `<kind_detection>` — the ordered procedure is pre-loaded above. Ownership routes away; ambiguity asks the user; every other text resolves to exactly one kind: copy, interface, docs, or internal-docs.

2. Invoke the kind's composed author skill via the Skill tool: `prose:author-copy`, `prose:author-interface`, `prose:author-docs`, or `prose:author-internal-docs`. That skill loads its standards layer and carries the kind's writing guidance and workflow.

3. For a document whose parts differ in kind — a docs page with embedded UI strings, a landing page with an essay — apply each part's kind. Classify per part, not per file.

4. Write or edit the text applying the base catalog and the kind's layer together. Zero tolerance for the base anti-patterns; the kind's overrides are the only sanctioned relaxations.

5. Direct an audit pass: dispatch the `prose-auditor` agent on the result, naming the resolved kind in the dispatch when detection needed the user's choice. Fix findings and re-audit until the verdict is `APPROVED`.

</workflow>

<success_criteria>

- The kind was resolved by the detection procedure or an explicit user choice before drafting began.
- The text was written through the kind's composed author skill, not from the router's own judgment.
- Mixed documents received per-part classification.
- A `prose-auditor` dispatch returned `APPROVED` on the final text.

</success_criteria>

<reference_index>

| Skill                                                                        | When to read                               |
| ---------------------------------------------------------------------------- | ------------------------------------------ |
| `/prose-standards`                                                           | Always — detection procedure and catalog   |
| `/author-copy`, `/author-interface`, `/author-docs`, `/author-internal-docs` | The resolved kind's skill, after detection |

</reference_index>
