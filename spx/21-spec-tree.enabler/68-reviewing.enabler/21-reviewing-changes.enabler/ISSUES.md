# ISSUES - review-changes

Known issues for `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`.

## Consumer inspections are not journaled as review scope

The review prompt's scope reaches unchanged consumers of a changed governing declaration, but `review_run.py finish` rejects a scope-advanced event whose unit is outside `changedFiles`, so an inspected consumer is recorded only when it yields a finding. Coverage of consumers that were inspected and found clean is invisible to the journal projection.

**Resolution shape**: when review moves into the SPX CLI (entry 9), generalize the scope unit from "changed file" to "reviewed unit" with a `scopeKind` of `changed`, `consumer`, or `governance`, project authoritative coverage from the changed-file units, and record consumer units as inspected without making them a `finish` precondition. Not a bounded fix here: it changes the runner's scope contract in a script owed to extraction.

## Eval lane suspended while the node is `tier: prototype`

The node's LLM-behavior assertions — rule-citation grounding, absence-claim discipline, severity rubric fit, wrapper protocol, findings direction, and the adversarial probes — carry `[audit]` evidence while the spec declares `tier: prototype`; the eval harness is unavailable for producer-coupled evidence. The `tier` frontmatter field is ahead of its declaration: `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/PLAN.md` defers tier until the CLI projects the frontmatter field and spec-audit recognizes it, so this node carries the key by operator direction before that schema lands (review run `2026-08-16_20-27-53-613-16cfc8848697`, one debt finding, tracked here).

**Resolution shape**: when the eval facility runs again, author one producer-coupled eval per assertion class through `prompt_source.producer` pointing at the shipped review prompt, relink the assertions as `[eval]`, and drop the tier marker. Cases for the probes: a diff asserting an exhaustive or mutually exclusive partition with a constructible hole; a restated rule with a dropped conjunct; a newly bound definite description with no owner; an unchanged cited consumer the change contradicts.

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

## 9. Four shipped review scripts await extraction into the SPX CLI

The `review-changes` skill ships four scripts past the fifty-line threshold:

- `src/plugins/spec-tree/skills/review-changes/scripts/review_run.py` (645 lines) — the single command surface owning diff-bundle scratch storage, journal command invocation, state passing between verbs, and run sealing.
- `src/plugins/spec-tree/skills/review-changes/scripts/review_result.py` (610 lines) — the canonical `review-result` schema: wire-format version, the `Severity` and `Concern` vocabularies, and the document shape.
- `src/plugins/spec-tree/skills/review-changes/scripts/journal_emit.py` (508 lines) — the adapter bridging the review-result schema to the shared run-journal projection.
- `src/plugins/spec-tree/skills/review-changes/scripts/compute_diff.py` (423 lines) — base-ref and head-ref precedence resolution plus the committed, staged, unstaged, and untracked diff bundle.

Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; all four have proven their value in use, so extraction is what they owe. `21-script-decomposition.adr.md` already names `compute_diff.py`, `journal_emit.py`, and `review_result.py` as stop-gap modules, so their extraction completes a decomposition this node has already decided rather than opening a new one.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository.

`review_result.py` also probes this repository's own `src/plugins/`, `dist/claude/`, and `dist/codex/` layout before its portable runtime-relative candidates when resolving a plugin-skill citation; those authoring-layout candidates never exist in a consumer checkout and leave with the extraction.

**Resolution shape**: port the runner, the result schema, the journal adapter, and diff computation into the SPX CLI, publish it, advance the floor, and reduce the shipped skill to its instruction with no scripts. Entry 3 above already routes review-finding validation to that boundary, and the projection scripts extract with it per `spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/ISSUES.md`, so the four move as one surface rather than piecemeal. Revisit when the capability publishes.

## 10. Agentic verification judges a mandated architectural seam without the decision that mandates it

A review of a shipped-script changeset raised the injected `Runner` Protocol in `src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` as unexercised surface, and offered two remedies: delete the seam, or add an ADR rule mandating it plus a test injecting a controlled `Runner`. Both are blocked by decisions above the node under review. `spx/12-shipped-scripting.adr.md` requires the seam (`shipped Python that invokes external tools accepts a dependency-injected runner implementing a Protocol at the orchestration boundary`), as does `spx/13-plugin-and-runtime-conventions.adr.md`; the same shipped-scripting decision permits a controlled runner only under `/test` Stage 5 exception 1 or 2, and git is an L1 real dependency that Stage 4 terminates on, so no exception opens. A node-level ADR rule restating a product-level one is misplacement besides.

Both surfaces resolve scope from the changed-file set, and neither product-level decision appears in a diff confined to one skill, so the mandate is invisible from the scope alone. Every shipped script in the marketplace carries this seam, so the false positive recurs on each one and costs a round to refute each time.

The cost is not symmetric across the two surfaces. A review states findings and the author disposes of them, so an unbacked finding costs one refutation. The implementation audit returns a terminal status, and `rejected` withholds the gate outright, so the same unbacked finding blocks until the auditor is re-dispatched with the mandating decisions in its role task. Scope derivation that reaches only the diff therefore turns a compliant, decision-mandated seam into a gate stop.

**Resolution shape**: give agentic-verification scope derivation the governing decisions for the changed paths — the same ancestor-and-cited-decision read-set `/contextualize` derives — so a mandated architectural seam is judged against the decision that mandates it rather than against the diff alone. This covers the review run and the implementation-audit run alike, since both derive scope the same way.

**Why it is separate**: the fix changes what context an agentic verification run loads, which belongs to this node's scope derivation and its eventual SPX extraction (entry 9), not to any changeset that happens to ship a script carrying the seam.

**Evidence**: review run `2026-08-05_13-13-52-179-c96364b3dc5f`, one debt finding on an otherwise approved review. Then implementation-audit run `2026-08-05_21-52-18-042-b561b26753fb` on the same script, `terminalStatus: rejected` on the single finding `design-coherence: speculative dependency-injection seam with no consumer`, whose stated expectation — that a seam arrive with a consumer or be deferred — is the opposite of what `spx/12-shipped-scripting.adr.md` requires, and whose asked-for test consumer that same decision permits only under a `/test` Stage 5 exception no L1 git dependency opens. Both were dropped as unbacked after `/test` routing and the two decisions above.

Revisit entries 5 and 6 when review moves from `spx journal --type review` to `spx verification run`. Exercise the migration with an in-progress inspection before seal, repeated inspection of one file, restored prior-run context, and a final projection whose unique covered-unit count equals the changeset scope.

## Consolidated implementation plan

The remaining tasks below harden the current `review-changes` implementation. They are implementation work, not active issue-driven defects.

### Plan items

1. Add deterministic finding-location validation.
   - Add a stdlib-only validator that compares each finding location with the diff emitted by `compute_diff.py` and with the repository.
   - Reject a finding on a changed file whose `file:line` is outside the changed coordinates visible to the review input, and reject a finding on an unchanged consumer whose `file:line` does not exist — the consumer case is admitted by design, since review scope reaches unchanged consumers of a changed governing declaration.
   - Wire the check into the per-finding path before journal emission, or into the SPX finding validation entry 3 routes there.

### Coordination

Run `/understand`, then `/contextualize spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` before acting. Verify each item against the current review prompt, policy module, journal adapter, and tests before implementation.

### Salvage plan for prompt single-source cleanup

Source branch: `work/review-prompt-single-source`

Source PR: `https://github.com/outcomeeng/plugins/pull/387`

Source head: `a3d65439c501a0f53bf7a8971fa0539e0cd5013b`

Current replacement branch: `work/review-prompt-single-source-v2`

Objective: merge the review prompt single-source cleanup without carrying the local hand-rolled preview workflow from the discarded branch.

#### Keep

- `REVIEW.md`: remove the repository-root review override so the shipped skill reference prompt is the only live review prompt authority.
- `REVIEW.example.md`: remove the unused example prompt so consumers do not copy a parallel prompt contract.
- `methodology/research/review-prompt.md`: remove the duplicate research prompt when it repeats the live prompt content.
- `src/plugins/spec-tree/skills/review-changes/SKILL.md`: preserve the runner-only workflow and raw-run-token caller output; remove `REVIEW.md` from review materials and workflow steps.
- `src/plugins/spec-tree/skills/review-changes/references/review-prompt.md`: preserve the tightened review prompt that forbids deterministic verification, requires streaming single-finding objects, rejects caller steering, and keeps rule citations grounded in loaded context.
- `src/plugins/spec-tree/skills/review-changes/scripts/review_run.py`: preserve scope-coverage enforcement before `finish` when the implementation still needs it on current `origin/main`.
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md`: update assertions so the bundled prompt is the sole review context and repository-root prompt files are not loaded.
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md`: keep the decision aligned with the single runner and journal-only durable state.
- Co-located tests for the retained behavior: preserve only the assertions required for bundled-prompt single source, raw token output, no root prompt loading, scope coverage, and journal event behavior.
- Generated `dist/claude/spec-tree/**` and `dist/codex/spec-tree/**`: regenerate from `src/plugins/spec-tree/**` with `just build-skills`; do not hand-copy generated content from the discarded branch.

#### Inspect Before Keep

- `src/plugins/spec-tree/skills/review-changes/scripts/journal_emit.py` and `review_result.py`: keep only changes still required by current tests and the live runner contract; avoid restoring review-specific finding validation into the skill path because `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/ISSUES.md` records that validation belongs in SPX.
- `outcomeeng_testing/harnesses/reviewing_changes.py`: keep only fixture cleanup directly tied to removed root prompt policy or obsolete citation domains.
- `spx/local/merging.md`: keep only review lifecycle wording that remains correct without the local preview workflow.

#### Discard

- `.github/workflows/review-changes-preview.yml`: discard the hand-rolled local workflow. The wanted preview is a thin caller of the reusable verification host from `outcomeeng/gh-actions`.
- `.github/workflows/spec-tree-review.yml`: discard comments or behavior that make the local `review-changes-preview.yml` workflow canonical.
- Commits `b5f5682742b22f8121d7d6b13d795b0aa10e5e7b`, `73fd856a16c32890769028746b794a0fd82e6986`, `82e96b29e1acfb27c452ed51118f2a14580125e1`, `bad2a8d58fe038f656281b86f792df62ca15c2dc`, `59ae3dbfc79865e2eadf0a0144863dbbb8f93526`, `c610caa2d1f27eaa20ae7c3469ad71f44911d927`, and `a3d65439c501a0f53bf7a8971fa0539e0cd5013b`: discard the local preview implementation and permission-envelope churn.
- Any generated root guide or unrelated marketplace-wide distribution churn visible only because `work/review-prompt-single-source` is stale against current `origin/main`.

#### Merge Path

1. Apply the retained source changes onto `origin/main` on `work/review-prompt-single-source-v2`.
2. Regenerate plugin distributions with `just build-skills`.
3. Run scoped deterministic verification for the touched review-changes tests and skill/doc checks.
4. Run `changes-reviewer` on the exact final tree and fix valid findings.
5. Open and manage a replacement PR through the standard merge lifecycle.
6. Close PR #387 after the replacement PR is open and carries the retained prompt work.

### Strict-finding-disposition extraction

Reconstruct the preserved review-journal and result-contract work from current `origin/main` as one review-owned merge cycle only when the patch has one observable result: the review skill records grounded findings in a sealed journal and returns one raw run token through source-owned evidence infrastructure.

The extraction includes this node's spec, review prompt, journal runner and result contracts, co-located tests and evals, and the smallest review-specific harness or generator changes they require. Eval-harness capabilities that can merge independently remain in `spx/13-infrastructure.enabler/25-eval-harness.enabler/PLAN.md`; merge policy that consumes the token remains in `spx/21-spec-tree.enabler/76-merge.enabler/PLAN.md`.

**Revisit condition:** replace this section with the extracted branch and PR identity after focused tests, evidence audits, and rollback analysis establish one review-owned cluster.
