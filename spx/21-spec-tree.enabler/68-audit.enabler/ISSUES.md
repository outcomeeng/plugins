# Issues - Audit

Known follow-ups for the audit node. Coordination note; not spec truth.

## Generic auditor has no YAML audit surface

During PR 420 local verification, the `auditor` agent rejected audit setup for
the full changeset scope when `.github/workflows/spec-tree-evals.yml` was
included:

```text
missing required skill: audit-yaml-kind
```

Checked facts:

- `actionlint .github/workflows/spec-tree-evals.yml` passed and covered workflow
  syntax.
- The `auditor` agent approved the remaining supported Python, test
  infrastructure, spec-test, and coordination-note scope after the workflow YAML
  was excluded.
- The final `changes-reviewer` gate still needs to review the full diff,
  including `.github/workflows/spec-tree-evals.yml`.

Revisit condition: when the audit-family surface work in `PLAN.md` resumes,
decide whether workflow YAML receives a dedicated YAML audit skill or routes to a
workflow-specific audit surface, then make `auditor` report that coverage
without requiring callers to split YAML out of an otherwise valid changeset.
