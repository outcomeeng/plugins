---
name: apply-change
description: >-
  ALWAYS invoke this skill when a session applies one claimed Applicable Change as its Applier. NEVER apply a Change's Declarations subsections without this skill.
argument-hint: "<#N | owner/repo#N | issue-url>"
allowed-tools: Read, Write, Glob, Grep, Skill, Agent, Bash(git status:*), Bash(git rev-parse:*), Bash(git log:*), Bash(git fetch:*), Bash(git switch:*), Bash(git show:*), Bash(git cat-file:*), Bash(git ls-tree:*), Bash(git merge-base --is-ancestor:*), Bash(gh issue view:*), Bash(gh pr view:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(gh api repos/*/issues/*/dependencies/blocked_by --method GET -F per_page=100), Bash(spx worktree status:*), Bash(spx spec status:*)
---

<objective>
One claimed Applicable Leaf carried to its end: its Changeset on the default branch and the Change closed Applied, or the Change submitted or released with a Handoff that names why Application stopped.
</objective>

<required_reading>

Use skill `product-tree:change-standards`. Its rules govern every record read below by their slugs; read its `references/github-store.md` for every store read.

Use skill `product-tree:merging-standards`. Its merge composition derives each subsection's results and Verifiers from the Node's Malleability after the Change and from the verification type each Assertion's group heading names; the record names none.

Use skill `product-tree:wait-for-load` for every resource-intensive command a step below runs: run each one under that skill's lock line in the foreground, and report a result only after every such line has exited.

Use skill `product-tree:manage-change`. It makes every Transition the steps below name.

Use skill `product-tree:author-change`. It makes every record write the steps below name.

</required_reading>

<definitions>

Each round's producing session is one subagent of the definition that fronts the skill its content needs:

| Content the round produces                                                                       | Definition                            | Skill it fronts                 |
| ------------------------------------------------------------------------------------------------ | ------------------------------------- | ------------------------------- |
| A Decision Record, a spec, or another artifact `/author` writes                                  | `product-tree:change-author`          | `product-tree:author`           |
| Verification evidence for a Node's Assertions                                                    | `product-tree:change-verifier`        | `product-tree:verify`           |
| Tests for Assertions routed to test                                                              | `product-tree:change-tester`          | `product-tree:test`             |
| Implementation of a Node in its language                                                         | `product-tree:change-implementer`     | `product-tree:implement-change` |
| A skill surface: a `SKILL.md`, another file in a skill directory, or an authored shared fragment | `product-tree:change-skill-author`    | `instructions:author-skill`     |
| A subagent definition                                                                            | `product-tree:change-subagent-author` | `instructions:author-subagent`  |

Each Author's task message names the subsection by its heading path and the Change by its issue URL; a skill-surface or subagent-definition Author's message adds the repository path it produces and the sentences `Add the plugin changelog entry that records the change.` and `Launch no audit or review; the Applier launches the Verifier.`, so the round that produces a surface produces its changelog entry and launches no Verifier. A round whose fronted skill is not installed returns a `blocked` result naming that skill.

A Fixer is a fresh session of the definition its round's Author used. Its task message is exactly the rejected run's sealed run file, unchanged, followed by the instruction `attend to every rule the run names and sweep each named class across the whole target`. NEVER add a summary, a remedy, a class name, or any other reading of the findings to it. A Fixer for a deterministic command that failed receives that command line and its output verbatim, followed by the same instruction. A Fixer returns, for each repair, the clause it applies and the check that shows the class closed; the gate reads the next Verifier's verdict, never that check.

A mechanical repair is the one artifact the Applier produces itself: a fix of a finding that changes no behavior or decision — a path or link, a typo, a wording the finding states, or a renamed identifier — and never Decision Record text. The Applier makes it directly with no Fixer round, commits it, runs Validate and every Test and Evaluate result it invalidates again, and launches no Verifier for it; the next Verifier pass judges it. Every other repair goes to a Fixer.

Each Verifier is the configured auditor or reviewer the merge composition selects, launched with a target-only task message after the round whose subject it judges returns; a round launches none:

| Subject                                    | Verifier                                   |
| ------------------------------------------ | ------------------------------------------ |
| A PDR                                      | `product-tree:pdr-auditor`                 |
| An ADR                                     | `product-tree:adr-auditor`                 |
| A Node spec                                | `product-tree:spec-auditor`                |
| A Node's test evidence                     | `product-tree:test-evidence-auditor`       |
| A Node's eval evidence                     | `product-tree:eval-evidence-auditor`       |
| An evidence obligation on Audit Assertions | `product-tree:assertion-auditor`           |
| Implementation                             | `product-tree:implementation-auditor`      |
| A skill surface                            | `instructions:skill-auditor`               |
| A subagent definition                      | `instructions:subagent-auditor`            |
| Changeset coherence, under `/merge`        | `product-tree:changeset-coherence-auditor` |
| The changeset, under `/merge`              | `product-tree:changes-reviewer`            |

Read the verdict of every auditor launch from the sealed run whose token the launch returns, and take the run file from the launch's result: a `rejected` run rejects whatever its finding count, a launch whose run spx refused a payload or the finish of is blocked, and a verdict read from a verdict object outside the run, a transcript, a task-output file, or text parsed into a scratch file is an unusable result.

A gate is one Verifier definition judging one subject. Launch each gate at most twice per Change:

- A rejection counts when a `blocking` finding, or a `debt` finding an audit raises, sits on a line the changeset changed or is caused by its edit, and a complete `BLOCKED` diagnostic from an audit gate counts as a rejection with no finding to read. A `debt` finding a review raises, a filed finding, a stale finding, a finding on untouched text, and a launch that seals no run count for nothing, and a published revision of the record's body restarts the count.
- The count holds every counted rejection from any session, those of Fixer rounds and of the reviewers and auditors `/merge` launches among them: the run tokens the newest Handoff's `hazards` names plus this session's own. A rejection the Operator overrides counts for nothing; read the override only from the verification run that names its actor, the subject commit, the artifacts judged, and the verdict set aside, never from a message or a comment. No override applies to a Deterministic result.
- A third launch of a gate on the Change is refused with the count, and no gate repeats until it approves. The cap covers agentic gates only: a deterministic command that fails runs again after its Fixer round, and one that fails again after that round releases the Change.

</definitions>

<launch_contract>

Each round or Verifier step requests exactly one native launch with its exact configured name and the task message `<definitions>` gives it, collected in the foreground. A failed launch or an unusable result stops Application: record the exact failure, launch no substitute, and release under step 9. Start every Verifier without this conversation's history, reasoning, summaries, or a suggested verdict.

</launch_contract>

<application_check>

Run every check against the current default branch plus the effects of the Change's earlier subsections, in record order:

- The Base resolves to a commit.
- A `+` slug with no `-` partner is absent from its file; a `+` heading with no `-` partner is absent, and a `-` heading is present.
- A file a `new file` header creates is absent from the default branch; in an edited contract file, Outcome record, or Product spec, each `-` line and context line reads on the default branch as at the Base.
- A file or Node a `deleted file` header names is present and reads as the Base holds it; a deleted Node's branch holds exactly the Nodes, Decision Records, contract files, and Outcome records it holds at the Base, each reading as the Base holds it.
- A file or Node a move names is present at its `rename from` path and absent at its `rename to` path, and reads as the Base holds it; a moved Node's branch passes the deleted-Node test.
- A replaced file reads on the default branch as the Base holds it.
- The current record is the one the audit judged, and, where the Operator's review binds an operation, the one the Operator reviewed or one that review carries forward to under `review-carry`.
- A `-` slug, alone or first in a replace, is present.
- The Malleability of each Node at the Base reads the same on the default branch.
- Each Node an infrastructure line names stands on the default branch with State Passing, or a blocking Change builds it.
- Each slug or opening line a `-` line names, and each context line, reads the same at the Base as on the default branch.

</application_check>

<workflow>

1. **Resolve the Change.** Take `$ARGUMENTS` as `#N`, `owner/repo#N`, or an issue URL; any other form, or none, returns `not-held` naming the three. Resolve the store under `<store_binding>` and read the issue, its fields, its comments, and its blockers under `<reads>`.
2. **Confirm the Claim.** Require the issue open, Lifecycle Available, Maturity Applicable, the current login its one assignee, and the newest `claim` comment's `worktree` equal to `git rev-parse --show-toplevel`. Run `spx worktree status` and require this session's running claim. Derive the type under `change-type`; refuse a Parent with `not-held` naming its type. Load the newest `release` comment's `handoff` as the latest Handoff. Any other state returns `not-held` with the observed values and writes nothing.
3. **Confirm the blockers.** Require every blocker closed Applied under `blocker-applied`, or closed Abandoned through a merge with the Change that absorbed it closed Applied under `blocker-abandoned`. A blocker not yet delivered keeps the Maturity: go to step 9 with the blocker named. A blocker closed Abandoned without a merge returns the Change to Refinement: go to step 9.
4. **Bring the work branch.** A branch the newest Handoff names stays the working branch: `git fetch origin <branch>` and `git switch <branch>`. When the Handoff names none, work on the checked-out branch only when it is not the default branch and its name ends with the Change number `<N>` with no digit before it, as `work/change-<N>` and `applier-<N>` do and `work/change-1<N>` does not; otherwise create `work/change-<N>` with `git switch -c work/change-<N> origin/<default>`. Then use skill `product-tree:sync-base`. When the Handoff names a merged Changeset and `next` is `none`, go to step 8.
5. **Run the Application check** of `<application_check>` before the first subsection. A failed check returns the Change to Sliced: make `lower Sliced` through `product-tree:manage-change` with the failed check as its reason, start no subsection, and go to step 9.
6. **Take the Declarations subsections in record order**, from the Handoff's `next`, or the first subsection when no Handoff names one:
   1. Derive the subsection's results and Verifiers from the merge composition for the Node's Malleability after the Change and the verification type of each Assertion's group heading, and select each round's definition from `<definitions>`. A subsection whose Node's result is a skill surface runs as a skill-surface round judged by the skill auditor, and one whose result is a subagent definition as a subagent-definition round judged by the subagent auditor.
   2. Launch one Author session under `<launch_contract>`. When it returns, run `git status --short` and use skill `product-tree:commit-changes` for every change it left. A `blocked` result goes to step 9 with its reason, and with its question verbatim when it carries one.
   3. Use skill `product-tree:sync-base`, then run the product's `verify` command, the one its root agent guide names among its Product Tree phase commands, over the subsection's Node and the changeset. A failing command starts a Fixer round under step 6.5. When every command passes, launch each Verifier the composition selects, one launch each, against that head.
   4. The subsection is complete when every Verifier it selects approves the verified head. Record the progress in the harness's own task list; the record receives no write.
   5. When a verdict rejects or a deterministic command fails, apply the gate cap. A mechanical repair is made under `<definitions>` with no Fixer round. A gate's second counted rejection, or a deterministic command that fails again after its Fixer round, goes to step 9 with both results named by gate and run token. Otherwise launch one Fixer and continue at step 6.3 on its committed head.
   6. When a subsection needs a decision line that differs from the reviewed line, make `lower Sliced` through `product-tree:manage-change` with that reason, write the new line through `product-tree:author-change`, keep the Claim, and make `submit` for the Operator's review; return `submitted`. When a round or check reopens a product or architecture judgment, write the question into the Change through `product-tree:author-change` and make `submit` with the question as its reason; return `submitted`, and once the Operator lowers the Change, release it under step 9.
7. **Integrate.** When every subsection is complete, use skill `product-tree:merge` for the changeset. Each rejection its reviewers and auditors return counts toward its gate's cap. Repair a valid finding in this session only as a mechanical repair; start a Fixer round of the definition whose round produced the file for every other repair, and go to step 9 for a finding on a file no round of this session produced. Pass each new `debt` finding a review raises on text the changeset touches or invalidates up the chain of positions for its ruling, and act on it only as the ruling directs.
8. **Close.** Make `applied` through `product-tree:manage-change`; it checks `leaf-applied` and the audit at close. A refused close goes to step 9 with its report; a completed close returns `closed`.
9. **Release.** When Application stops with continuation remaining, make `release` through `product-tree:manage-change` with a Handoff whose `completed` lists every subsection the newest earlier Handoff lists plus those this session completed, whose `next` names the first one not listed, whose `blockers` carry each question verbatim, and whose `hazards` name every counted rejection by gate and run token. Return `released`, or `release-refused` with the exact report when the release is refused.

</workflow>

<constraints>

- NEVER write, edit, or delete a product artifact in this session other than by a mechanical repair; the launched sessions produce every other artifact.
- NEVER write the Change record except to make a Transition, to lower an Applicable Change to Sliced and write a changed decision line, or to write a reopened judgment's question and submit the Change.
- NEVER run an audit or review skill in this session; every verdict comes from a launched Verifier.
- NEVER launch a definition `<definitions>` does not name.

</constraints>

<failure_modes>

**A `/merge` finding was repaired in the Applier session.** Claude held the finding and the file it named in one session, took the repair for a small edit the Applier could make directly although it changed behavior, and edited the file. Only a mechanical repair is made directly; start a Fixer round of the definition whose round produced the file.

**A refused release was reported as released.** Claude returned `released` for a Change whose release the Transition refused, because it took the invocation for the release. Return `release-refused` with the exact report whenever the release is refused.

</failure_modes>

<output_format>

Return the result — `closed`, `submitted`, `released`, `release-refused`, `not-held`, or `unavailable` — the Change URL, the final full head SHA, each round's definition, target, and verdict run tokens, the merge commit when integration happened, and the newest Transition comment this session posted.

</output_format>

<success_criteria>

- Application began only on an Applicable Leaf this session's worktree held, with every blocker resolved and the Application check passed.
- Every artifact other than a mechanical repair came from a launched session of the definition its content required, and every Fixer received exactly the sealed run file and the fixed instruction.
- Every verdict came from a configured Verifier launched once on a committed head that passed the product's `verify` command, read from its sealed run.
- No load-gated command was still running when the result was reported.

</success_criteria>
