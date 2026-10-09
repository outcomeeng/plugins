# Issues: Change Execution

## The seven definitions ship for Claude Code only

**Evidence**: `/subagent-standards` requires each subagent definition without declared per-harness release acceptance to retain its exact-definition minimal isolated invocation, per `spx/43-instructions.enabler/21-subagents.enabler/subagents.md`. The build emits no Codex rendering of `change-executor`, `change-author`, `change-verifier`, `change-tester`, `change-implementer`, `change-skill-author` and `change-subagent-author`.

**Impact**: a Codex session cannot execute a Change: `/orchestrate-change` Start and `/execute-change` return an explicit unavailable result on Codex.

**Settlement condition**: a Codex Executor start exists, the seven definitions list Codex among their targets, and each Codex rendering retains its own minimal isolated invocation.

## The Executor's session start through `--agent` is unobserved

**Evidence**: `probes/definition-invocation/probe.md` launches each of the seven definitions as a child of one `Agent` call. `/orchestrate-change` starts the Executor another way: it starts a new Claude Code session in a herdr pane with `--agent` naming `change-executor` and `--disallowedTools` withholding the structured-question tool. No retained run shows a session started that way loading `change-executor`, preloading `/execute-change`, and running without the structured-question tool.

**Impact**: the Executor start is the one launch path every Change execution takes, and it is also the path the harness's classifier refused twice in orchestration sessions. A defect there, such as a definition that does not load as a main-session agent, surfaces only when the first Change is executed.

**Settlement condition**: a retained run in which a session started with `--agent` naming the emitted `change-executor` and the structured-question tool withheld reports that definition as its agent, lacks the structured-question tool, and returns a result `/execute-change` declares.

## The Executor's `gh api graphql` grant admits store mutations

**Evidence**: `instructions:skill-auditor` finding f-009, severity `WARNING`, against `src/plugins/spec-tree/skills/execute-change/SKILL.md:6`, in the typed skill audit of head `c4ed94bfc0c440a7d0f0a55c0a8b541a0d67de49`. The grant `Bash(gh api graphql:*)` admits issue-field mutations as well as the field and successor reads `canonical-state` requires, while the skill's first constraint limits its session to deterministic commands, integration, and Lifecycle recorded through the Lifecycle skills, which carry their own `gh api graphql` grants.

**Impact**: the Executor's approved surface can change store state outside `/claim-change`, `/release-change` and `/close-change`.

**Settlement condition**: the grant is narrowed to the read forms the Executor runs, and a retained invocation shows the harness admits those reads under the narrowed patterns without a prompt. The matcher's treatment of a pattern that is not a literal prefix of the issued command is the open question recorded in `spx/43-instructions.enabler/21-skills.enabler/ISSUES.md` under "A skill-directory token inside an `allowed-tools` pattern may never match".

## The Executor skill leaves three composed-command results unrouted

**Evidence**: `instructions:skill-auditor` findings f-009, f-010 and f-011, severity `WARNING`, against `src/plugins/spec-tree/skills/execute-change/SKILL.md` steps 4, 5.3 and 6 and its `allowed-tools`, in the typed skill audit of head `932fac2f46aa033536a4b8156a01f1fa3581f186`. Steps 4 and 5.3 invoke `spec-tree:sync-base` without naming the results that continue or routing every other result to step 8. Step 6 does not state which `/merge` result returns control or where a finding on a file no round produced goes. Step 5.3 runs the product's `verify` command and the `/wait-for-load` waiter, neither of which the Bash grants cover.

**Impact**: a failed base sync can precede verification on a stale head, and a `/merge` finding on a file no round produced is settled by judgment where the first constraint forbids this session to repair it. Each verify command asks for approval during autonomous execution.

**Settlement condition**: each composed skill's continuing results are named and every other result routes to step 8; step 6 names the `/merge` result that returns control and routes a finding with no producing round to step 8; the workflow states the approval model of the product's `verify` command or grants the narrowest pattern the waiter needs; one typed skill audit of `execute-change` then raises no `composed_result_unhandled`, `ambiguous_cross_skill_control_flow` or `allowed_tools_vs_workflow_commands` finding.

## The Executor skill's grants, verify scope and reading tag carry three open warnings

**Evidence**: `instructions:skill-auditor` findings f-008, f-010 and f-011, severity `WARNING`, against `src/plugins/spec-tree/skills/execute-change/SKILL.md`, in the typed skill audit of head `8b72c99fe5a258ef2d562e7e33e1151c909c0658`, which approved with no must-fix finding. The Codex render grants `spawn_agent` and `wait_agent` although its `<codex_surface>` runs no step. Step 5.3 runs the product `verify` command over the Activity's nodes and the changeset, and a skill-surface or subagent-definition round targets paths outside any spec node. `<required_reading>`, a workflow-file tag, holds the always-on composition directives of a non-router skill.

**Impact**: the Codex grant exceeds the behavior it serves, the verification scope for a round whose subject is no spec node depends on judgment, and the tag does not name its content.

**Settlement condition**: the Codex render grants only what its `unavailable` path needs, step 5.3 states the scope for a subject that is no spec node, and the always-on directives sit in a semantically named section; one typed skill audit of `execute-change` then raises no `narrowest_allowed_tools`, `ambiguous_instruction` on scope, or `tag_semantics` finding.

## An instruction round's changelog entry has no declared owner in the fronted skills

**Evidence**: `spec-tree:changes-reviewer` run `2026-10-03_21-00-54-163-94f69948f54e` on head `a5828b89d9470a14436c069f6884a556847610bc`, finding severity `DEBT`, category consistency, against `change-execution.md`. Neither `instructions:create-skill` nor `instructions:create-subagent` declares changelog authoring. The `/execute-change` task message carries the instruction as a sentence, and the 0.101.0 entry of the spec-tree changelog states that each round produces the entry that records its surface. A surface outside any plugin has no plugin changelog.

**Impact**: a round produces the changelog entry only as far as its fronted skill follows an instruction its declared scope does not name, and the Executor can neither detect nor fill the gap without producing an artifact itself.

**Settlement condition**: `instructions:create-skill` and `instructions:create-subagent` each declare a changelog step with its scope for a surface outside any plugin, or the entry moves to its own Activity and definition; the change-execution spec assertion, the `execute-change` task-message rule and the spec-tree changelog entry then name that owner.

## A subagent-definition round carries no committed-head skill audit for its calling-skill update

**Evidence**: `spec-tree:changes-reviewer` run `2026-10-03_21-54-22-438-ece57dd8f255` on head `1fd878a45b689558d17066797f74d806631edd92`, finding severity `DEBT`, category evidence, against `src/plugins/spec-tree/skills/execute-change/SKILL.md` and `change-execution.md`. `instructions:create-subagent` step 5 updates the calling skill through `instructions:create-skill`, which dispatches no skill audit, while the Verifier pairing of a `change-subagent-author` round names `instructions:subagent-auditor` only.

**Impact**: when a Change's subagent-definition Activity also edits a calling skill, that edit reaches `/merge` with a skill audit only if the Change's Frame names a skill-surface obligation for it.

**Settlement condition**: the pairing of a subagent-definition round names `instructions:skill-auditor` as well whenever the round's committed diff changes a skill surface, in the `execute-change` definitions text, its step 5.3 and the change-execution assertion, and one typed skill audit of `execute-change` then approves.

## `instructions:create-subagent` declares no repair-block intake for a Fixer round

**Evidence**: `spec-tree:changes-reviewer` run `2026-10-03_22-50-05-358-7abe73e44d07` on head `59622008c0a2f9b78310058eda2d61bce96f9f52`, finding severity `DEBT`, category consistency, against the Fixer rule of `src/plugins/spec-tree/skills/execute-change/SKILL.md`. A Fixer round of `change-skill-author` or `change-subagent-author` receives its Author's task message and a repair block of rejected verdicts and failed command output. The `improve` route of `instructions:create-skill` routes supplied findings to `workflows/repair-skill.md`, which takes each supplied finding and each requested change as one inventory row and returns a disposition for every row. `instructions:create-subagent` takes only its configuration target and declares no intake for a supplied block.

**Impact**: a `change-subagent-author` Fixer round started by a rejected verdict, a failed deterministic command or a `/merge` finding repairs only what its own catalog check of the definition finds, so a defect that check does not reproduce returns to the repeated-defect stop of `/execute-change`.

**Settlement condition**: `instructions:create-subagent` declares an intake that joins a supplied repair block of verdicts and failed command output to the findings the round repairs, and the Fixer rule of `/execute-change` then drops its exception for that skill.

## No route produces the invocation evidence of a subagent definition an Executor delivers

**Evidence**: `spec-tree:changes-reviewer` run `2026-10-03_22-56-23-685-4cdbf8555ae6` on head `72378e875578070b6574c37595f0882802f41e3d`, finding severity `DEBT`, category evidence, against `src/plugins/spec-tree/skills/execute-change/SKILL.md` and `change-execution.md`. `/subagent-standards` requires each subagent definition without declared per-harness release acceptance to retain its exact-definition minimal isolated invocation, and `instructions:create-subagent` returns that invocation as verification still outstanding. The `<definitions>` table of `/execute-change` has no row whose result is a retained invocation run, the Executor produces no artifact, and the paired Verifier of a `change-subagent-author` round is `instructions:subagent-auditor` alone.

**Impact**: a subagent-definition Activity completes only when its auditor finds the invocation evidence present, so a definition whose evidence is absent reaches the repeated-defect stop of `/execute-change` with no round that can produce it.

**Settlement condition**: a `<definitions>` row or named Activity result produces and retains the invocation run for the committed emitted definition, steps 5.3 and 5.4 of `/execute-change` require it before the round completes, and the change-execution assertion on the subagent-definition round names it.

## `/execute-change` resolves a held Change from a marker a compaction may drop

**Evidence**: `instructions:skill-auditor` finding f-010, severity `WARNING`, rule `compaction_marker_survival`, against `src/plugins/spec-tree/skills/execute-change/SKILL.md` step 1, in the typed skill audit of head `add3e3e862f7512a55e8b9655d07f78412abe87c`. Step 1 falls back to the newest `<CLAIMED_CHANGE>` marker in the conversation without the compaction caveat `/release-change` and `/close-change` state.

**Impact**: an Executor resumed after a compaction finds no marker and stops with `not-held` instead of asking for the issue reference.

**Settlement condition**: step 1 carries the compaction caveat the Lifecycle skills state, and one typed skill audit of `execute-change` raises no `compaction_marker_survival` finding.

## `/execute-change` carries two skill-audit debt findings on untouched text

**Evidence**: `instructions:skill-auditor` run `2026-10-07_06-57-56-424-f64221b6b17a` rejected the audit of `execute-change` at head `9d7f098b0afb894c102143d3bc4e2aaeaa993588` on two `debt` findings. The changeset's diff of `src/plugins/spec-tree/skills/execute-change/SKILL.md` against the base is line 6, the `gh api repos/*/issues/*/dependencies/blocked_by` grant; no finding lies on changed text. Rule `success-criteria-soundness`, `SKILL.md` lines 121-127: the success criteria cover only the `closed` and `released` results, so a correct `not-held`, `unavailable` or `release-refused` result cannot be judged against them. Rule `unresolved-ambiguity`, `SKILL.md` line 92 (step 6): a valid `/merge` finding goes to a Fixer of the definition whose round produced the named file, with no route when no round of this session produced it, as after a resume from a Handoff.

**Impact**: a result that is correct but not `closed` or `released` has no criterion that judges it, and an Executor resumed from a Handoff has no stated route for a finding on a file an earlier session produced.

**Settlement condition**: each declared result has a success criterion, step 6 states a route for a finding whose file has no producing round in this session, and one typed skill audit of `execute-change` raises neither finding.
