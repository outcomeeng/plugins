---
name: execute-change
description: >-
  ALWAYS invoke this skill when a session executes one claimed Executable Change as its Executor. NEVER run a Change's Activities without this skill.
argument-hint: "[#N | owner/repo#N | issue-url]"
allowed-tools: Read, Glob, Grep, collaboration.spawn_agent, collaboration.wait_agent, Bash(git status:*), Bash(git rev-parse:*), Bash(git log:*), Bash(git fetch:*), Bash(git switch:*), Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh pr view:*), Bash(gh project view:*), Bash(gh project field-list:*), Bash(gh project item-list:*), Bash(spx worktree status:*)
---

<objective>
One claimed Executable Change carried to its end in this session: every Activity's result produced by configured subagent sessions and judged by configured Verifiers, the changeset integrated into the default branch, and the Change closed as `Applied`, or released with a Handoff that names why execution stopped.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; its rules govern every store read below by their `id`.

Use skill `spec-tree:wait-for-load` for every resource-intensive command any step below runs: run the waiter and that command as one line in the foreground, and report a result only after every such line has exited.

</required_reading>

<definitions>

Each round's producing session is one subagent of the definition that fronts the skill the Activity's result needs:

| Result the Activity names                                        | Definition                     | Skill it fronts     |
| ---------------------------------------------------------------- | ------------------------------ | ------------------- |
| A decision, spec, node, note, or other artifact `/author` writes | `spec-tree_change-author`      | `/author`           |
| Verification selection for a node's or decision's claims         | `spec-tree_change-verifier`    | `/verify`           |
| Test evidence for assertions routed to test                      | `spec-tree_change-tester`      | `/test`             |
| Implementation of a node in its language                         | `spec-tree_change-implementer` | `/implement-change` |

A Fixer is a fresh session of the definition the round's Author used. The task message of an Author session is the Activity's target in the form its fronted skill accepts: the canonical `spx/...` path of the node or decision it produces, which the `change-author` task message follows with the Change's issue reference, because `/author` reads the Output's requirements from the Change. The task message of a Fixer session is its Author's task message followed by a repair block: the verbatim result of every rejected verdict of the earlier round, and the exact command line and output of every deterministic command that failed on it. The fronted skill reads that block as its repair input.

Each Verifier is the configured auditor or reviewer for the evidence obligation the Change's Frame states, launched with a target-only task message:

| Subject the obligation names        | Verifier                           |
| ----------------------------------- | ---------------------------------- |
| A PDR                               | `spec-tree_pdr-auditor`            |
| An ADR                              | `spec-tree_adr-auditor`            |
| A node spec                         | `spec-tree_spec-auditor`           |
| A node's test evidence              | `spec-tree_test-evidence-auditor`  |
| A node's eval evidence              | `spec-tree_eval-evidence-auditor`  |
| Implementation in a changeset scope | `spec-tree_implementation-auditor` |
| A skill surface                     | `instructions_skill-auditor`       |
| A subagent definition               | `instructions_subagent-auditor`    |
| A Change record                     | `spec-tree_change-auditor`         |

</definitions>

<launch_contract>

Each round or Verifier step requests exactly one native launch with its exact configured name and the task message `<definitions>` gives it. Use the native tool schema and result-collection capabilities, and collect each launch in the foreground. A failed launch or an unusable final result stops execution: record the exact failure, launch no substitute, and release the Change under step 8.

Start every Verifier without this conversation's history, reasoning, summaries, or a suggested verdict. While the native capability reports a launch still running, collect that same invocation; an observation timeout never authorizes a new launch.

</launch_contract>

<workflow>

1. **Resolve the Change.** Read `$ARGUMENTS` as an issue reference — `#N`, `owner/repo#N`, or an issue URL — or, when empty, the newest `<CLAIMED_CHANGE>` marker in the conversation; neither present stops with result `not-held` naming the missing reference. Read the issue, its comments, and its single project item under `canonical-state`.
2. **Confirm the claim.** Resolve this session's assigned worktree root with `git rev-parse --show-toplevel`. Require the issue `OPEN`, Status `Claimed`, Maturity `Executable`, and the claim root of the winning Claim under `claim-record` equal to that root. Run `spx worktree status` from the root and require this session's running claim for it. Any other state stops with result `not-held` and the observed values, with nothing written.
3. **Confirm execution may start.** Require every Change in `refined_from` to have Lifecycle `Refined`, and every Change in `blocked_by` to have its current lineage leaves at `Applied`, following each blocker's successors — the Changes whose `refined_from` names it, found with `gh issue list --repo <store> --search "<blocker reference> in:body" --state all`. Require that no Change in the store names this Change in its `refined_from`. An unmet condition goes to step 8 with the condition as the blocker.
4. **Bring the work into this worktree.** Read the newest `Handoff:` comment. When its `Branch or PR` line names a branch or a pull request, resolve the branch — a pull request's with `gh pr view <url> --json headRefName` — then `git fetch origin <branch>` and `git switch <branch>`. When no Handoff exists or the line is `none`, resolve the default branch from `git rev-parse --abbrev-ref origin/HEAD` with its leading `origin/` removed, and create the working branch the Change's Activities name with `git switch -c <branch> origin/<default>`. Use skill `spec-tree:sync-base` afterwards. Continue from the Handoff's next Activity, or from the first unchecked Activity when no Handoff exists.
5. **Run each Activity in order** as one or more rounds:
   1. Select the definition from `<definitions>` by the result the Activity names. An Activity whose result is a Verifier's verdict goes to step 5.3 with the committed subject. An Activity whose result is integration goes to step 6, and an Activity whose result is closing goes to step 7.
   2. Launch one Author session of that definition under `<launch_contract>`. When it returns, run `git status --short`; use skill `spec-tree:commit-changes` for every uncommitted change the session left, recording the verification state. A `blocked` result goes to step 8 with its reason, and with its question verbatim when it carries one.
   3. Use skill `spec-tree:sync-base`, then run the deterministic commands the Change's Frame names for the Activity's nodes on the resulting head. A failing command starts a Fixer round under step 5.5 with that command as its reference. When every command passes, launch each Verifier the Frame's evidence obligations name for the Activity's subject, one launch each, against that same head.
   4. The Activity is complete when every Verifier it names approves the head step 5.3 verified.
   5. When a verdict rejects or a deterministic command fails, launch one Fixer session under `<definitions>`, its repair block carrying every rejected verdict and failed command of the round; when it returns, commit what it left as step 5.2 does and continue at step 5.3 for the new committed head. A rejection whose defect class a prior round of the same subject already raised, or a deterministic command that fails again after a Fixer round for it, goes to step 8 with the repeated class or command and both results.
6. **Integrate.** When every Activity before integration is complete, use skill `spec-tree:author-change` to check those Activities in the record, then use skill `spec-tree:merge` for the changeset. A gate that `/merge` reports blocked goes to step 8 with its exact report.
7. **Close.** Use skill `spec-tree:close-change` with `Applied` and the Change reference, and return result `closed`.
8. **Release.** When execution stops with continuation remaining — a blocker, a failed launch or unusable result, a repeated defect class, a blocked gate, or a question that reopens product or architecture judgment — use skill `spec-tree:release-change` with the Change reference. The Handoff names the stop condition, the verdict run tokens, and the question verbatim when one exists. Return result `released`.

</workflow>

<constraints>

- NEVER write, edit, or delete a product artifact in this session — the launched sessions produce every artifact; this session commits, runs deterministic commands, integrates, and records Lifecycle.
- NEVER run an audit or review skill in this session; every verdict comes from a launched Verifier.
- NEVER launch a definition `<definitions>` does not name, and never launch one under another name.
- NEVER settle a question the Change's Frame leaves open; step 8 carries it to the Handoff.

</constraints>

<output_format>

Return the result — `closed`, `released`, or `not-held` — the Change URL, the final full head SHA, each round's definition, target, and verdict run tokens, the merge commit when integration happened, and the Handoff comment URL when the Change was released.

</output_format>

<success_criteria>

- Execution began only after the store showed this session's worktree holding the Executable Change, with its predecessors `Refined` and its blockers' leaves `Applied`.
- Every artifact came from a launched session of the definition the Activity's result required, and every Fixer was a fresh session of the same definition.
- Every verdict came from a configured Verifier launched once with a target-only task message on a committed head that passed the Frame's deterministic commands.
- The Change ended `Applied` through `/close-change`, or `Available` with a Handoff naming the stop condition through `/release-change`.
- No load-gated command was still running when the result was reported.

</success_criteria>
