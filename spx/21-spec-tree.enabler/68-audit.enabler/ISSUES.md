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
