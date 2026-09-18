# Issues

## Eval run history is stale for all three suites

The newest full-suite passing rows for `evals/structure`, `evals/voice`, and
`evals/tag-validity` are from 2026-07-11 (git SHAs
`afe86c93648cae7896781155345627f0c5be62b9` and
`16c29f04a151d941ed4a0be9855892f3234055fa`); the 2026-07-20 rows are single-case
runs on commits that are not ancestors of the current head. The producer
`src/plugins/spec-tree/skills/audit-adr/SKILL.md` changed in twenty commits since,
the eval harness changed, and `prompt.md` was rematerialized, so no committed run
proves the current producer, prompt, and case set. `PLAN.md` in this node defers
the refresh behind the verification-run migration.

**Settlement condition**: one passing `just eval-node` run over the three suites
on a head that carries the current producer, with its rows committed to each
`history.jsonl`.

**Evidence**: `spec-tree:eval-evidence-auditor` findings `f-007`, `f-008`,
`f-009` on head `a65659114b99767b90b4d920550fff5dc0824794` during Change #76, whose prototype boundary runs no eval.

## Two tag-validity assertions rest on one case each under a 0.85 threshold

The assertions for a bare mechanism tag on a compliance-type rule and for a
universal claim tagged `scenario` each map to exactly one case
(`compliance-type-bare-mechanism-tag-rejected`,
`universal-scenario-tag-rejected`) in a seven-case suite whose threshold is
0.85; 6/7 = 0.857 passes the suite, so either assertion can be unfulfilled while
the suite passes. `history.jsonl` records sixteen rows with 6 of 7 passing and
`passed: true`.

**Settlement condition**: each of the two assertions is backed by more than one
case, or the suite threshold requires its case.

**Evidence**: `spec-tree:eval-evidence-auditor` finding `f-004` on head `a65659114b99767b90b4d920550fff5dc0824794`
during Change #76.
