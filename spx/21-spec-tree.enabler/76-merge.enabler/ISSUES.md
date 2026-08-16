# Issues — Merging

Known follow-ups for the merging node. Coordination note; not spec truth.

## The CLOSE-phase fresh-handoff explanation is restated in three skill surfaces

The rule that a transport never authors the closeout and a prior same-conversation `/handoff` never satisfies `CLOSE` lives canonically in `src/plugins/spec-tree/skills/merging-standards/references/merge-policy.md` `<close_phase>`, and `src/plugins/spec-tree/skills/merge/SKILL.md` (Step 4, Step D5, one failure mode, success criteria) and `src/plugins/spec-tree/skills/manage-github-pr/SKILL.md` (Step 7, Failure 4, success criteria) each restate the mechanism and the cheapness rebuttal in their own wording. The `skill-auditor` (finding `f-005`, rule `conciseness`, severity `WARNING`, on the changeset that introduced the rule) proposes keeping the canonical explanation in `<close_phase>` and reducing the transport skills to a citation plus their local signal and avoid-action, because the introducing changeset itself had to hunt one wording drift across three authored files.

**Why it is large**: the consolidation restructures how the rule is taught across three shipped skill surfaces and trades against the same auditor's `keep-these-aspects` rows, which value the self-contained failure-mode narratives; resolving that tension is an editorial pass over the whole CLOSE teaching shape, gated by `skill-auditor`, not a wording fix inside the introducing changeset.

**Revisit condition**: the next changeset that restructures `merging-standards` or either transport skill's CLOSE teaching.

## `merge-policy.md` loads 510 lines for any one of its 24 sections

`src/plugins/spec-tree/skills/merging-standards/references/merge-policy.md` spans 24 tagged sections, and `merging-standards`'s `<reference_index>` instructs reading it whole before any detailed merge-lifecycle operation. A composing step that needs only `<branch_hygiene>` or `<review_classification>` pays the full payload. The file carries the `<contents>` index its length requires, so this violates no standard today.

`<review_classification>` is the strongest split candidate: `manage-pr` Step 3 already reaches it independently, and its taxonomy cross-references little else. A split file would hang directly off `SKILL.md`'s index, as `merge-cleanup.md` and `action-tokens.md` already do, so the no-reference-dispatches-a-reference rule holds.

**Why separate**: splitting a shared reference every merge transport loads means re-verifying each composing skill's read path, and the section boundaries need checking against actual cross-references rather than the tag list — work independent of any changeset that edits the file's content.

**Revisit condition**: when a changeset next restructures `merging-standards` rather than editing one of its sections. Surfaced by `skill-auditor` on the release-overlay changeset as finding `f-006`, rule `progressive_disclosure_token_cost`, severity `WARNING` in the `worth-improving` row. That role returns a JSON verdict and no journal run token, so the finding identifier and rule are its whole citable identity.

## The overlay's base-checkout fast-forward has no deterministic coverage

`spx/local/merging.md` declares a deploy-phase fast-forward of the designated main checkout with four outcomes — advanced, `held-by-live-session`, `uncommitted-work`, `not-fast-forwardable` — and no `[test]` or `[eval]` exercises any of them. The behavior reaches the spec tree through its own `[audit]`-backed assertion in `spx/21-spec-tree.enabler/76-merge.enabler/merge.md`, alongside the product-local overlay assertion, so the gap is consistent with its neighbours rather than an unbacked claim.

Deterministic coverage needs a harness that materializes a bare-repository pool with a designated main checkout and drives each outcome — a live claim, a dirty tree, a diverged local `main` — which no existing merging harness models.

**Resolution shape**: fold these outcomes into the eval-coverage sweep the prompt-only-simulation entry below already schedules, since both need the same worktree-state modelling the current merge eval harnesses lack.

**Revisit condition**: when `evals/local-completion-boundary` and `evals/transport-selection` are converted to producer-coupled evals.

## Transport classifier extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/merge/scripts/classify_changeset.py` runs to 161 lines — the coordination-note-only classification over the full changed-file set, committed branch scope plus uncommitted working-tree changes, with counts computed over the whole set so a large changeset is never misclassified from a truncated sample. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; the classifier has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository.

**Resolution shape**: port the classification into the SPX CLI together with the base-ref and branch-scope derivation it routes through, tracked in `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/ISSUES.md`; publish, advance the floor, and reduce the shipped skill to its instruction with no script. Keep whole-set counting across the move — the truncation guard is the classifier's correctness property, not an implementation detail. The transport-selection wording entry below governs how the result is reported, so it applies to the ported surface too. Revisit when the capability publishes.

## Transport-selection status message exposes classifier internals

`/merge` can report the selected transport with raw classifier counts and a mechanical delegation sentence:

```text
Transport selected: GitHub PR, because the classification has 2 changed files and 2 non-coordination-note files. I'm delegating to /manage-github-pr, which owns branch creation, commit, PR opening, checks, review, and merge.
```

The status is technically traceable to the transport-selection policy in `spx/21-spec-tree.enabler/76-merge.enabler/merge.md`, but it is the wrong operator surface. It leaks count-level classifier implementation detail, over-narrates delegation, and reads as a handoff rather than a lifecycle step the merge skill continues to own. A future merging-skill change should adjust the `/merge` transport-selection wording and eval expectations so the message names the selected transport and the policy reason at the user-facing level: coordination-note-only changes use direct-push, overlay-declared transport wins, otherwise GitHub PR. The message should avoid raw changed-file counts unless the count is itself the decision boundary the operator needs to inspect.

## Generated instruction-block lifecycle vocabulary window

`spx/15-merging.pdr.md` declares four readiness gates and the lifecycle `VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE`, while the generated instruction blocks still teach the installed `merging-standards` vocabulary until the shared methodology PR updates `src/plugins/spec-tree/skills/merging-standards/SKILL.md` and regenerates instruction-block output.

Required handling:

- Update `src/plugins/spec-tree/skills/merging-standards/SKILL.md` in the shared methodology PR.
- Run `just build-skills` and `just build-instructions`.
- Verify the generated instruction blocks in root `CLAUDE.md` and `AGENTS.md` no longer teach the old three-gate or production-readiness lifecycle.

## Merge lifecycle eval suites are prompt-only simulations

`eval-evidence-auditor` runs `019f4219-ac8e-7b92-96db-fefd48bf8b41` and
`019f421a-01ad-7ac0-b1f8-abc05f458dc7` reported that the
`local-completion-boundary` and `transport-selection` eval suites do not prove
the producing merge lifecycle behavior:

- `local-completion-boundary` simulates status assessment in
  [`prompt.md`](evals/local-completion-boundary/prompt.md); replacing
  [`src/plugins/spec-tree/skills/merge/SKILL.md`](../../../src/plugins/spec-tree/skills/merge/SKILL.md)
  or [`spx/local/merging.md`](../../local/merging.md) would not change the
  evaluated behavior.
- `local-completion-boundary` covers the local-stop/local-pause branch, but not
  continuation through default-branch merge, declared deploy/release phases, and
  closeout.
- `transport-selection` grades a static prompt/case model without materializing
  or directly invoking
  [`src/plugins/spec-tree/skills/merge/SKILL.md`](../../../src/plugins/spec-tree/skills/merge/SKILL.md).
- Both suites hard-code the policy in the prompt, so the grader can keep passing
  after the producer changes.

Revisit condition: run `/apply` on
`spx/21-spec-tree.enabler/76-merge.enabler` to convert
`evals/local-completion-boundary` and `evals/transport-selection` to
producer-coupled evals, or reclassify/remove the `[eval]` assertions they no
longer support. Rerun `eval-evidence-auditor` over the repaired eval artifacts.

### PR-lifecycle skills carry no eval trigger

`transport-selection` does not own the `manage-github-pr` or `open-pr` skills.
Its `prompt.md` names `manage-github-pr` only as the literal `delegation_target`
string its own decision rule dictates, never loading that skill's content, and
`open-pr` appears in neither `prompt.md` nor `cases.jsonl`. Replacing either
skill's `SKILL.md` with unrelated text changes no case outcome, so a CI trigger
on those paths starts a job that cannot detect the change that started it.

Those four trigger paths therefore carry no `owned_paths` declaration and no
generated trigger entry. Declaring them would assert a producer coupling the
suite does not have.
[`spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md`](../../13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md)
requires a skill eval to couple to its real producer through direct invocation,
harness-mediated invocation, or source-derived prompt materialization, and
refuses a prompt-only simulation as evidence for that producer. This suite does
none of those for either skill.

Revisit condition: this resolves with the prompt-only simulation above. Once
`transport-selection` materializes its prompt from a declared `prompt_source`
producer, declare the producers the materialized prompt actually reads — then
the generator derives their trigger paths, and a mutation to those skills
genuinely changes a case outcome.

## The direct-push lifecycle carries no worked example

`src/plugins/spec-tree/skills/merge/SKILL.md` `<direct_push_lifecycle>` governs a push straight to the default branch on origin through named gates and predicates with no concrete trace — a selected transport, an overlay configuration, the push command, the resulting full SHA — that an in-progress run can be compared against before the push completes.

**Resolution shape**: add one worked before/after example to `<direct_push_lifecycle>`, gated by `instructions:skill-auditor`. The example is a content addition to a section the reload-timing changeset does not touch, so it ships as its own change.

**Evidence.** Surfaced by the `skill-auditor` review of `src/plugins/spec-tree/skills/merge/SKILL.md` on the post-compaction reload-timing change (finding `abstract_examples`).

## The GitHub-PR lifecycle skill carries no worked mode-to-step example

`src/plugins/spec-tree/skills/manage-github-pr/SKILL.md` routes four modes (Open PR, Instructed, Existing changeset, Empty) through a seven-step lifecycle and states how the mode is detected, with no `<examples>` block showing one concrete state signal per mode and the step sequence it produces.

**Resolution shape**: add one short example per mode naming the observed repository state and the resulting step sequence, gated by `instructions:skill-auditor`. The examples are a content addition to the skill's routing surface, separate from the reload-timing rule.

**Evidence.** Surfaced by the `skill-auditor` review of `src/plugins/spec-tree/skills/manage-github-pr/SKILL.md` on the post-compaction reload-timing change (finding `no_examples_section`).

## The PR-management skill restates its post-watch re-entry rule twice

`src/plugins/spec-tree/skills/manage-pr/SKILL.md` carries the sentence "and immediately return to Step 1 in the same turn. Do not merge or emit a final token from pre-watch state. The post-watch pass must re-read PR state, check rollup, PR-level comments, formal reviews, and review-thread comments before deciding the next action." verbatim at two sites (the wait step and the merge-readiness evaluation).

**Resolution shape**: state the rule once at the merge-readiness evaluation and cross-reference it from the wait step, gated by `instructions:skill-auditor`.

**Evidence.** Surfaced by the `skill-auditor` review of `src/plugins/spec-tree/skills/manage-pr/SKILL.md` on the post-compaction reload-timing change (finding `duplicate_content`).

## The merge-readiness decision table carries no worked trace

`src/plugins/spec-tree/skills/manage-pr/SKILL.md` `<merge_readiness_decision_table>` enumerates eleven rules over named predicate fields with no example tracing one concrete `gh pr view --json` field set through a matched rule to its emitted guard verdict.

**Resolution shape**: add one worked trace — sample JSON fragment, matched rule number, emitted `guard_verdict` — gated by `instructions:skill-auditor`.

**Evidence.** Surfaced by the `skill-auditor` review of `src/plugins/spec-tree/skills/manage-pr/SKILL.md` on the post-compaction reload-timing change (finding `abstract_examples`).
