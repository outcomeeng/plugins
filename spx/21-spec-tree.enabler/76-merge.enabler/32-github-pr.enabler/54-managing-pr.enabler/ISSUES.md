# Issues: PR Managing Protocol

## 1. Reviewer-skipped-by-design exception lacks an eval-backed scenario

The reviewer-skipped-by-design exception — `/merging-standards` `<authority_gates>`, `/manage-pr` Step 8, the `MENTION_REVIEW_NEEDED` action token — has a `managing-pr.md` compliance assertion declaring the mention-trigger but no scenario exercising the skip path and no dedicated eval.

A scenario for the skip path would fit the node's eval pattern:

> Given the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file and no current-head review exists, when the managing flow evaluates `MERGE_READINESS`, then it posts `<trigger-phrase> review` as a PR-level comment and emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`.

Required handling when an eval-coverage sweep happens:

- Add the scenario assertion above to `managing-pr.md`.
- Create `evals/reviewer-skipped/` with `eval.toml`, `cases.jsonl`, `prompt.md` per the cross-skill eval pattern.
- Run the eval to populate `history.jsonl`.

## 2. Worktree-safe branch-deletion default lacks eval coverage for the deletion mechanism

The `managing-pr.md` merge-command scenario declares two observable branch-deletion behaviors: the overlay-silent default runs the worktree-safe deletion sequence (`gh pr merge --merge --delete-branch=false`, then detach this worktree onto the refreshed base tip and delete the local and remote branches separately), and an overlay MAY opt into inline `gh pr merge --merge --delete-branch` for always-single-worktree projects. The retired `merge-command-overlay-precedence` eval verified only the merge-strategy flag and its source; no case exercised the deletion mechanism.

Required handling when an eval-coverage sweep happens:

- Add a scenario assertion to `managing-pr.md` (or extend the merge-command scenario) declaring the deletion-mechanism choice as a separately observable behavior.
- Create `evals/merge-cleanup-deletion/` with a verdict schema carrying a deletion-mechanism field, exercising the overlay-silent worktree-safe path and the single-worktree inline opt-in.
- Run the eval to populate `history.jsonl`.

Surfaced by the local `changes-reviewer` gate on `fix/worktree-safe-branch-deletion` (2026-06-07).

## 3. Retired merge-management evals need producer-backed replacements

The retired eval suites under `evals/merge-readiness/`,
`evals/merge-command-overlay-precedence/`, `evals/pr-check-wait/`, and
`evals/review-inspection-comments/` modeled `/manage-pr` behavior by prompting a
model to classify supplied JSON plans or state. They did not run the producing
`/manage-pr` skill, did not exercise the live PR inspection commands, and did
not prove the producer behavior declared by the node's assertions. The affected
assertions now use `[audit]` evidence until replacement evals can drive the real
producer surface and score parseable outputs.

Revisit condition:

- Add producer-backed evals for `MERGE_READINESS`, reviewer-skipped handling,
  merge-command selection, review-surface inspection, and foreground PR-check
  wait/re-entry behavior.
- Keep the eval prompts focused on the real producer artifact rather than a
  copied policy simulation.
- Run the canonical eval commands and commit each `history.jsonl`.

## 4. Review-thread resolver extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/manage-pr/scripts/resolve_review_thread.py` runs to 313 lines — resolution of one GitHub pull-request review thread. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; the resolver has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository.

**Resolution shape**: port thread resolution into the SPX CLI, publish it, advance the floor, and reduce the shipped skill to its instruction with no script. Thread resolution mutates pull-request state, so the ported surface keeps that mutation behind the same explicit-instruction boundary the product-level compliance rule requires and the `inspect-github-actions` mutation gate enforces today, tracked in `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/ISSUES.md`. Revisit when the capability publishes.

## 5. The PR-management skill restates its rules across workflow, failure modes and success criteria

`src/plugins/spec-tree/skills/manage-pr/SKILL.md` states several rules more than once: the clean current-head review predicate at four or five sites, the post-watch re-read rule at five sites with two verbatim, the `gh pr view --json` command pair at three sites, the foreground wait command at five sites, the `--return-closeout` marker semantics at three sites, the merge-composition qualifier on the evidence Auditors and the local review at five sites, and the pass-local token rule at three sites. Each copy must be kept in sync by hand. The cross-skill entry `DEBT [conciseness]` in `spx/21-spec-tree.enabler/76-merge.enabler/ISSUES.md` carries the same class for the other merge-lifecycle skills.

**Evidence:** `skill-auditor` runs `2026-10-06_18-23-28-029-1d92c59bd0d9` and `2026-10-06_18-27-45-474-4a44c6857fb0`, finding rule `conciseness`, severity `debt`.

**Why it is large:** stating each rule once means restructuring the skill around owning steps and references, an editorial pass over the whole file gated by the typed skill auditor, not a bounded edit inside the merge-composition changeset.

**Settlement condition:** each rule stated once at its owning step and referenced by step or tag name elsewhere, and one typed skill audit of `manage-pr` raising no `conciseness` finding.

## 6. The PR-management skill's description overlaps the GitHub-PR lifecycle skill's trigger

The description of `src/plugins/spec-tree/skills/manage-pr/SKILL.md` triggers on "managing, waiting on, or continuing an open pull request lifecycle", and the description of `src/plugins/spec-tree/skills/manage-github-pr/SKILL.md` triggers on "open or manage a GitHub pull request"; both fire on a request to manage a PR.

**Evidence:** `skill-auditor` run `2026-10-06_18-27-45-474-4a44c6857fb0`, finding rule `description-distinct`, severity `debt`.

**Why it is large:** separating the triggers changes which skill a consumer's request selects across the GitHub-PR transport, so both descriptions change together and both skills take the typed skill auditor; the merge-composition changeset edits neither description.

**Settlement condition:** the two descriptions carry trigger terms that select one skill for a request to manage an open PR, and one typed skill audit of each raises no `description-distinct` finding.

## 7. The PR-management skill wraps every section in a generic step tag

`src/plugins/spec-tree/skills/manage-pr/SKILL.md` marks its re-entry policy, its PR identity field list, its whole Step 0-9 workflow, its merge-readiness decision table and its merge command selection each as `<step name="...">`, and its prose refers to sections as "the `pr_identity_fields` step". The tag name carries no meaning, and the workflow section nests further `<step>` tags inside numbered steps.

**Evidence:** `skill-auditor` run `2026-10-06_18-51-23-618-78110f586d6b`, finding rule `semantic-tag-names`, severity `debt`, on lines 21, 33, 47, 98 and 137, none of which the merge-composition changeset touches.

**Why it is large:** renaming the sections changes every in-file reference and the cross-skill references other merge-lifecycle skills make to these sections, an editorial pass gated by the typed skill auditor.

**Settlement condition:** each section carries a semantic tag such as `<workflow>` or `<merge_readiness_decision_table>`, prose refers to sections by tag name, and one typed skill audit of `manage-pr` raises no `semantic-tag-names` finding.

## 8. The PR-management success criteria re-list the workflow steps

Most bullets of the `<success_criteria>` of `src/plugins/spec-tree/skills/manage-pr/SKILL.md` restate a workflow step, such as loading the references, inspecting three surfaces, checking base drift and running the foreground wait, instead of stating a property of the merged PR or the closeout-ready result.

**Evidence:** `skill-auditor` run `2026-10-06_18-51-23-618-78110f586d6b`, finding rule `success-criteria-properties`, severity `debt`; its cited bullets sit on lines 250, 251, 252, 256, 261 and 264, outside the changed lines 255 and 259 of the merge-composition changeset.

**Why it is large:** rewriting the criteria as output properties restates what proves a management pass sound for every step, together with the step restatements entry 5 records, an editorial pass gated by the typed skill auditor.

**Settlement condition:** each success criterion states a property of the merged PR, the closeout-ready result or the reported blocking condition, and one typed skill audit of `manage-pr` raises no `success-criteria-properties` finding.

## 9. `manage-pr` carries seven skill-audit debt findings

`instructions:skill-auditor` run `2026-10-06_18-43-57-466-ceb2c552ad89` rejected the post-edit audit of `manage-pr` at head `4be7a922d11c27af632039953b5baf36db8b999f` on seven `debt` findings. The changeset's diff of `src/plugins/spec-tree/skills/manage-pr/SKILL.md` is lines 40 and 43; the script is outside it. No finding lies on changed text.

- Rule `ambiguous-instruction`, `SKILL.md` line 240 (`<failure_modes>`, "Used GitHub mergeability as authority"): the avoidance step ends "emit the wait token and refresh tracking", and no section defines a tracking mechanism.
- Rule `internal-consistency`, `SKILL.md` line 236 (`<failure_modes>`, "Wait-token-only without the foreground wait"): the failure mode attributes the foreground wait to Step 8, and the workflow assigns it to Step 7.
- Rule `anti-pattern-repeating-skill-name`, `SKILL.md` lines 23 and 27 (`pr_wait_and_reentry_policy`): the body invokes `/manage-pr` and names it as the actor.
- Rule `xml-semantic-names`, `SKILL.md` lines 47-159 (`the_managing_flow`): Steps 0-9 sit in a `step` container with three nested `step` tags while the other steps are bold-prose paragraphs.
- Rule `tool-restriction-grant-coverage`, `SKILL.md` frontmatter line 6 and Step 6 at line 72: Step 6 instructs `mktemp -d`, and `allowed-tools` grants no `mktemp` pattern.
- Rule `conciseness`, `SKILL.md` lines 90, 133, and 153, and the clean-review predicate at lines 118, 130, 232, and 256: the wait-routing instruction and the predicate definition are restated.
- Rule `script-validation-message`, `scripts/resolve_review_thread.py` line 237 (`iter_thread_comments`): a malformed review-thread node `id` raises the CLI-argument message `thread_id must be a GitHub node ID` instead of naming the response field.

`instructions:skill-auditor` run `2026-10-07_06-38-38-191-06ac6f474845` rejected the audit of `manage-pr` at head `3f9a679fe2e4b2531e671242bb8242cb7c14dc8c` on eight `debt` findings. The changeset's diff of `src/plugins/spec-tree/skills/manage-pr/SKILL.md` against the base is lines 40 and 43 and the decision table rows at lines 102 to 113; the script is outside it. No finding lies on changed text. The run repeats six of the seven findings above (`anti-pattern-repeating-skill-name`, `xml-semantic-names`, `conciseness`, the step-number inconsistency and the undefined tracking action, and `script-validation-message` at lines 146 and 237 of the script) and adds the `description-trigger-conflict` finding that entry 6 records. It raised no `tool-restriction-grant-coverage` finding.

**Impact.** A reader of the skill meets a tracking mechanism that does not exist, two step numbers for one command, and a Step 6 command outside the grant.

**Settlement condition.** Each of the seven findings is resolved in the skill and its script, and one typed skill audit of `manage-pr` then raises none of them.

## 10. The review-thread resolver pages GraphQL connections without a page count

`src/plugins/spec-tree/skills/manage-pr/scripts/resolve_review_thread.py` discovers a review thread from a review-comment ID by reading `reviewThreads(first: 100, after: $threadsAfter)` and, for each thread, `comments(first: 100, after: $commentsAfter)`. The loops at lines 183 and 264 continue while `hasNextPage` stays true and carry no page count, and `managing-pr.md` line 28 requires the discovery to page through both connections before declaring a review comment absent. The rationale of `spx/15-agent-tools.pdr.md` names an unbounded paginated GraphQL read as the hazard to the account-wide GraphQL budget, and product property 3 reaches the `gh` calls a skill's text instructs, so a call a shipped script issues is outside the property and its audit rule.

`spec-tree:changes-reviewer` run `2026-10-06_18-56-26-316-837e0b2a122f` on head `27de076ed368f5eee6477012d9526a89a8af2b77` raised this as a `consistency` finding against the script at line 183.

**Settlement condition.** A decision states whether the page-bound rule covers calls a shipped script issues, and the script bounds each loop with a page count and ends in a deterministic error naming the bound; `managing-pr.md` line 28 and its linked test follow.
