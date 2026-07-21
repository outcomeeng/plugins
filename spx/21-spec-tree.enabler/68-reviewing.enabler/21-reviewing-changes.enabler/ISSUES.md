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

## 7. Review scope carries deterministically generated artifacts

Review scope is the raw changed-file set, so a changeset that edits authored plugin sources reviews each generated mirror as an independent unit. A run over a 128-file scope drew 38 units from `src/plugins`, 38 from `dist/claude`, 38 from `dist/codex`, 13 from `spx`, and 1 from `README.md`: the 76 `dist/` units are 59% of the scope and carry no information the `src/` units do not, because `spx/18-plugin-build.enabler/plugin-build.md` declares build determinism (`same src/ content always produces byte-identical dist/claude/ and dist/codex/ outputs`) and generated-artifact provenance (`every committed file under dist/ traces to a src/ ancestor through the build`), both `[test]`-backed, and the gate's `dist-diff` step fails the build on any divergence. A finding raised against a generated file is also unfixable at its own location — its fix belongs to the `src/` ancestor — so the scope admits findings the cited site has no authority to satisfy.

`compute_diff.py` applies no path classification; the reviewer receives every changed path.

This is a separate larger concern rather than a bounded fix: the changeset definition is declared at product level in `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` as `the files changed between the base ref and HEAD`, governing all five verification types, so narrowing review scope amends a decision above this node rather than a script inside it. It also runs against `spx/15-merging.pdr.md` and this node's own rule that the reviewer resolves its own scope and treats caller-supplied scope as non-authoritative — a generated-path exclusion must be established as the reviewer's own derivation, never a caller filter, and the two must be told apart in the declaration. `dist/` is this repository's generated root; a consumer's differs, so the exclusion has to be a declared property of the project rather than a hardcoded path, and `spx/12-shipped-scripting.adr.md` sends a shipped script's logic to the SPX CLI once it passes fifty lines and proves its value.

Required handling:

- Decide whether generated-artifact exclusion is a property of the changeset definition (all verification types) or of review scope alone, and amend the governing decision before any lower layer adopts it.
- Declare the generated roots as a project-supplied property; never hardcode `dist/`.
- Distinguish reviewer-owned scope derivation from a caller-supplied scope filter in the declaration, so the exclusion does not weaken the caller-independence rule this node already carries.
- Keep audit and base-sync scope unaffected unless the amended decision covers them — `branch_scope` serves all three consumers, and base sync needs the real changed-file set.

## 8. The review-changes skill omits an explicit model pin

`src/plugins/spec-tree/skills/review-changes/SKILL.md` declares no `model` field, so a direct skill invocation inherits the session model. `skill-standards` states that marketplace verification-sensitive surfaces use explicit `sonnet` and never use session inheritance, and every `audit-*` skill in the spec-tree plugin pins `model: sonnet`. Review is a verification type whose findings decide `VERIFICATION_READINESS`, so an inherited model makes the review verdict depend on whichever model the invoking session happens to run.

The primary path is already pinned: the `changes-reviewer` agent declares `model: sonnet`, so agent-dispatched reviews are reproducible today. The gap is the direct skill-invocation path.

Required handling:

- Add `model: sonnet` to the `review-changes` skill frontmatter, matching the `audit-*` sibling convention.
- Regenerate the plugin runtime trees and the catalog so the pin reaches `dist/`.
- Re-run the skill auditor for the node after the change.

The sibling reference skill `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` needs no pin: `scope-changeset` is `user-invocable: false` with `allowed-tools: Read`, supplying deterministic script primitives rather than a model-judged verdict.

Revisit entries 5 and 6 when review moves from `spx journal --type review` to `spx verification run`. Exercise the migration with an in-progress inspection before seal, repeated inspection of one file, restored prior-run context, and a final projection whose unique covered-unit count equals the changeset scope.
