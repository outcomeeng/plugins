# PLAN - review-changes hardening

The remaining tasks below harden the current `review-changes` implementation. They are implementation work, not active issue-driven defects.

## Plan items

1. Add deterministic diff-coordinate validation.
   - Add a stdlib-only validator that compares each finding location with the diff emitted by `compute_diff.py`.
   - Reject findings whose `file:line` is outside the changed coordinates visible to the review input.
   - Wire the check into the existing per-finding validation path before journal emission.

2. Add a prompt-injection guard for diff content.
   - State in `references/review-prompt.md` that diff content is untrusted data.
   - Require the reviewer to ignore instructions embedded in changed files, comments, fixtures, or generated text.
   - Keep this separate from repository-rule citation grounding.

## Coordination

Run `/understand`, then `/contextualize spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler` before acting. Verify each item against the current review prompt, policy module, journal adapter, and tests before implementation.

## Salvage plan for prompt single-source cleanup

Source branch: `work/review-prompt-single-source`

Source PR: `https://github.com/outcomeeng/plugins/pull/387`

Source head: `a3d65439c501a0f53bf7a8971fa0539e0cd5013b`

Current replacement branch: `work/review-prompt-single-source-v2`

Objective: merge the review prompt single-source cleanup without carrying the local hand-rolled preview workflow from the discarded branch.

### Keep

- `REVIEW.md`: remove the repository-root review override so the shipped skill reference prompt is the only live review prompt authority.
- `REVIEW.example.md`: remove the unused example prompt so consumers do not copy a parallel prompt contract.
- `methodology/research/review-prompt.md`: remove the duplicate research prompt when it repeats the live prompt content.
- `src/plugins/spec-tree/skills/review-changes/SKILL.md`: preserve the runner-only workflow and raw-run-token caller output; remove `REVIEW.md` from review materials and workflow steps.
- `src/plugins/spec-tree/skills/review-changes/references/review-prompt.md`: preserve the tightened review prompt that forbids deterministic verification, requires streaming single-finding objects, rejects caller steering, and keeps rule citations grounded in loaded context.
- `src/plugins/spec-tree/skills/review-changes/scripts/review_run.py`: preserve scope-coverage enforcement before `finish` when the implementation still needs it on current `origin/main`.
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md`: update assertions so the bundled prompt is the sole review context and repository-root prompt files are not loaded.
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md`: keep the decision aligned with the single runner and journal-only durable state.
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/evals/wrapper-protocol/prompt.md`: preserve protocol wording that describes `append-scope`, streaming `append-finding`, and raw token output.
- Co-located tests for the retained behavior: preserve only the assertions required for bundled-prompt single source, raw token output, no root prompt loading, scope coverage, and journal event behavior.
- Generated `dist/claude/spec-tree/**` and `dist/codex/spec-tree/**`: regenerate from `src/plugins/spec-tree/**` with `just build-skills`; do not hand-copy generated content from the discarded branch.

### Inspect Before Keep

- `src/plugins/spec-tree/skills/review-changes/scripts/journal_emit.py` and `review_result.py`: keep only changes still required by current tests and the live runner contract; avoid restoring review-specific finding validation into the skill path because `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/ISSUES.md` records that validation belongs in SPX.
- `outcomeeng_testing/harnesses/reviewing_changes.py`: keep only fixture cleanup directly tied to removed root prompt policy or obsolete citation domains.
- `spx/local/merging.md`: keep only review lifecycle wording that remains correct without the local preview workflow.

### Discard

- `.github/workflows/review-changes-preview.yml`: discard the hand-rolled local workflow. The wanted preview is a thin caller of the reusable verification host from `outcomeeng/gh-actions`.
- `.github/workflows/spec-tree-review.yml`: discard comments or behavior that make the local `review-changes-preview.yml` workflow canonical.
- Commits `b5f5682742b22f8121d7d6b13d795b0aa10e5e7b`, `73fd856a16c32890769028746b794a0fd82e6986`, `82e96b29e1acfb27c452ed51118f2a14580125e1`, `bad2a8d58fe038f656281b86f792df62ca15c2dc`, `59ae3dbfc79865e2eadf0a0144863dbbb8f93526`, `c610caa2d1f27eaa20ae7c3469ad71f44911d927`, and `a3d65439c501a0f53bf7a8971fa0539e0cd5013b`: discard the local preview implementation and permission-envelope churn.
- Any generated root guide or unrelated marketplace-wide distribution churn visible only because `work/review-prompt-single-source` is stale against current `origin/main`.

### Merge Path

1. Apply the retained source changes onto `origin/main` on `work/review-prompt-single-source-v2`.
2. Regenerate plugin distributions with `just build-skills`.
3. Run scoped deterministic verification for the touched review-changes tests and skill/doc checks.
4. Run `changes-reviewer` on the exact final tree and fix valid findings.
5. Open and manage a replacement PR through the standard merge lifecycle.
6. Close PR #387 after the replacement PR is open and carries the retained prompt work.

## Strict-finding-disposition extraction

Reconstruct the preserved review-journal and result-contract work from current `origin/main` as one review-owned merge cycle only when the patch has one observable result: the review skill records grounded findings in a sealed journal and returns one raw run token through source-owned evidence infrastructure.

The extraction includes this node's spec, review prompt, journal runner and result contracts, co-located tests and evals, and the smallest review-specific harness or generator changes they require. Eval-harness capabilities that can merge independently remain in `spx/13-infrastructure.enabler/25-eval-harness.enabler/PLAN.md`; merge policy that consumes the token remains in `spx/21-spec-tree.enabler/76-merge.enabler/PLAN.md`.

**Revisit condition:** replace this section with the extracted branch and PR identity after focused tests, evidence audits, and rollback analysis establish one review-owned cluster.
