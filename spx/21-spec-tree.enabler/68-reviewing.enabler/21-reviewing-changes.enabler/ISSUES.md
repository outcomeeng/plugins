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

The failure repeated on 2026-07-22 from branch `work/unconditional-checkpoint-sync`. Four distinct `changes-reviewer` agents returned raw tokens that `render_review_run.py` could not resolve and reported as `journal run not found; open the run before operating on it`:

- agent `019f8b95-6543-7a41-93c4-aa802ae3631a`, token `2026-07-22_20-47-56-571-8d1c3ca4f544`;
- agent `019f8b9f-28d0-7bf3-b1e9-68cd944e31ba`, token `2026-07-22_20-58-34-471-ffe381ade072`;
- agent `019f8ba9-60aa-7a43-8b48-83ca80eb5e22`, token `2026-07-22_21-09-40-615-1ed65024e00f`;
- agent `019f8bbb-31d8-71f3-bce3-0db7b80a63ca`, token `2026-07-22_21-29-15-940-8390c8f3a5fe`.

The helper's current-scope render and sealed-run fallback found no matching run, so none of the four tokens produced an admissible review projection.

The failure was narrowed further on 2026-07-23. Agent `019f8bf8-9a97-7760-a38f-ea02669c855c` received raw scope `HEAD` and returned token `2026-07-22_22-36-47-423-1c75456d2b84`. Projection from the assigned `plugins-a` worktree reported the run missing, while projection from the canonical `plugins` worktree succeeded and showed an approved review of head `37c04c2f33ea5e2e10059a77c6b6778852bc5c01` instead of the assigned branch head `9737f096edd9bf742be5b3a775f699964546bbeb`. The token was present; the wrapper agent had resolved `HEAD` in a different worktree and reviewed the wrong changeset.

After rebasing the assigned branch, agent `019f8d43-f6a8-7f91-ac7c-b42949f6b3c5` received explicit raw scope `origin/main...work/unconditional-checkpoint-sync` and failed with `unknown revision or path not in the working tree`. The typed reviewer interface exposes no repository or working-directory selector, so a main session operating outside its native repository cannot direct the reviewer to an unpushed branch in the assigned worktree.

Required handling:

- Make review run lookup derive the same branch scope for wrapper-agent produced runs and main-session projection reads, or provide a supported branch-scope selector for `spx journal render` and `spx journal read`.
- Let typed reviewer dispatch bind an explicit repository or assigned worktree before resolving raw scope.
- Reject a projected review when its head and base identities differ from the caller's expected review subject.
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

Governing decision settled: `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md` amends the product-level scope model — the exclusion is a property of agentic verification only (deterministic verification keeps the complete changeset), the generated roots are a committed project-supplied declaration at `spx/local/generated-sources.toml` (never a hardcoded `dist/`), and findings about generated content resolve to the declaring relation's sources.

Required handling:

- Consume the declared attribution in this node's scope derivation as the reviewer's own derivation, never a caller filter, preserving the caller-independence rule this node already carries; the skip-and-record mechanics arrive with the `spx` verification scope projection tracked in `spx/31-outcomeeng.enabler/31-verification.enabler/PLAN.md`.
- Keep base-sync scope on the real changed-file set — the governing decision widens no exclusion beyond agentic verification.

## 8. The review-changes skill omits an explicit model pin

`src/plugins/spec-tree/skills/review-changes/SKILL.md` declares no `model` field, so a direct skill invocation inherits the session model. `skill-standards` states that marketplace verification-sensitive surfaces use explicit `sonnet` and never use session inheritance, and every `audit-*` skill in the spec-tree plugin pins `model: sonnet`. Review is a verification type whose findings decide `VERIFICATION_READINESS`, so an inherited model makes the review verdict depend on whichever model the invoking session happens to run.

The primary path is already pinned: the `changes-reviewer` agent declares `model: sonnet`, so agent-dispatched reviews are reproducible today. The gap is the direct skill-invocation path.

Required handling:

- Add `model: sonnet` to the `review-changes` skill frontmatter, matching the `audit-*` sibling convention.
- Regenerate the plugin runtime trees and the catalog so the pin reaches `dist/`.
- Re-run the skill auditor for the node after the change.

The sibling reference skill `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler` needs no pin: `scope-changeset` is `user-invocable: false` with `allowed-tools: Read`, supplying deterministic script primitives rather than a model-judged verdict.

## 9. Four shipped review scripts await extraction into the SPX CLI

The `review-changes` skill ships four scripts past the fifty-line threshold:

- `src/plugins/spec-tree/skills/review-changes/scripts/review_run.py` (645 lines) — the single command surface owning diff-bundle scratch storage, journal command invocation, state passing between verbs, and run sealing.
- `src/plugins/spec-tree/skills/review-changes/scripts/review_result.py` (610 lines) — the canonical `review-result` schema: wire-format version, the `Severity` and `Concern` vocabularies, and the document shape.
- `src/plugins/spec-tree/skills/review-changes/scripts/journal_emit.py` (508 lines) — the adapter bridging the review-result schema to the shared run-journal projection.
- `src/plugins/spec-tree/skills/review-changes/scripts/compute_diff.py` (423 lines) — base-ref and head-ref precedence resolution plus the committed, staged, unstaged, and untracked diff bundle.

Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; all four have proven their value in use, so extraction is what they owe. `21-script-decomposition.adr.md` already names `compute_diff.py`, `journal_emit.py`, and `review_result.py` as stop-gap modules, so their extraction completes a decomposition this node has already decided rather than opening a new one.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository.

**Resolution shape**: port the runner, the result schema, the journal adapter, and diff computation into the SPX CLI, publish it, advance the floor, and reduce the shipped skill to its instruction with no scripts. Entry 3 above already routes review-finding validation to that boundary, and the projection scripts extract with it per `spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/ISSUES.md`, so the four move as one surface rather than piecemeal. Revisit when the capability publishes.

Revisit entries 5 and 6 when review moves from `spx journal --type review` to `spx verification run`. Exercise the migration with an in-progress inspection before seal, repeated inspection of one file, restored prior-run context, and a final projection whose unique covered-unit count equals the changeset scope.
