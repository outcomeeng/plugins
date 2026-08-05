# Issues: Prose Plugin

## `audit-prose` emits no structured verdict, so its behavior is not gradeable (RESOLVED)

**Resolved by the router-pair surface.** `audit-prose` declares a machine-readable verdict — `schema_version`, `skill`, `overall: APPROVED | REJECTED`, `findings[]` carrying `kind`, `pattern`, `category`, `quote`, `rewrite`, and a `summary` — produced only through the dispatched `prose-auditor` agent. The former `audit-internal-docs` prose-flag surface is now a composed finding producer feeding that verdict. Eval evidence grading the contract is the recorded follow-up in `spx/43-prose.enabler/PLAN.md`.

## Reference-skill `<success_criteria>` prove a downstream document, not the catalog (RESOLVED)

**Resolved across the standards pair and the new kind layers.** `prose-standards` and `internal-docs-standards` each carry a catalog-soundness criterion beside the document-facing checklist — both in the at-least-one-worked-example form their catalogs satisfy — and the new `copy-standards`, `interface-standards`, and `docs-standards` shipped with one from the start.
