# Issues - Audit

Known follow-ups for the audit node. Coordination note; not spec truth.

## Generic auditor has no workflow-YAML audit surface

During PR 420 local verification, the `auditor` agent rejected audit setup when
the full changeset scope included `.github/workflows/spec-tree-evals.yml`:

```text
missing required skill: audit-yaml-kind
```

Checked facts:

- `actionlint .github/workflows/spec-tree-evals.yml` passed and covered workflow
  syntax.
- The `auditor` agent approved the remaining supported Python, test
  infrastructure, spec-test, and coordination-note scope after the workflow YAML
  was excluded.
- The changeset review gate still owns full-diff review, including workflow YAML,
  because the generic implementation auditor cannot currently judge that surface.

Revisit condition: when the audit-family surface work in `PLAN.md` resumes,
decide whether workflow YAML receives a dedicated YAML audit skill or routes to a
workflow-specific audit surface, then make `auditor` report that coverage
without requiring callers to split YAML out of an otherwise valid changeset.

## SPX audit verification contract follow-ups

The plugin implementation-auditor model records implementation-audit coverage, findings, terminal state, and projections through `spx verification run`. The remaining issues live in the SPX verification-run contract rather than in plugin-side verdict scripts.

Open gaps:

- Audit scope payloads require stable producer identity and producer provenance for every unit, but `missing-skill`, `unsupported`, and `coverage-gap` units may have no executed leaf skill and sometimes no skill or plugin version. SPX should distinguish the run driver that recorded the unit from the expected producer that would have covered it, and make provenance optional when the expected producer is absent.
- Audit unit identity and subject normalization are not specified. SPX should define deterministic `unit_id` derivation, parent/child identity stability, and normalized subject shape so findings, coverage gaps, and prior-run context converge across repeated runs.
- Audit class/kind validation needs a compatibility matrix for `instructions`, `spec`, and `implementation` classes so impossible combinations such as an implementation audit of `skill` or an instructions audit of `code` are rejected by schema validation.
- Audit terminal rollup is planned, but the public `finish` contract still speaks as caller-supplied terminal status. SPX should decide whether audit `finish` derives status without a caller value or validates a supplied value against the derived rollup, and specify the rejected mismatch behavior.
