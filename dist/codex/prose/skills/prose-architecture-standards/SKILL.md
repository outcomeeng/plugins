---
name: prose-architecture-standards
user-invocable: false
description: >-
  Prose ADR conventions enforced across architect and auditor skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The prose ADR conventions — template source, structure ownership, atemporal voice — and the per-kind structural conventions a prose ADR draws its rules from.
</objective>

<success_criteria>

- The ADR conforms to the decision template loaded from the live `/understand` foundation; no prose skill restates that template's shape.
- Structural rules are ALWAYS/NEVER rules carrying `([audit])`.
- The ADR decides structure — artifact set, section architecture, ordering, terminology homes, cross-link topology — and no prose artifact carries structural annotation.
- Every sentence states permanent truth; no section narrates document history or a migration.

</success_criteria>

<reference_note>
This is a reference skill. Composing prose architecture skills load these conventions explicitly before authoring or auditing prose ADRs. It is not a standalone workflow.
</reference_note>

<structure_ownership>

A prose ADR owns the structure of the prose artifacts its governing spec node declares. Structure and text have separate owners: the ADR decides sections, ordering, and moves — including sequencing across sibling and descendant artifacts — and the artifact's writer complies with those decisions while owning every sentence. Structural intent lives only in the ADR, so no prose artifact carries a structural annotation, a move mark, or any other in-artifact trace of a structural decision.

A structural change is an ADR change first. Reordering a document set, splitting a page, or renaming a section starts by amending the governing ADR; the artifact then follows. A structural edit with no governing decision is the gap the audit names.

</structure_ownership>

<prose_adr_content>

The ADR's shape is owned by the `/understand` foundation's decision template. Begin by loading that template through the live foundation; this standard never restates its sections, because a restated shape drifts the moment the template advances. Structural conformance of prose is agent judgment, so a prose ADR's verification rules carry `([audit])`.

**What a prose ADR decides:** the artifact set and each artifact's kind; each artifact's section architecture and ordering; sequencing and cross-references across sibling and descendant artifacts; terminology homes — which artifact canonically defines each shared concept; and the structural conventions from the kind's reference below that the set commits to. The structure the ADR decides is stated as rules, never reproduced as a draft or an outline of the artifacts themselves.

**What a prose ADR never contains:** drafted prose, style rules the kind layers already carry, or per-sentence guidance — style belongs to `/prose-standards` and its kind layers, and text belongs to the artifact's writer.

</prose_adr_content>

<atemporal_voice>

A prose ADR states structural truth. It never narrates document history, current page state, or a restructuring plan. "The onboarding guide currently opens with prerequisites" narrates state; "The onboarding guide opens with the first milestone" decides structure. "We need to merge the two runbooks" narrates a plan; "One runbook covers the deploy path" is the decision the merge complies with.

</atemporal_voice>

<kind_structures>

A kind's structural conventions carry the shapes its artifacts take. Read the supplied kind's file before writing or auditing a prose ADR for artifacts of that kind; the ADR selects and binds the conventions its artifact set commits to.

| Kind            | Structural conventions                     |
| --------------- | ------------------------------------------ |
| `copy`          | `${SKILL_DIR}/references/copy.md`          |
| `interface`     | `${SKILL_DIR}/references/interface.md`     |
| `documentation` | `${SKILL_DIR}/references/documentation.md` |

Each kind's style layer lives in the matching reference of `/prose-standards`; a style rule never migrates into an ADR.

</kind_structures>
