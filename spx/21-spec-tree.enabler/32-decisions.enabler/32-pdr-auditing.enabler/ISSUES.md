# Issues: PDR Auditing Enabler

## Third audit property carries three names — "compliance quality" vs "tag-validity" (DEBT, tracked)

The PDR audit's third property has divergent names across the surfaces that describe it:

- `pdr-auditing.md` "PDR Evidence Model" property 3 — **Compliance quality** ("MUST/NEVER rules are verifiable by product review or automated test").
- `audit-pdr` SKILL.md verdict row 3 and step 5 — **tag-validity** (the verdict-row machine identifier; renamed from `mode-validity`).
- `src/plugins/spec-tree/skills/audit-pdr/references/pdr-evidence-model.md` `<compliance_quality>` — **compliance quality**, defined as three sub-checks: verifiability, tag matching its subsection, and specificity.

"Compliance quality" is the broader concept: tag-matching is only its second sub-check, alongside verifiability and specificity. The verdict row and the eval suites name the slot "tag-validity" and exercise tag-matching and evidence-type fit only, not verifiability or specificity. Renaming the spec property to "tag-validity" would narrow it and mischaracterize the reference's verifiability/specificity content; renaming the reference section to "tag-validity" would discard that teaching content.

Reconciling the name coherently is a model-naming decision spanning `pdr-auditing.md`, the canonical `pdr-evidence-model.md` reference, and the `audit-pdr` verdict contract — whether the third property is "compliance quality" (broad: verifiability + tag-matching + specificity, with "tag-validity" as a sub-aspect) or "tag-validity" (narrow), and whether the eval suites should grow verifiability/specificity cases to match. This predates the eval-slice retag (the divergence existed as "compliance quality" vs the former `mode-validity` row) and is larger than the mechanical `mode-validity → tag-validity` rename that slice carried.

Surfaced by the local `review-changes` review on the PDR-auditing eval-suite change (`feat/pdr-auditing-eval-suites`).

Required handling:

- Decide the canonical name and scope of the third audit property across `pdr-auditing.md` (PDR Evidence Model property 3), `pdr-evidence-model.md` (`<compliance_quality>` and the overview list), and the `audit-pdr` verdict row/step.
- If the property stays "compliance quality" (broad), either rename the verdict row back to a compliance-quality identifier or document that `tag-validity` is one sub-aspect's row; if it becomes "tag-validity" (narrow), relocate the verifiability/specificity checks the reference teaches.
- Keep the eval suites aligned with whichever scope the row claims.
