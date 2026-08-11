---
name: author-prose
description: >-
  ALWAYS invoke this skill when writing or editing any text for human readers — documents, web pages, articles, product docs, UI text, error messages, notifications, emails, READMEs, release notes, marketing copy, and internal team pages. NEVER invoke for chat responses to the user (no matter how long), code comments, commit messages, or agent-facing instructions like SKILL.md.
argument-hint: "[interface|document|copy] <what to write>"
allowed-tools: Read, Edit, Write, Glob, Grep, Skill,{!% if target == 'claude' %!} Agent{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}}{!% endif %!}
---

{!% require_skill 'prose:prose-standards' %!}

<objective>

Human-facing text drafted against the kind its caller supplied and approved by a `prose-auditor` pass.

</objective>

<constraints>

- NEVER derive the kind from the request, the destination, or a draft. Writing precedes the text, so no property of the text exists to read; a draft against the wrong kind's standards reads wrong in ways later editing does not repair.
- NEVER guess when no kind arrives. Ask, from the three-kind list, once.
- NEVER invent a style outside the taxonomy.
- NEVER author a repository- or domain-governed artifact here — ownership outranks a supplied kind, and a governed artifact routes to its own workflow before anything else runs.

</constraints>

<kind_intake>

The kind is an input. Resolve it in this order and stop at the first that yields one:

1. **The invocation.** A kind named in the arguments or the request — `interface`, `document`, or `copy`.
2. **The repository's map.** When the repository declares a path-to-kind map at `spx/local/prose.md` and the target path matches an entry, that entry is the kind. The map is a declaration its owner wrote, never an inference.
3. **One question.** Ask the user to pick from the three kinds, presenting what each covers. Never guess and never proceed without an answer.

| Kind        | The text goes into                                                                                           |
| ----------- | ------------------------------------------------------------------------------------------------------------ |
| `interface` | A designed surface: buttons, labels, empty states, error messages, tooltips, notifications, email templates  |
| `document`  | A document set: product docs, wiki pages, runbooks, reference, policies, rubrics, onboarding guides, READMEs |
| `copy`      | A standalone piece read start to finish: essays, articles, long-form landing narrative                       |

Before any of the three, check ownership: a spec, ADR, PDR, `SKILL.md`, `PLAN.md`, `ISSUES.md`, or root agent guide is governed by its own workflow and never enters the prose surface. Chat responses and operational prose — a code comment, a commit message, an agent-facing instruction — stay outside it the same way.

One text carries one kind. Register variation inside it is carried by the `/prose-standards` `<rule_packs>`, which bind on a feature rather than on a kind, so a runbook's procedure and an essay's table are governed where they appear without a second kind.

</kind_intake>

<workflow>

1. Resolve the kind through `<kind_intake>`. Nothing is written before it is settled.

2. Invoke the kind's composed author skill via the Skill tool: `prose:author-interface`, `prose:author-document`, or `prose:author-copy`. That skill loads its standards layer, which transcludes the shared voice canon and carries the kind's writing guidance.

3. Write or edit the text applying the base catalog and the kind's layer together. Zero tolerance for the base anti-patterns; the kind's overrides are the only sanctioned relaxations.

4. Apply every rule pack the text triggers. A numbered procedure triggers the instruction pack; a table triggers the table pack.

5. Direct an audit pass: dispatch the `prose-auditor` agent on the result, naming the kind in the dispatch as `Kind: <kind>`. The dispatched audit reads nothing without it. Fix findings and re-audit until the verdict is `APPROVED`.

</workflow>

<success_criteria>

- The kind came from the invocation, the repository's map, or one asked question, and was settled before drafting began.
- The text was written through the kind's composed author skill, not from the router's own judgment.
- Every rule pack the text triggers was applied where its feature appears.
- The `prose-auditor` dispatch carried the kind and returned `APPROVED` on the final text.

</success_criteria>

<failure_modes>

**Drafting started before the kind was settled.**

Claude read "write the onboarding page for the new export flow", recognized a page, and drafted against the document layer. The text was destined for a product-tour overlay, so every paragraph had to become a sequence of elements under the interface brevity caps. Nothing survived the conversion but the facts. The kind is not a property of a draft that can be corrected afterward; it selects the standards the draft is built from, so an unresolved kind stops the writing rather than steering it.

</failure_modes>

<reference_index>

| Skill                                                   | When to read                            |
| ------------------------------------------------------- | --------------------------------------- |
| `/prose-standards`                                      | Always — base catalog and rule packs    |
| `/author-interface`, `/author-document`, `/author-copy` | The supplied kind's skill, after intake |

</reference_index>
