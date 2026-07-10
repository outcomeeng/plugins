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
- Prior-run selection must distinguish gating runs over committed heads from advisory runs over live modified or untracked files. The run-set selector should expose run purpose directly rather than infer authority from scope payload prose.

## Codex verifier skill enablement and wrapper portability

Codex custom-agent `skills.config` entries enable named skills; they do not copy
skill content into the initial subagent context. The generated developer
instructions therefore name each required skill, require it before specialized
work, and stop when it cannot load. This is the intended Codex shape and does not
require inlining audit intelligence into the wrapper agent.

Runtime evidence distinguishes skill loading from orchestration failure:

- The installed implementation-audit orchestration skill exists in the Codex plugin cache.
- `test-evidence-auditor` run `019f468d-6ab3-7613-af9f-b61e1d6442e2`
  returned JSON `PASS`.
- `changes-reviewer` run `019f468d-8269-7863-88c6-e8234b1809d5` returned raw
  review token `2026-07-09_11-05-34-525-da5ee9f78a95`; its projection reported
  approved, 22 files examined, 0 blocking findings, and 0 debt findings.
- A separate `changes-reviewer` returned prose instead of a raw token and was
  invalid under the reviewer output contract.
- The retired generic `auditor` path failed twice, including one run that reached
  an audit dispatch gate and then attempted a forbidden constructed helper path.
  That failure does not establish that typed artifact verifiers cannot load
  enabled skills.

Remaining handling:

- The authored and generated plugin trees contain `implementation-auditor`, but
  the active Codex runtime role registry rejects the exact required spawn with
  `unknown agent_type 'implementation-auditor'` before the wrapper can invoke
  `spx verification run`.
- Revisit after the merged plugin version is installed and a new runtime session
  exposes `implementation-auditor`; run the same smoke audit and preserve the run
  token plus rendered projection, or the exact blocked SPX command when dispatch
  succeeds but the verification lifecycle rejects a payload.
