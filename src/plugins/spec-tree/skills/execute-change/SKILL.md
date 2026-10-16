---
name: execute-change
description: >-
  ALWAYS invoke this skill when a session executes one claimed Executable Change as its Executor. NEVER run a Change's Governance mutations and Spec mutations blocks without this skill.
argument-hint: "[#N | owner/repo#N | issue-url]"
allowed-tools: Read, Glob, Grep, {{! tool('use_skill') !}},{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}},{!% endif %!} Bash(git status:*), Bash(git rev-parse:*), Bash(git log:*), Bash(git fetch:*), Bash(git switch:*), Bash(git push:*), Bash(gh issue view:*), Bash(gh issue comment:*), Bash(gh pr view:*), Bash(gh api graphql:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by --method GET -F per_page=100), Bash(spx worktree status:*)
---

<objective>
One claimed Executable Leaf carried to its end: its changeset on the default branch and the Change closed as `Applied`, or the Change released with a Handoff that names why execution stopped.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; its rules govern every store read below by their `id`.

Use skill `spec-tree:change-standards`. Invoke it with `Executable`; its `merge_composition` derives each block's results and Verifiers, because the record names none.

Use skill `spec-tree:wait-for-load`. Run the waiter and every resource-intensive command any step below runs as one line in the foreground, and report a result only after every such line has exited.

</required_reading>

<definitions>

Each round's producing session is one subagent of the definition that fronts the skill the content the round produces needs. A `## Governance mutations` block produces the decision record at its path. A `## Spec mutations` block produces its Node's spec and, by the Node's malleability after and the tags of its assertions, the results the `merge_composition` requires for that malleability: verification selection and test evidence for the assertions tagged `[test]` or `[eval]`, implementation when the malleability after is `implementation`, and a Verifier's verdict for an `[audit]` assertion. Content that is a skill surface or a subagent definition selects the matching definition:

| Content the round produces                                                                       | Definition                                                     | Skill it fronts                |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- | ------------------------------ |
| A decision record, spec, node, note, or other artifact `/author` writes                          | `{{! subagent_name('spec-tree', 'change-author') !}}`          | `spec-tree:author`             |
| Verification selection for a node's or decision's claims                                         | `{{! subagent_name('spec-tree', 'change-verifier') !}}`        | `spec-tree:verify`             |
| Test evidence for assertions routed to test                                                      | `{{! subagent_name('spec-tree', 'change-tester') !}}`          | `spec-tree:test`               |
| Implementation of a node in its language                                                         | `{{! subagent_name('spec-tree', 'change-implementer') !}}`     | `spec-tree:implement-change`   |
| A skill surface: a `SKILL.md`, another file in a skill directory, or an authored shared fragment | `{{! subagent_name('spec-tree', 'change-skill-author') !}}`    | `instructions:create-skill`    |
| A subagent definition                                                                            | `{{! subagent_name('spec-tree', 'change-subagent-author') !}}` | `instructions:create-subagent` |

A Fixer is a fresh session of the definition the round's Author used, and its task message follows the Fixer entry below. The task message of each Author session follows its definition:

- `{{! subagent_name('spec-tree', 'change-author') !}}` Author: the canonical `spx/...` path of the node or decision it produces, followed by the Change's issue URL, because `/author` reads the Output's requirements from the Change.
- `{{! subagent_name('spec-tree', 'change-skill-author') !}}` Author: the `instructions:create-skill` intent the block selects — a Node whose malleability before is `none` selects create, any other Node selects improve — or the intent the block names — add workflow, add reference, add template, add script, or upgrade to router — the repository path of the skill surface the block produces, the Change's issue URL, and the sentences `Add the plugin changelog entry that records the change.` and `Launch no audit or review; the Executor launches the Verifier.`; the intent keeps `instructions:create-skill` from asking its intake menu, the first sentence makes the round that produces the surface produce its changelog entry, and the second keeps the skill's own audit step out of the round.
- `{{! subagent_name('spec-tree', 'change-subagent-author') !}}` Author: the repository path of the subagent definition the block produces, the Change's issue URL, and the sentences `Add the plugin changelog entry that records the change.` and `Launch no audit or review; the Executor launches the Verifier.`, so the round that produces the definition produces its changelog entry and launches no Verifier.
- Every other definition's Author: the block's Node or record in the form its fronted skill accepts.
- Fixer for a rejected audit run: exactly two inputs — the rejected run's sealed run file, unchanged, taken from the launch's result, and the instruction `attend to every rule the run names and sweep each named class across the whole target`. The Executor adds no summary, remedy, class name, or other interpretation of the findings.
- Fixer where a deterministic command failed and no auditor ran: a repair block holding the exact command line and output of every deterministic command that failed on the committed head the round before it produced.
- Fixer where a `/merge` review sealed no run: a repair block holding the verbatim finding that names the round's file.
- Every Fixer's fronted skill reads that run file or block as its repair input, except `instructions:create-subagent`, which declares no repair-input intake.

A round whose fronted skill is not installed returns a `blocked` result naming that skill.

Each Verifier is the configured auditor or reviewer that the `merge_composition` selects for a block, launched with a target-only task message: the decision-record audit for a Governance mutations block's record at any malleability, and for a Spec mutations block the evidence audits and audits that its Node's malleability after and the tags of its assertions select. The Executor launches every Verifier the composition selects for a block after the round whose subject it judges returns; a round session launches none. A `change-verifier` session produces verification routing and evidence through `/verify` and is an Author or Fixer, never a Verifier; its result is no verdict. The Verifier of a `{{! subagent_name('spec-tree', 'change-skill-author') !}}` round is `{{! subagent_name('instructions', 'skill-auditor') !}}`, and the Verifier of a `{{! subagent_name('spec-tree', 'change-subagent-author') !}}` round is `{{! subagent_name('instructions', 'subagent-auditor') !}}`:

| Subject the obligation names                            | Verifier                                                            |
| ------------------------------------------------------- | ------------------------------------------------------------------- |
| A PDR                                                   | `{{! subagent_name('spec-tree', 'pdr-auditor') !}}`                 |
| An ADR                                                  | `{{! subagent_name('spec-tree', 'adr-auditor') !}}`                 |
| A node's test evidence                                  | `{{! subagent_name('spec-tree', 'test-evidence-auditor') !}}`       |
| A node's eval evidence                                  | `{{! subagent_name('spec-tree', 'eval-evidence-auditor') !}}`       |
| An evidence obligation on a node's `[audit]` assertions | `{{! subagent_name('spec-tree', 'assertion-auditor') !}}`           |
| A skill surface                                         | `{{! subagent_name('instructions', 'skill-auditor') !}}`            |
| A subagent definition                                   | `{{! subagent_name('instructions', 'subagent-auditor') !}}`         |
| The changeset, under `/merge`                           | `{{! subagent_name('spec-tree', 'changes-reviewer') !}}`            |
| Changeset coherence, under `/merge`                     | `{{! subagent_name('spec-tree', 'changeset-coherence-auditor') !}}` |

A gate is one Verifier definition judging one subject; under `/merge`, the local review and the CI review are two gates. The Executor launches each gate at most twice per Change, counting real rejections:

- A rejection counts when at least one blocking or debt finding sits on a line the changeset changed, or is caused by its edit, read from the diff against the base, and a complete `BLOCKED` diagnostic from an audit gate counts as a rejection with no finding to read. A filed finding, a stale finding, and a finding on untouched text count for nothing; a launch that seals no run counts for nothing.
- The count holds every counted rejection from any session, a Fixer round's and those of the reviewers and auditors `/merge` launches among them. It is the run tokens the newest Handoff's `Hazards` line names plus this session's own counted rejections, and only launches after the newest published revision of the Change's body count.
- A third launch of a gate on the Change is refused with the count, and no gate is repeated until it approves.
- The cap covers agentic gates only. A deterministic command that fails runs again after its Fixer round outside the cap.

</definitions>

<audit_run_verdict>

Each launch of `{{! subagent_name('spec-tree', 'adr-auditor') !}}`, `{{! subagent_name('spec-tree', 'pdr-auditor') !}}`, `{{! subagent_name('spec-tree', 'spec-auditor') !}}`, `{{! subagent_name('spec-tree', 'test-evidence-auditor') !}}`, `{{! subagent_name('spec-tree', 'eval-evidence-auditor') !}}`, `{{! subagent_name('spec-tree', 'changeset-coherence-auditor') !}}`, `{{! subagent_name('spec-tree', 'implementation-auditor') !}}`, `{{! subagent_name('spec-tree', 'assertion-auditor') !}}`, `{{! subagent_name('instructions', 'skill-auditor') !}}`, and `{{! subagent_name('instructions', 'subagent-auditor') !}}` seals its verdict as one `spx verification run`. Its result names the run token, the run file, and the rendered projection. Read the verdict from the terminal status of the sealed run whose token the launch returns, and take the run file from the launch's result:

- `approved` approves.
- `rejected` rejects whatever the finding count; a required unit left uncovered rejects with no finding.
- A launch whose run `spx` refused a payload or the finish of is blocked: it yields no verdict and goes to step 8 with its complete diagnostic.
- A verdict read from a verdict object outside the run, a transcript, a task-output file, or text parsed into a scratch file is an unusable result under `<launch_contract>`.

</audit_run_verdict>

<launch_contract>

Each round or Verifier step requests exactly one native launch with its exact configured name and the task message `<definitions>` gives it. Use the native tool schema and result-collection capabilities, and collect each launch in the foreground. A failed launch or an unusable final result stops execution: record the exact failure, launch no substitute, and release the Change under step 8.

Start every Verifier without this conversation's history, reasoning, summaries, or a suggested verdict. While the native capability reports a launch still running, collect that same invocation; an observation timeout never authorizes a new launch.

</launch_contract>

{!% if target == 'codex' %!}
<codex_surface>

The plugin ships the round definitions this skill launches for Claude Code only. On this surface the skill runs none of its steps: it returns result `unavailable` with the Change reference and this reason, and writes nothing.

</codex_surface>
{!% endif %!}

<workflow>

1. **Resolve the Change.** Resolve the store and Product under `store-binding`. Read `$ARGUMENTS` as an issue reference — `#N`, `owner/repo#N`, or an issue URL — or, when empty, the newest `<CLAIMED_CHANGE>` marker in the conversation; neither present stops with result `not-held` naming the missing reference, and an `owner/repo` that differs from the overlay store stops with result `not-held` naming it. Read the issue, its `url`, its comments, and its fields under `canonical-state`.
2. **Confirm the claim.** Resolve this session's assigned worktree root with `git rev-parse --show-toplevel`. Require the issue `OPEN`, Lifecycle `Claimed`, Maturity `Executable`, a Leaf by the type `change-type` derives from the body's `## Governance mutations` and `## Spec mutations` blocks and the store's `Parent` values, and the claim root of the winning Claim under `claim-record` equal to that root. Run `spx worktree status` from the root and require this session's running claim for it. A Parent, or a root that carries neither block, is refused with result `not-held` naming its type, and any other state stops with result `not-held` and the observed values, with nothing written.
3. **Confirm execution may start.** Read this Change's predecessors from its `Predecessors` field and its blockers under `canonical-state`, and for every blocker closed `Abandoned` the Change whose `Predecessors` value names that blocker, found by the store-wide absorber lookup `canonical-state` states. Require every predecessor closed, and every blocker resolved under `blockers`: closed `Applied`, or closed `Abandoned` and absorbed by a Change that has closed `Applied`. A blocker closed `Abandoned` that no Change absorbed returns the Change to refinement and goes to step 8. An unmet condition goes to step 8 with the condition as the blocker.
4. **Bring the work into this worktree.** Read the newest `Handoff:` comment. When its `Branch or PR` line holds a branch or a pull request, followed by `@` and the full head commit SHA, take the text before `@` as the branch or pull request and resolve the branch — a pull request's with `gh pr view <url> --json headRefName` — then `git fetch origin <branch>` and `git switch <branch>`. When no Handoff exists or the line is `none`, take the branch the record names and create it with `git switch -c <branch> origin/<default>`, where `<default>` is `git rev-parse --abbrev-ref origin/HEAD` with its leading `origin/` removed. When neither the Handoff nor the record names a branch, read the checked-out branch with `git rev-parse --abbrev-ref HEAD` and work on it only when it is neither `HEAD` nor `<default>` and its name ends with the Change number `<N>` with no digit before it, as `work/change-<N>` and `executor-<N>` do, because a stale branch an interrupted release left in the worktree must not be adopted for an unrelated Change. Otherwise the worktree counts as naming no branch: on a detached checkout, the default branch, or a branch whose name does not end with `<N>`, create `work/change-<N>` from the Change's number with `git switch -c work/change-<N> origin/<default>`. A named branch always wins over the worktree's branch, and the Handoff's wins over the record's. Use skill `spec-tree:sync-base`. When the newest Handoff's `Branch or PR` line names a merged pull request and its `Next block` line is `none`, go to step 7. Continue from the Handoff's `Next block` line, or from the first `## Governance mutations` block, or the first `## Spec mutations` block when the record has none, when no Handoff exists.
5. **Take the `## Governance mutations` blocks, then the `## Spec mutations` blocks, each in record order** as one or more rounds:
   1. Select the definition from `<definitions>` by the content the block produces and the `merge_composition`: a Governance block selects `change-author`; a Spec block selects `change-author` for the Node's spec, `change-verifier` or `change-tester` by the tag of each assertion and the malleability after, and the definition fronting the Node's implementation when the malleability after is `implementation`; content no definition fronts goes to step 8 with that content as the blocker. A result that is a Verifier's verdict goes to step 5.3 with the committed subject.
   2. Launch one Author session of that definition under `<launch_contract>`. When it returns, run `git status --short`. Use skill `spec-tree:commit-changes`. Commit every uncommitted change the session left, recording the verification state. A `blocked` result goes to step 8 with its reason, and with its question verbatim when it carries one.
   3. Use skill `spec-tree:sync-base`. Run the product's `verify` command — the one the product's root agent guide names among its Spec Tree phase commands — over the block's Node and the changeset on the resulting head; a guide that names no `verify` command goes to step 8 with that gap as the blocker. A failing command starts a Fixer round under step 5.5 with that command as its reference. When every command passes, launch each Verifier the `merge_composition` selects for the block, and for a skill-surface or subagent-definition round the Verifier `<definitions>` pairs with its definition, one launch each, against that same head; a Verifier both name is launched once. Read each auditor's verdict under `<audit_run_verdict>`. A gate that already holds two counted rejections on the Change is not launched: the launch is refused with its count and goes to step 8.
   4. The block is complete when every Verifier the composition selects for it approves the head step 5.3 verified. The record receives no write. Record the progress in a Handoff: push the work branch, then post one Handoff comment in the `handoff-record` shape, with the file-payload and `inert-stdin` handling of `lifecycle.md`, and leave the Change Claimed with its Claim in force. Its `Branch or PR` line is the pushed branch followed by `@` and the full head commit SHA that `git rev-parse HEAD` prints, its `Completed blocks` line is the blocks the newest earlier Handoff lists plus the block just completed, each block named by its path with no run token, a Governance mutations block listed only because its decision-record audit run sealed `approved`, and its `Next block` line is the first uncompleted block. A Handoff that cannot be pushed or posted goes to step 8 with the exact failure.
   5. When a run is sealed `rejected` or a deterministic command fails, apply the gate cap `<definitions>` states. A rejection that is its gate's second counted rejection on the Change goes to step 8 with both rejections named by gate and, where the gate seals a run, run token, and a deterministic command that fails again after a Fixer round for it goes to step 8 with the command and both results. Otherwise launch one Fixer session under `<launch_contract>` with the message the Fixer entry of `<definitions>` gives: the rejected run's run file and the fixed instruction for a rejected audit run, the earliest in launch order when several rejected. When it returns, commit what it left as step 5.2 does and continue at step 5.3 for the new committed head.
6. **Integrate.** When every block is complete, integrate the changeset. Use skill `spec-tree:merge`. `/merge` launches its own reviewers and auditors, each one a Verifier `<definitions>` names, and each rejection they return counts toward its gate's cap. A valid finding a `/merge` review or audit raises is never repaired in this session: it goes to step 5.5, which releases the Change at its gate's second counted rejection and otherwise starts a Fixer round of the definition whose round produced the file the finding names, handed the rejected `/merge` audit run's run file or, where a `/merge` review sealed no run, the verbatim finding; `/merge` then continues on the new committed head. A gate that `/merge` reports blocked goes to step 8 with its exact report. When `/merge` reports the changeset merged, post one Handoff in the `handoff-record` shape as step 5.4 does, leaving the Change Claimed: its `Branch or PR` line is the merged pull request followed by `@` and its merge commit, its `Completed blocks` line lists every block by its path with no run token, and its `Next block` line is `none`.
7. **Close.** Use skill `spec-tree:close-change`. Close the Change with `Applied` and the Change reference; the skill reads the merge commit and the completed-blocks line from the newest Handoff, which step 6 posted. A close it refuses goes to step 8 with its exact report; a completed close returns result `closed`.
8. **Release.** When execution stops with continuation remaining — a blocker, a failed launch or unusable result, a gate's second counted rejection or a refused third launch, a deterministic command that failed again after its Fixer round, a blocked gate, or a question that reopens product or architecture judgment — state in the conversation the stop condition and the gate of every counted rejection and the run token of each that sealed one on the Change. Use skill `spec-tree:release-change`. Release the Change by its reference. The Handoff's `Completed blocks` line names the blocks the newest earlier Handoff lists plus the blocks this session completed under step 5.4, each by its path with no run token, and its `Next block` line names the first block not listed. The Handoff's `Hazards` line carries what the conversation states, so the next Executor's count starts from those tokens; the Handoff carries the question verbatim under `Blockers` when one exists. Return result `released` once `/release-change` reports the Change released; a release it refuses returns result `release-refused` with its exact report and the stop condition.

</workflow>

<constraints>

- NEVER write, edit, or delete a product artifact in this session — the launched sessions produce every artifact; this session commits, runs deterministic commands, integrates, and records Lifecycle.
- NEVER run an audit or review skill in this session; every verdict comes from a launched Verifier.
- NEVER launch a definition `<definitions>` does not name, and never launch one under another name.
- NEVER execute a Parent or a root that carries neither a Governance mutations nor a Spec mutations block; step 2 refuses it.
- NEVER settle a question the Change's Frame leaves open; step 8 carries it to the Handoff.

</constraints>

<failure_modes>

**A `/merge` finding was repaired in the Executor session.** Claude edited the file a valid `/merge` review finding named, which the first constraint forbids, so the merge gate could not pass within the Executor's own limits. Start a Fixer round of the definition whose round produced the file, handed the rejected run's run file or, where the review sealed no run, the verbatim finding (step 6).

**A refused release was reported as released.** Claude returned `released` for a Change still `Claimed` after `/release-change` refused. Return `release-refused` with the exact report whenever the release is refused (step 8).

</failure_modes>

<output_format>

Return the result — `closed`, `released`, `release-refused`, `not-held`, or `unavailable` — the Change URL, the final full head SHA, each round's definition, target, and verdict run tokens, the merge commit when integration happened, and the URL of the newest Handoff comment this session posted.

</output_format>

<success_criteria>

- Execution began only after the store showed this session's worktree holding the Executable Leaf, with every predecessor closed and every blocker resolved.
- Every artifact came from a launched session of the definition the block's content required, and every Fixer was a fresh session of the same definition, handed only the input its entry in `<definitions>` names.
- Every auditor verdict is the terminal status of a sealed run, and every verdict came from a configured Verifier launched once with a target-only task message on a committed head that passed the product's `verify` command.
- A `closed` result follows a completed `/close-change`, never a merge alone; a `released` result names the gate and run token of every counted rejection, and the completed and next blocks; `release-refused`, `not-held`, and `unavailable` carry the exact report or observed values with nothing written.
- No load-gated command was still running when the result was reported.

</success_criteria>
