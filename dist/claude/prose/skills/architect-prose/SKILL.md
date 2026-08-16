---
name: architect-prose
description: >-
  ALWAYS invoke this skill when writing ADRs for prose.
  NEVER author a prose ADR without this skill.
argument-hint: "[interface|documentation|copy] <what to structure>"
allowed-tools: Read, Write, Glob, Grep, Skill
---

Invoke the `prose:prose-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `prose:prose-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

<objective>
A binding prose ADR, authored to the decision template the `/understand` foundation provides, whose structural rules are ALWAYS/NEVER rules carrying `([audit])`.
</objective>

<foundational_stance>
Standards are pre-loaded by the `require_skill` directives above. `/prose-architecture-standards` names the template source and owns structure ownership and the per-kind structural conventions; `/prose-standards` defines the voice and the kind style layers the ADR never restates.

- The ADR's shape comes from the `/understand` foundation's decision template, loaded before authoring — no skill restates it.
- The ADR decides structure — artifact set, section architecture, ordering, sequencing across sibling and descendant artifacts, terminology homes, cross-link topology — and never contains drafted prose or style rules.
- The artifact's writer is `/author-prose`; this skill never writes a prose artifact, and no prose artifact carries a structural annotation.

</foundational_stance>

<kind_intake>

Before anything below, check ownership. A spec, decision record other than the one being authored, `SKILL.md`, `PLAN.md`, `ISSUES.md`, or root agent guide is governed by its own workflow and never enters the prose surface as a governed artifact, whatever kind the request supplies. Chat responses and operational prose — a code comment, a commit message, an agent-facing instruction — stay outside it the same way.

The kind of the governed artifacts is an input. Resolve it in this order and stop at the first that yields one:

1. **The invocation.** A kind named in the arguments or the request — `interface`, `documentation`, or `copy`.
2. **The repository's map.** When the repository declares a path-to-kind map at `spx/local/prose.md` and the governed paths match an entry, that entry is the kind.
3. **One question.** Ask the user to pick from the three kinds. Never guess.

An artifact set whose artifacts differ in kind is structured by one ADR naming each artifact's kind; each artifact still carries exactly one kind.

</kind_intake>

<inputs>
Before creating a prose ADR, read:

- **The governing spec node** — the node whose declared output the prose artifacts realize, with its ancestors' constraints.
- **Existing decisions** — decisions in the node's scope, so the new ADR stays consistent.
- **The artifact set** — the existing prose artifacts the ADR will govern, read for their current structure, never edited here.

</inputs>

<outputs>
The skill produces prose ADRs at the scope of the decision, placed and indexed per `/author`:

| Decision scope | ADR location                                    |
| -------------- | ----------------------------------------------- |
| Product-wide   | `spx/{NN}-{slug}.adr.md`                        |
| Node-specific  | `spx/.../{NN}-{slug}.{node}/{NN}-{slug}.adr.md` |

</outputs>

<adr_creation_protocol>
Execute these phases in order.

**Phase 0 — Check ownership and resolve the kind.** Run `<kind_intake>`: confirm every governed artifact is prose the surface owns, then resolve each governed artifact's kind through the invocation, the repository's map, or one question. Nothing below runs before both are settled.

**Phase 1 — Identify the structural decisions.** For the governed artifact set, list what needs deciding: which artifacts exist and their kinds, each artifact's section architecture and ordering, the sequencing and cross-references across artifacts, and the terminology homes.

**Phase 2 — Select each kind's conventions.** Read every governed kind's reference — each kind the artifact set carries — in `/prose-architecture-standards` `<kind_structures>` and select the shapes the artifact set commits to.

**Phase 3 — Write the ADR.** Load the decision template through the live `/understand` foundation and author to it, applying `/prose-architecture-standards` `<prose_adr_content>`. State structure as ALWAYS/NEVER rules carrying `([audit])`, in atemporal voice — never as a draft, an outline of current pages, or a migration plan.

**Phase 4 — Verify consistency.** The new ADR contradicts no ancestor or sibling decision, and every structural rule is one `/author-prose` can comply with and an audit can judge.

**Phase 5 — Return the authored ADR.** Report the canonical ADR path, the decision summary, and the binding structural rules. Writing the artifacts is `/author-prose`'s work and stays outside this skill.

</adr_creation_protocol>

<constraints>

- NEVER write or edit a prose artifact — this skill decides structure; `/author-prose` is the artifact's sole writer.
- NEVER place a structural annotation, move mark, or restructuring note inside a prose artifact — structural intent lives in the ADR.
- NEVER restate style rules — `/prose-standards` and its kind layers own them.
- NEVER derive the kind from the artifacts — the kind is supplied per `<kind_intake>`.

</constraints>

<success_criteria>

- A structural comparison against the loaded decision template finds no missing, extra, or reordered section, and every structural rule is falsifiable by audit.
- The ADR decides the artifact set, section architecture, ordering, cross-artifact sequencing, and terminology homes, and contains no drafted prose, no style rules, and no temporal narration.
- The kind came from the invocation, the repository's map, or one asked question.
- No prose artifact was written or annotated.

</success_criteria>
