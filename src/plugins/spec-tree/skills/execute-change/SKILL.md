---
name: execute-change
description: >-
  ALWAYS invoke this skill when a session executes one claimed Executable Change as its Executor. NEVER run a Change's Activities without this skill.
argument-hint: "[#N | owner/repo#N | issue-url]"
allowed-tools: Read{!% if target == 'claude' %!}, Glob, Grep, {{! tool('use_skill') !}}, Agent, Bash(git status:*), Bash(git rev-parse:*), Bash(git log:*), Bash(git fetch:*), Bash(git switch:*), Bash(gh issue view:*), Bash(gh pr view:*), Bash(gh api graphql:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by --method GET -F per_page=100), Bash(spx worktree status:*){!% endif %!}
---

<objective>
One claimed Executable Change carried to its end: its changeset on the default branch and the Change closed as `Applied`, or the Change released with a Handoff that names why execution stopped.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; its rules govern every store read below by their `id`.

Use skill `spec-tree:wait-for-load` for every resource-intensive command any step below runs: run the waiter and that command as one line in the foreground, and report a result only after every such line has exited.

</required_reading>

<definitions>

Each round's producing session is one subagent of the definition that fronts the skill the Activity's result needs:

| Result the Activity names                                                                        | Definition                                                     | Skill it fronts                |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- | ------------------------------ |
| A decision, spec, node, note, or other artifact `/author` writes                                 | `{{! subagent_name('spec-tree', 'change-author') !}}`          | `spec-tree:author`             |
| Verification selection for a node's or decision's claims                                         | `{{! subagent_name('spec-tree', 'change-verifier') !}}`        | `spec-tree:verify`             |
| Test evidence for assertions routed to test                                                      | `{{! subagent_name('spec-tree', 'change-tester') !}}`          | `spec-tree:test`               |
| Implementation of a node in its language                                                         | `{{! subagent_name('spec-tree', 'change-implementer') !}}`     | `spec-tree:implement-change`   |
| A skill surface: a `SKILL.md`, another file in a skill directory, or an authored shared fragment | `{{! subagent_name('spec-tree', 'change-skill-author') !}}`    | `instructions:create-skill`    |
| A subagent definition                                                                            | `{{! subagent_name('spec-tree', 'change-subagent-author') !}}` | `instructions:create-subagent` |

A Fixer is a fresh session of the definition the round's Author used. A Fixer whose subject no Author round of this session produced — a verdict-only Activity's subject, a file an earlier session's round produced before a Handoff, a file the base already carried, or a file `/merge` regenerated — takes the file the rejected finding or failed command names and is a fresh session of the definition the table above selects for the kind of result that file is, with that file's path as its Author's target; a file no row matches, or a rejection or failed command that names no file, goes to step 8 with that rejection or command as the blocker. The task message of each session follows its definition:

- `{{! subagent_name('spec-tree', 'change-author') !}}` Author: the canonical `spx/...` path of the node or decision it produces, followed by the Change's issue URL, because `/author` reads the Output's requirements from the Change.
- `{{! subagent_name('spec-tree', 'change-skill-author') !}}` Author: the `instructions:create-skill` intent the Activity names — create, improve, add workflow, add reference, add template, add script, or upgrade to router — the repository path of the skill surface the Activity produces, the Change's issue URL, and the sentence `Add the plugin changelog entry that records the change.`; the intent keeps `instructions:create-skill` from asking its intake menu, and the sentence makes the round that produces the surface produce its changelog entry.
- `{{! subagent_name('spec-tree', 'change-subagent-author') !}}` Author: the repository path of the subagent definition the Activity produces, the Change's issue URL, and the sentence `Add the plugin changelog entry that records the change.`, so the round that produces the definition produces its changelog entry.
- Every other definition's Author: the Activity's target in the form its fronted skill accepts.
- Fixer: its Author's task message followed by a repair block: the verbatim result of every rejected verdict of the earlier round, and the exact command line and output of every deterministic command that failed on it. The fronted skill reads that block as its repair input. `instructions:create-skill` and `instructions:create-subagent` declare no repair-block intake, so for a `{{! subagent_name('spec-tree', 'change-skill-author') !}}` or `{{! subagent_name('spec-tree', 'change-subagent-author') !}}` Fixer the block is the improvement the task message requests: the message names the `improve` intent in place of the Author's for a `{{! subagent_name('spec-tree', 'change-skill-author') !}}` round, because the Author's round already produced the target, and each rejected finding and failed command in the block is a requested improvement the fronted skill repairs together with the findings of the audit it dispatches itself.

A round whose fronted skill is not installed returns a `blocked` result naming that skill.

Each Verifier is the configured auditor or reviewer for the evidence obligation the Change's Frame states, launched with a target-only task message. A `{{! subagent_name('spec-tree', 'change-verifier') !}}` session produces verification routing and evidence through `/verify` and is an Author or Fixer, never a Verifier; its result is no verdict. The Verifier of a `{{! subagent_name('spec-tree', 'change-skill-author') !}}` round is `{{! subagent_name('instructions', 'skill-auditor') !}}`, and the Verifier of a `{{! subagent_name('spec-tree', 'change-subagent-author') !}}` round is `{{! subagent_name('instructions', 'subagent-auditor') !}}`:

| Subject the obligation names        | Verifier                                                            |
| ----------------------------------- | ------------------------------------------------------------------- |
| A PDR                               | `{{! subagent_name('spec-tree', 'pdr-auditor') !}}`                 |
| An ADR                              | `{{! subagent_name('spec-tree', 'adr-auditor') !}}`                 |
| A node spec                         | `{{! subagent_name('spec-tree', 'spec-auditor') !}}`                |
| A node's test evidence              | `{{! subagent_name('spec-tree', 'test-evidence-auditor') !}}`       |
| A node's eval evidence              | `{{! subagent_name('spec-tree', 'eval-evidence-auditor') !}}`       |
| A node's `[audit]` assertions       | `{{! subagent_name('spec-tree', 'assertion-auditor') !}}`           |
| Implementation in a changeset scope | `{{! subagent_name('spec-tree', 'implementation-auditor') !}}`      |
| A skill surface                     | `{{! subagent_name('instructions', 'skill-auditor') !}}`            |
| A subagent definition               | `{{! subagent_name('instructions', 'subagent-auditor') !}}`         |
| A Change record                     | `{{! subagent_name('spec-tree', 'change-auditor') !}}`              |
| The changeset, under `/merge`       | `{{! subagent_name('spec-tree', 'changes-reviewer') !}}`            |
| Changeset coherence, under `/merge` | `{{! subagent_name('spec-tree', 'changeset-coherence-auditor') !}}` |

A node spec's own declarations go to `{{! subagent_name('spec-tree', 'spec-auditor') !}}`; the results of its `[audit]` assertions go to `{{! subagent_name('spec-tree', 'assertion-auditor') !}}`, whose task message is the repository path of that node's spec.

The verdict of a `{{! subagent_name('instructions', 'skill-auditor') !}}`, `{{! subagent_name('instructions', 'subagent-auditor') !}}`, or `{{! subagent_name('spec-tree', 'assertion-auditor') !}}` launch is the terminal status of the sealed run whose token the launch returns: `approved` approves, and `rejected` rejects whatever the finding count. A launch that returns a blocked diagnostic — a run that never started, or a refused payload or finish — yields no verdict and goes to step 8 with that diagnostic.

</definitions>

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
2. **Confirm the claim.** Resolve this session's assigned worktree root with `git rev-parse --show-toplevel`. Require the issue `OPEN`, Lifecycle `Claimed`, Maturity `Executable`, and the claim root of the winning Claim under `claim-record` equal to that root. Run `spx worktree status` from the root and require this session's running claim for it. Any other state stops with result `not-held` and the observed values, with nothing written.
3. **Confirm execution may start.** Read this Change's predecessors from its `Predecessors` field, its blockers, and each Change's successors under `canonical-state`. Require every predecessor to have Lifecycle `Refined`, and every blocker to have its current lineage leaves at `Applied`, following each blocker's successors to its leaves. Require that this Change has no successor. An unmet condition goes to step 8 with the condition as the blocker.
4. **Bring the work into this worktree.** Read the newest `Handoff:` comment. When its `Branch or PR` line names a branch or a pull request, resolve the branch — a pull request's with `gh pr view <url> --json headRefName` — then `git fetch origin <branch>` and `git switch <branch>`. When no Handoff exists or the line is `none`, resolve the default branch from `git rev-parse --abbrev-ref origin/HEAD` with its leading `origin/` removed, and create the working branch the Change's Activities name with `git switch -c <branch> origin/<default>`; Activities that name no branch go to step 8 with that gap as the blocker. Use skill `spec-tree:sync-base` afterwards. Continue from the Handoff's next Activity, or from the first unchecked Activity when no Handoff exists.
5. **Run each Activity in order** as one or more rounds:
   1. Select the definition from `<definitions>` by the result the Activity names; a result no row matches goes to step 8 with that result as the blocker. An Activity whose result is a Verifier's verdict goes to step 5.3 with the committed subject. An Activity whose result is integration goes to step 6, and an Activity whose result is closing goes to step 7.
   2. Launch one Author session of that definition under `<launch_contract>`. When it returns, run `git status --short`; use skill `spec-tree:commit-changes` for every uncommitted change the session left, recording the verification state. A `blocked` result goes to step 8 with its reason, and with its question verbatim when it carries one.
   3. Use skill `spec-tree:sync-base`, then run the product's `verify` command — the one the product's root agent guide names among its Spec Tree phase commands — over the Activity's nodes and the changeset on the resulting head; a guide that names no `verify` command goes to step 8 with that gap as the blocker. A failing command starts a Fixer round under step 5.5 with that command as its reference. When every command passes, launch each Verifier the Frame's evidence obligations name for the Activity's subject, and for a skill-surface or subagent-definition round the Verifier `<definitions>` pairs with its definition, one launch each, against that same head; a Verifier both name is launched once.
   4. The Activity is complete when every Verifier it names approves the head step 5.3 verified.
   5. When a verdict rejects or a deterministic command fails, launch one Fixer session under `<definitions>`, its repair block carrying every rejected verdict and failed command of the round; when it returns, commit what it left as step 5.2 does, then continue at step 5.3 for the new committed head when the round belongs to an Activity, or return to `/merge` when step 6 started it. A rejection whose defect class a prior round of the same subject already raised — a finding carrying the same rule identifier, or the same category where the verdict names no rule, against the same file — or a deterministic command that fails again after a Fixer round for it, goes to step 8 with the repeated class or command and both results.
6. **Integrate.** When every Activity before integration is complete, use skill `spec-tree:author-change` to check those Activities in the record, then use skill `spec-tree:merge` for the changeset. `/merge` launches its own reviewers and auditors, each one a Verifier `<definitions>` names. A valid finding a `/merge` review or audit raises is never repaired in this session: it starts a Fixer round under step 5.5, whose definition `<definitions>` selects from the file the finding names, with the finding as its repair block; step 5.3 does not run for that round, because `/merge` re-runs its own verification and Verifiers when it continues on the new committed head. A gate that `/merge` reports blocked goes to step 8 with its exact report. When `/merge` reports the changeset merged, use skill `spec-tree:author-change` to check the integration Activity and every closing Activity, so every Activity in the record is checked before step 7.
7. **Close.** Use skill `spec-tree:close-change` with `Applied` and the Change reference. A close it refuses goes to step 8 with its exact report; a completed close returns result `closed`.
8. **Release.** When execution stops with continuation remaining — a blocker, a failed launch or unusable result, a repeated defect class, a blocked gate, or a question that reopens product or architecture judgment — use skill `spec-tree:release-change` with the Change reference. Its Handoff names the stop condition under `Hazards` and carries the question verbatim under `Blockers` when one exists; verdict run tokens stay in this skill's result, never in the Change. Return result `released` once `/release-change` reports the Change released; a release it refuses returns result `release-refused` with its exact report and the stop condition.

</workflow>

<constraints>

- NEVER write, edit, or delete a product artifact in this session — the launched sessions produce every artifact; this session commits, runs deterministic commands, integrates, and records Lifecycle.
- NEVER run an audit or review skill in this session; every verdict comes from a launched Verifier.
- NEVER launch a definition `<definitions>` does not name, and never launch one under another name.
- NEVER settle a question the Change's Frame leaves open; step 8 carries it to the Handoff.

</constraints>

<failure_modes>

**A `/merge` finding was repaired in the Executor session.** Claude edited the file a valid `/merge` review finding named, which the first constraint forbids, so the merge gate could not pass within the Executor's own limits. Start a Fixer round of the definition whose round produced the file, with the finding as its repair block (step 6).

**A refused release was reported as released.** Claude returned `released` for a Change still `Claimed` after `/release-change` refused. The result was written from the decision to release rather than from `/release-change`'s report, so the store and the result disagreed and the next holder found no Handoff. Return `release-refused` with the exact report whenever the release is refused (step 8).

</failure_modes>

<output_format>

Return the result — `closed`, `released`, `release-refused`, `not-held`, or `unavailable` — the Change URL, the final full head SHA, each round's definition, target, and verdict run tokens, the merge commit when integration happened, and the Handoff comment URL when the Change was released.

</output_format>

<success_criteria>

- Execution began only after the store showed this session's worktree holding the Executable Change, with its predecessors `Refined` and its blockers' leaves `Applied`.
- Every artifact came from a launched session of the definition the Activity's result required, and every Fixer was a fresh session of the same definition.
- Every verdict came from a configured Verifier launched once with a target-only task message on a committed head that passed the product's `verify` command.
- The Change ended `Applied` through `/close-change`, or `Available` with a Handoff naming the stop condition through `/release-change`.
- A `not-held` or `unavailable` result wrote nothing and names the missing reference or the observed values that stopped it; a `release-refused` result carries `/release-change`'s exact report and the stop condition.
- No load-gated command was still running when the result was reported.

</success_criteria>
