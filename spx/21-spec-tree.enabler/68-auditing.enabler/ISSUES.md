# Issues: Auditing Enabler

## 1. Audit-skill `SKILL.md` bodies diverge from the auditor skeleton

`develop:skill-auditor` flags structural-conformance gaps in the `audit-{lang}` skill **bodies**
and reference-polish gaps, independent of the no-deterministic-verification work:

- `audit-python` and `audit-typescript` `<success_criteria>` are checklists of workflow steps rather
  than verdict-soundness properties (the auditor skeleton's `<success_criteria_shape>`).
- `audit-typescript` has no `<constraints>` section (prohibitions split across `<essential_principles>`
  and `<what_to_avoid>`), and its `<verdict_format>` sits after `<failure_modes>` rather than before.
- `audit-rust` reference polish: `references/unsafe-soundness.md` has markdown headings,
  and `references/false-positive-handling.md` has a stray trailing code fence.

## Why tracked, not fixed here

These live in the `audit-{lang}` `SKILL.md` bodies and other reference files; the changeset that
surfaced them edited only `references/example-audit.md`. They are a separate audit-skill-quality
refactor (re-shaping `<success_criteria>` to soundness properties and aligning section order to the
auditor skeleton across the audit-skill family), not part of the example-verdict JSON rewrite. A
dedicated pass should run `develop:skill-auditor` across every audit skill and bring the bodies to
skeleton conformance.
