---
name: author-prose
description: >-
  ALWAYS invoke this skill when writing text for human readers — docs pages, UI text, error messages, emails, release notes. NEVER invoke for chat responses, code comments, commit messages, or agent instructions.
argument-hint: "[interface|documentation|copy] <what to write>"
allowed-tools: Read, Edit, Write, Glob, Grep, Skill, Agent
---

Invoke the `prose:prose-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

Human-facing text drafted against the kind its caller supplied, complying with the governing prose ADR, and approved by a `prose-auditor` pass.

</objective>

<constraints>

- NEVER derive the kind from the request, the destination, or a draft. Writing precedes the text, so no property of the text exists to read; a draft against the wrong kind's standards reads wrong in ways later editing does not repair.
- NEVER guess when no kind arrives. Ask, from the three-kind list, once.
- NEVER invent a style outside the taxonomy.
- NEVER author a repository- or domain-governed artifact here — ownership outranks a supplied kind, and a governed artifact routes to its own workflow before anything else runs.
- NEVER decide structure against the governing prose ADR. This skill is the artifact's sole writer, and the ADR owns the artifact set's structure; a structural change routes through `/architect-prose` first.

</constraints>

<kind_intake>

Before any step below, check ownership. A spec, ADR, PDR, `SKILL.md`, `PLAN.md`, `ISSUES.md`, or root agent guide is governed by its own workflow and never enters the prose surface, whatever kind the request supplies. Chat responses and operational prose — a code comment, a commit message, an agent-facing instruction — stay outside it the same way. Ownership outranks a supplied kind, so a kind arriving at step 1 never resolves past this check.

The kind is an input. Resolve it in this order and stop at the first that yields one:

1. **The invocation.** A kind named in the arguments or the request — `interface`, `documentation`, or `copy`.
2. **The repository's map.** When the repository declares a path-to-kind map at `spx/local/prose.md` and the target path matches an entry, that entry is the kind. The map is a declaration its owner wrote, never an inference.
3. **One question.** Ask the user to pick from the three kinds, presenting what each covers. Never guess and never proceed without an answer.

| Kind            | The text goes into                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------ |
| `interface`     | A designed surface: buttons, labels, empty states, error messages, tooltips, notifications, email templates  |
| `documentation` | A document set: product docs, wiki pages, runbooks, reference, policies, rubrics, onboarding guides, READMEs |
| `copy`          | A standalone piece read start to finish: essays, articles, long-form landing narrative                       |

One text carries one kind. Register variation inside it is carried by the `/prose-standards` `<rule_packs>`, which bind on a feature rather than on a kind, so a runbook's procedure and an essay's table are governed where they appear without a second kind.

</kind_intake>

<workflow>

1. Check ownership through `<kind_intake>`. A governed artifact routes to its own workflow and stops here, whatever kind the request supplied.

2. Resolve the kind through `<kind_intake>`. Nothing is written before it is settled.

3. Locate the governing prose ADR. When the repository's spec tree carries a prose ADR governing the target artifact, read it — it decides the artifact's structure, its place among sibling artifacts, and the terminology homes. When the request needs a structural change the ADR does not decide — a new artifact, a reordered set, a split page — route the structural decision through `/architect-prose` before writing. With no governing ADR, the kind's structural conventions in `/prose-architecture-standards` guide the artifact's shape directly.

4. Read the kind's style layer — the supplied kind's file from `/prose-standards` `<kind_layers>` — and the kind's structural conventions from `/prose-architecture-standards` `<kind_structures>`.

5. Write or edit the text applying the voice canon, the base catalog, and the kind's layers together. Zero tolerance for the base anti-patterns; the kind's overrides are the only sanctioned relaxations.

6. Apply every rule pack the text triggers. A numbered procedure triggers the instruction pack; a table triggers the table pack.

7. Direct an audit pass: dispatch the `prose-auditor` agent on the result, naming the kind in the dispatch as `Kind: <kind>`. The dispatched audit reads nothing without it. The agent returns a raw run token; render the sealed run through the `/project-run-journal` inspection helper, fix the findings it reports, and re-audit until the run completes approved.

</workflow>

<success_criteria>

- Ownership was checked before the kind resolved, and a governed artifact routed to its own workflow without drafting, whatever kind the request supplied.
- The kind came from the invocation, the repository's map, or one asked question, and was settled before drafting began.
- The text complies with the governing prose ADR where one exists, and any needed structural change routed through `/architect-prose` rather than being decided while writing.
- The kind's style layer and structural conventions were both read and applied.
- Every rule pack the text triggers was applied where its feature appears.
- The `prose-auditor` dispatch carried the kind and its final run completed approved on the final text.

</success_criteria>

<failure_modes>

**Drafting started before the kind was settled.**

Claude read "write the onboarding page for the new export flow", recognized a page, and drafted against the documentation layer. The text was destined for a product-tour overlay, so every paragraph had to become a sequence of elements under the interface brevity caps. Nothing survived the conversion but the facts. The kind is not a property of a draft that can be corrected afterward; it selects the standards the draft is built from, so an unresolved kind stops the writing rather than steering it.

</failure_modes>

<reference_index>

| Skill                           | When to read                                                                |
| ------------------------------- | --------------------------------------------------------------------------- |
| `/prose-standards`              | Always — voice canon, base catalog, rule packs, kind style layers           |
| `/prose-architecture-standards` | The kind's structural conventions, and the ADR shape when structure changes |
| `/project-run-journal`          | Rendering the audit run token the `prose-auditor` dispatch returns          |

</reference_index>
