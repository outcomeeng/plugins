# ISSUES - review-changes

Known issues for `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`.

## 1. Review nodes use gerunds

`spx/21-spec-tree.enabler/68-reviewing.enabler` and `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` use gerund slugs. The nodes must be `review` and `review-changes`.

Required handling:

- Use `/refactor` to rename the nodes and update spec filenames, links, and references.
- Preserve the verification-kind vocabulary: `review` is the verification type and `review-changes` is the skill surface.
- Regenerate derived plugin, runtime, catalog, and guide artifacts that carry the node paths or names.

## 2. Review-changes tests violate testing governance

The tests under `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/` are not acceptable evidence for this node. They violate the testing skill, Python test standards, and this product's testing ADR/PDR rules.

Required handling:

- Rewrite the test evidence through `/test` and run the required test-evidence audit before accepting it.
- Align the evidence chain with `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`, `spx/15-test-language.adr.md`, and the Python test standards.
- Keep `tests/` limited to typed assertion files; move harness, generator, fixture, and source-owned vocabulary responsibilities to their governed homes.

## 3. Review finding validation belongs in SPX

The stop-gap runner appends review findings through the shared run journal without review-specific validation for required finding fields, severity and concern values, or citation shape. `spx journal append` validates the journal event boundary, but it does not yet enforce the review finding contract.

Required handling:

- Add review-specific finding validation to the SPX verification or journal boundary that owns review runs.
- Validate the finding shape before a review run can be sealed or projected.
- Keep the skill runner as a thin command surface; do not restore per-finding schema or citation validation to the skill path as a durable fix.

## 4. Review journal scope can hide a completed run from projection

A local `changes-reviewer` run token `2026-06-30_12-22-01-921-462d1675edbf` was written under `.spx/branch/head-b5180223/review/runs/`, while `spx journal render review 2026-06-30_12-22-01-921-462d1675edbf` and `spx journal read review 2026-06-30_12-22-01-921-462d1675edbf` could not locate it from branch `feat/issue-cross-repo-followup` at head `3b21c057b07f87df2b6516c1e160df992447fa76`. The review gate then required direct JSONL inspection to recover the approved result and one debt finding.

Required handling:

- Make review run lookup derive the same branch scope for wrapper-agent produced runs and main-session projection reads, or provide a supported branch-scope selector for `spx journal render` and `spx journal read`.
- Add regression coverage for a review run created by `changes-reviewer` and read from the main session on the same changeset head.
- Keep direct `.spx/branch/**/review/runs/*.jsonl` reads out of the normal merge workflow once the projection lookup resolves the run token.

## 5. Unsealed prefixes lack a supported inspection projection

Live review run `2026-07-11_12-08-54-490-cf96cc5a58e9` had already recorded complete unique scope coverage and a rejecting finding while the reviewer agent was still running. `render_review_run.py` rejected inspection with `has no terminal completion event`, forcing the caller to query and summarize the raw event prefix.

Required handling:

- Render unsealed prefixes as in-progress projections.
- Surface findings immediately after their events are appended.
- Report current unique scope coverage without requiring a terminal event.
- Preserve the same finding and coverage projection when the run seals.

## 6. Repeated inspection events inflate scope coverage

The sealed run declared 385 changed files and emitted 626 `verification.scope.advanced` events. The projection reported `385 files, 626 examined`; most files appeared three times and `AGENTS.md` appeared four times.

Required handling:

- Preserve repeated inspection events in the append-only history when they represent distinct attempts.
- Project authoritative coverage by stable scope-unit identity rather than raw event count.
- Distinguish total inspection attempts from unique covered units when both are useful.
- Restore prior-run context without copying prior scope events into the new run's authoritative coverage count.

Revisit entries 5 and 6 when review moves from `spx journal --type review` to `spx verification run`. Exercise the migration with an in-progress inspection before seal, repeated inspection of one file, restored prior-run context, and a final projection whose unique covered-unit count equals the changeset scope.

## 7. This branch is a rejected coherence unit — split before publication

The `changeset-coherence-auditor` (shipped in spec-tree 0.79.0) audited this branch's changeset and returned `REJECTED`, `publication_authorized: false`. The changeset bundles seven independently mergeable semantic clusters across three independent dependency roots, so it cannot ship as one review unit.

The recommended dependency-ordered split:

1. **Eval-harness multi-producer (`producer-files`) rendering** — the `producer-coupled-skill-evals` ADR, `producer_prompt` capability, and `audit-eval-evidence` freshness rule. Independent root; every other unit below depends on it.
2. **Runtime-token scanner ISSUES.md note** (`spx/15-validation.enabler/32-runtime-token.enabler`). Independent root; no coupling to any other unit.
3. **ADR voice-eval rationale-temporal case** — depends on unit 1.
4. **Instruction-block terminology + generator-migration ISSUES.md note** (`spx/21-spec-tree.enabler/43-instruction-block.enabler`). Independent root.
5. **`audit-specs` stale eval-link fix** routing through the consolidated `structure` eval — depends on unit 1.
6. **Audit coverage-by-artifact-ownership** classification (`audit.md`, `audit-implementation`, `audit-tests`) — depends on unit 1.
7. **The review-finding-disposition rewrite itself** (`reviewing-changes`, `merging`, TypeScript remediation) — depends on units 1 and 6. This is the branch's anchor concern; the other six are separable capabilities it happens to consume.

Required handling:

- Split the branch into the seven review units above, publishing in dependency order (roots 1, 2, 4 first).
- One `debt` finding to resolve during the split: the generated `.github/workflows/spec-tree-evals.yml` trigger block is regenerated jointly by units 6 and 7 (unit 6 adds the implementation-ownership `owned_paths`, unit 7 narrows the merging evals'), so that file's diff is not attributable to a single producer unit — keep both units' `owned_paths` edits together wherever that file lands.
- The verdict binds to the branch tip current at audit time; re-run `changeset-coherence-auditor` against the branch to regenerate a current split if the branch advances.
