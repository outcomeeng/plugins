# Issues: Prose Plugin

## Eval evidence for the prose surface stays deferred

The kind-detection and style-adherence evals for the prose surface remain unwritten by operator decision: the eval harness is under repair in a separate concurrent effort, and no spec node names that effort yet, so this entry is the owning record rather than a pointer. Revisit when the eval surface is operational.

## `prose.md` exceeds the assertion-count decompose guidance

`spx/43-prose.enabler/prose.md` carries 8 assertions in one `### Compliance`
subsection, above the >7 guidance that triggers decomposition. The assertions
cluster into two separable concerns: router and composition-surface shape
(assertions 1, 5, 6, 7) versus kind-detection and audit-verdict behavior
(assertions 2, 3, 4, 8).

**Resolution shape**: a `/decompose` pass on `spx/43-prose.enabler` splitting
the two concerns into child enablers, or an explicit re-scope that keeps the
node within the guidance.

**Evidence.** Surfaced by the changes reviewer on the prose router-surface
changeset (sealed review run `2026-08-05_21-08-16-860-5bf3b83599ce`, PR #501).

## `audit-prose` emits no structured verdict, so its behavior is not gradeable (RESOLVED)

**Resolved by the router-pair surface.** `audit-prose` declares a machine-readable verdict — `schema_version`, `skill`, `overall: APPROVED | REJECTED`, `findings[]` carrying `kind`, `pattern`, `category`, `quote`, `rewrite`, and a `summary` — produced only through the dispatched `prose-auditor` agent. The former `audit-internal-docs` prose-flag surface is now a composed finding producer feeding that verdict.

## Reference-skill `<success_criteria>` prove a downstream document, not the catalog (RESOLVED)

**Resolved across the standards pair and the new kind layers.** `prose-standards` and `internal-docs-standards` each carry a catalog-soundness criterion beside the document-facing checklist — both in the at-least-one-worked-example form their catalogs satisfy — and the new `copy-standards`, `interface-standards`, and `docs-standards` shipped with one from the start.
