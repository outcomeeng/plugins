# Plan: audit verification-run migration

The audit surface uses the published `spx verification run` lifecycle. The
target surface is declared by `spx/21-spec-tree.enabler/17-audit.adr.md`: one
spec-tree-owned
`implementation-auditor` wrapper agent composes `audit-{lang}-code`,
`audit-{lang}-tests`, and `audit-{lang}-architecture` skills inside one isolated
verifier context, then records one audit verification run. Language plugins ship
skills only; they do not ship language-specific auditor agents.

## Remaining slices

- Add executable agent/eval coverage for representative implementation-auditor
  runs over one-language, multi-language, and unsupported-file scopes once the
  agentic runner can be exercised deterministically.
- Generalize the implementation-auditor partitioning and coverage inventory for
  several files, several languages, and changesets containing unsupported files.
- Move remaining audit run-set convergence onto SPX prior-context restoration
  once the plugin smoke path proves the single-run lifecycle.
- Reconcile artifact-type auditors (`adr-auditor`, `pdr-auditor`,
  `spec-auditor`, `test-evidence-auditor`, `eval-evidence-auditor`) with the
  same `spx verification run` contract after implementation audit is runnable.

## Governing context

- `spx/15-audit-result-delivery.pdr.md`: audit progress and findings are visible
  during the run on local and pull-request surfaces.
- `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md`:
  agentic verification uses one append-only run source of truth and projection
  surfaces.
- `spx/21-spec-tree.enabler/17-audit.adr.md`: audit-specific wrapper, language
  skill naming, composition, and no-language-agent-fleet rules.
- `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`:
  deterministic validation, test, and eval stay outside the dispatched audit.
- Root guide published-floor rule: shipped skills may depend on `spx
  verification run` only after the repository floor and CI pin reach the
  published SPX release carrying it.

## Strict-finding-disposition extraction

`work/audit-runtime-evidence` currently changes 59 paths across implementation-audit contracts, Python authoring guidance, distribution code, and repository configuration. Partition it before publication.

The audit-owned merge cycle contains the implementation-auditor run contract, coverage inventory, wrapper configuration, governing audit declarations, co-located tests, and required generated output. Python authoring or distribution changes that can merge and verify without that contract receive their own owning-node plans and branches.

**Revisit condition:** replace this section with the resulting audit PR reference after the branch has one implementation-audit behavior, one verification story, and one rollback story. Keep the separate changeset-coherence auditor excluded until the operator starts it explicitly.
