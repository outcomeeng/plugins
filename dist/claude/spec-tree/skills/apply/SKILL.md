---
name: apply
description: >-
  ALWAYS invoke this skill before implementing any spec-tree work item.
  NEVER write code, tests, or architecture for a spec-tree node without this skill.
argument-hint: "[--agent] [full-spx-node-path]"
allowed-tools: Read, Skill, Agent, AskUserQuestion
---

<objective>
A spec-tree work item implemented and ready for the delivery boundary the user requested.

</objective>

<quick_start>

0. Select the slice when the work is a plan or proposal, not a specific node or queue — invoke `/slice` to select the observable slice whose node set becomes the work queue (see `<invocation_modes>`)
1. Load methodology (Step 1 — once per session)
2. Load work item context (Step 2 — every node)
3. Architect -> audit until APPROVED (Steps 3–4)
4. Test -> audit until APPROVED (Steps 5–6)
5. Implement -> audit until the rendered projection reports `terminalStatus: approved` (Steps 7–8)
6. Evidence-auditor gates for touched `[test]` and `[eval]` evidence, then whole-changeset review when the change reaches beyond the target node (Step 9)
7. Run the terminal full deterministic gate when the repository requires it, only after all agentic gates converge
8. Merge — carry default-branch work through `/merge` until it reaches the default branch on origin (Step 10)

</quick_start>

<invocation_modes>

The raw invocation string `$ARGUMENTS` controls what runs before the per-node flow below. Parse it exactly once before Step 0:

- `$ARGUMENTS` beginning with `--agent` → dispatch the typed `applier` agent through the current runtime's subagent tool, passing the optional canonical full `spx/...` node path that follows it. Do not run the per-node authoring steps in the main context. The `applier` role does not review the whole changeset or merge. On return, treat its live-file audit handoffs as advisory work summaries: run focused deterministic verification, apply `<verification_checkpoint>` to commit the stabilized tree, confirm the worktree is clean, and replace each live-file request with the resulting committed `<base>..<head>` scope and no live file list before dispatching the auditor. Then continue with Step 9 (when the change is cross-node) and Step 10 over the resulting changeset.
- `$ARGUMENTS` containing a canonical full `spx/...` node path without `--agent` → the work queue is that single node.
- Empty `$ARGUMENTS` → determine the work from the conversation; if nothing is clear, read `spx/EXCLUDE`, whose entries are relative to `spx/`, and prefix each non-comment, non-blank entry with `spx/` before adding it to the work queue. Never pass a bare `spx/EXCLUDE` entry to `/contextualize`. If no work is found, report "Nothing to apply" and stop.

When the work is described as a plan or proposal rather than a specific node or queue, invoke `/slice` first: it selects the next executable observable slice and produces the node set that becomes this flow's work queue. Skip the preflight when the queue is already a specific node or an `spx/EXCLUDE` list.

When the queue holds more than one node, order by numeric index prefix (lower first) — lower-indexed nodes constrain higher-indexed ones. For each node in order:

1. Strip the canonical node path's leading `spx/` to derive its `spx/EXCLUDE` entry. If that relative entry is listed, remove its exact line first — the `spx` CLI then includes its tests in `spx test passing`.
2. Run Steps 1–9 on the node.
3. Confirm the final gate subject is committed and the worktree is clean.
4. Proceed to the next node without stopping or asking, subject to the gate-retry limits in `<review_gates>`.

If a node's flow cannot reach its gate-specific passing state or a converged review within the retry limit, stop the queue, report the failed node and step, and leave the remaining nodes in `spx/EXCLUDE`. Step 10 (`/merge`) runs once over the whole changeset after the queue completes.

</invocation_modes>

<language_detection>

Before starting Step 3, determine the product language:

- `tsconfig.json` exists -> **TypeScript**
- `pyproject.toml` or `setup.py` exists -> **Python**
- `Cargo.toml` or `rust-toolchain.toml` exists -> **Rust**
- Multiple supported language markers exist -> inspect the loaded spec node for a single applicable language; when ambiguity remains, ask the operator and stop before Step 3 until one language is selected
- No supported marker exists, or the selected language has no installed architecture, test, and code skills -> stop before Step 3 and report the exact marker state plus the missing language-plugin capability

Proceed to Step 3 only after exactly one supported language and its required skill surface resolve. Use that language for ALL Steps 3–8. Do not switch mid-flow.

</language_detection>

<scope_detection>

Before starting Step 3, determine the change's scope — this determination governs every later gate:

- **Node-local** — the entire diff stays within the target node's own directory (its spec, its `tests/`, and the implementation files that node governs).
- **Cross-node** — the work touches anything else: a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node.

When the scope is cross-node, every audit gate — Steps 4, 6, and 8 — runs at **whole-changeset** scope, not only the target node, and Step 9 is REQUIRED before the flow may be declared complete. A per-node audit reads only the target node's files; it cannot see a regression the change introduced in a file the node does not own. Carry the determination through Steps 4, 6, and 8 — each gate step restates the scope requirement at its point of action.

</scope_detection>

<stabilized_diff_rule>

Before any audit gate or whole-changeset review runs, self-converge the diff: read the changed specs, tests, and implementation together; confirm the design is coherent; and fix obvious contradictions before asking an auditor or reviewer to find them. Audit gates confirm a stabilized design. They are not the design loop.

When a gate returns `REJECTED`, `UNKNOWN`, or `BLOCKED`, or when a review surfaces a valid finding, treat it as evidence of a defect class. Read the touched node(s) — the files they govern — find same-class instances, and fix the class before re-running the gate. Same-class means the same rule, source contract, evidence pattern, lifecycle step, generated-source relationship, or architectural boundary. A patch to the cited line alone is sufficient only when the sweep proves the defect isolated.

Do not re-run a gate after every micro-edit. Batch the class fix, re-read the affected diff, then run the gate once on the stabilized tree. If repeated findings keep reopening the same design area, stop patching and refactor Claude's approach before the next gate.

</stabilized_diff_rule>

<verification_checkpoint>

Before dispatching any persisted audit or review gate, bind its subject to an exact local commit:

1. Run the touched-scope deterministic verification required by the repository overlay over the stabilized changes. Do not run an aggregate gate whose generated-output drift check requires committed `src/` and `dist/` files before creating the checkpoint.
2. When the relevant tracked or untracked files differ from `HEAD`, invoke `/commit-changes` to create an atomic local verification checkpoint.
3. Confirm the worktree is clean and record the checkpoint's full `HEAD` commit ID.
4. Dispatch the gate against the committed `<base>..<head>` scope. Do not supply a live file list for a gating run. The repository's declared full deterministic gate, when required, runs once against the clean checkpoint head as a later lifecycle step rather than before every checkpoint.

An audit over modified or untracked files is advisory. It may provide early feedback, but it never satisfies a Step 4, Step 6, Step 8, evidence-auditor, Step 9, or merge-readiness predicate.

After a rejected audit or valid review finding, repair the defect class, rerun deterministic verification, and create a new checkpoint commit before redispatch. Preserve the earlier checkpoint identity while its run remains prior context; do not amend the audited commit in place.

</verification_checkpoint>

<evidence_auditor_gate>

Before Step 9 invokes `changes-reviewer`, run the applicable artifact-type evidence auditors over the stabilized diff. This gate is separate from the language-specific Step 6 test audit: Step 6 checks the tests written for the target node in the TDD flow; this pre-review gate checks any evidence artifacts the final changeset would publish.

Run deterministic verification first. The main conversation brings local validation, tests, and required eval runs to passing for the touched scope before dispatching evidence auditors. A dispatched evidence auditor reads and judges evidence quality; it never runs deterministic verification.

Dispatch `test-evidence-auditor` before Step 9 when the diff creates or modifies any `[test]` assertion, linked test file, or test-infrastructure artifact imported by a linked test. Include the governing node, assertion text or spec path plus assertion headings, and the test files in the dispatch prompt. If the auditor returns `REJECTED`, `UNKNOWN`, a failing row, an unknown row, or a reject finding, fix the evidence defect class, re-run deterministic verification, and re-dispatch before Step 9.

Dispatch `eval-evidence-auditor` before Step 9 when the diff creates or modifies any `[eval]` assertion, `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, or producer artifact for an eval-backed assertion. Include the governing node, assertion text or spec path plus assertion headings, the eval artifacts, and the producer artifacts in the dispatch prompt. If the auditor returns `FAIL`, `UNKNOWN`, a failing row, an unknown row, or a reject finding, fix the evidence defect class, re-run the required eval evidence, and re-dispatch before Step 9.

Before dispatching an applicable evidence auditor, apply `<verification_checkpoint>`. When both evidence classes changed, dispatch both auditors against the same checkpoint before Step 9. Step 9 starts only after every applicable evidence-auditor verdict is clean on the exact committed diff it reviews.

</evidence_auditor_gate>

<skill_map>

Step 0 and Steps 1–2 are language-independent. Steps 3–8 use the detected language. Steps 9 and 10 are language-independent; Step 0 runs only when the work is described as a plan or proposal rather than a specific node or queue, Step 9 runs only when the change reaches beyond the target node, and Step 10 runs unless the work is explicitly scoped to a proposal, analysis, review, or local-only change.

| Step | Purpose                  | TypeScript                                                       | Python                      | Rust                      |
| ---- | ------------------------ | ---------------------------------------------------------------- | --------------------------- | ------------------------- |
| 0 §  | Select the slice         | `Skill("spec-tree:slice")`                                       | same                        | same                      |
| 1    | Load methodology         | `Skill("spec-tree:understand")`                                  | same                        | same                      |
| 2    | Load context             | `Skill("spec-tree:contextualize", args: "{full-spx-node-path}")` | same                        | same                      |
| 3    | Architect                | `Skill("architect-typescript")`                                  | `Skill("architect-python")` | `Skill("architect-rust")` |
| 4    | Architecture audit       | `adr-auditor` agent                                              | same                        | same                      |
| 5    | Write tests              | `Skill("test-typescript")`                                       | `Skill("test-python")`      | `Skill("test-rust")`      |
| 6    | Test audit               | `test-evidence-auditor` agent                                    | same                        | same                      |
| 7    | Implement                | `Skill("code-typescript")`                                       | `Skill("code-python")`      | `Skill("code-rust")`      |
| 8    | Implementation audit     | `implementation-auditor` agent                                   | same                        | same                      |
| 8a   | Evidence-auditor gates   | `test-evidence-auditor`, `eval-evidence-auditor` agents          | same                        | same                      |
| 9    | Whole-changeset review † | `changes-reviewer` agent                                         | same                        | same                      |
| 10   | Merge ‡                  | `Skill("spec-tree:merge")`                                       | same                        | same                      |

§ Step 0 runs only when the work is described as a plan or proposal rather than a specific node or queue; it selects the observable slice whose node set becomes the work queue (see `<invocation_modes>`).
† Step 9 runs only when the change touches files or specs beyond the target node (see the step for the condition).
‡ Step 10 runs for any change destined for the default branch — skip only when the user explicitly scoped the work to a proposal, analysis, review, or local-only change (see the step).

Invoke the exact skill or agent surface shown. Never substitute, skip, or reorder.

</skill_map>

<workflow>

<step number="1" name="Load methodology" frequency="once per session">

Invoke `/understand`.

This loads the spec-tree methodology — node types, assertion formats, durable map rules. Skip if `SPEC_TREE_FOUNDATION` marker is already present in this session.

**Do not proceed until complete.**

</step>

<step number="2" name="Load work item context" frequency="every node">

Invoke `/contextualize` with the canonical full `spx/...` node path from the work queue.

Load the full context hierarchy for the specific node — parent chain, sibling nodes, applicable decisions, assertions.

**Repeat for every new node.** Do not reuse context from a previous node.

**Do not proceed until complete.**

</step>

<step number="3" name="Architect">

Invoke the architecting skill for the detected language.

Produce the ADR(s) for the work item. The architecture must be complete before audit.

</step>

<step number="4" name="Architecture audit" gate="true">

Classify the ADR itself before dispatch: use `language-neutral` when the decision constrains no implementation language; otherwise enumerate every implementation-language partition the decision constrains. Derive the partitions from the ADR's governed implementation surface and the committed audit scope, preserving every language for a cross-language decision instead of collapsing the classification to the flow's detected language.

Dispatch `adr-auditor` with the ADR path, governing node path, exact committed audit scope chosen in `<scope_detection>`, and `Scope classification: language-neutral` or `Scope classification: implementation-language partitions: <comma-separated languages>`. Require only the structured JSON verdict specified by `audit-adr`. The auditor composes each declared language's `audit-{lang}-architecture` concern inside its isolated context.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — an architecture regression the change introduced in a file the node does not own is invisible to a per-node audit.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`.

**REJECTED -> fix the defect class -> re-dispatch this step.** Loop until APPROVED.

</step>

<step number="5" name="Write tests">

Invoke the testing skill for the detected language.

Write tests for all assertions in the spec. Tests come before implementation — no exceptions.

</step>

<step number="6" name="Test audit" gate="true">

Dispatch `test-evidence-auditor` with the governing node, assertion text or spec path plus assertion headings, linked test files, detected language, and the same audit scope chosen in `<scope_detection>`. The auditor composes the detected language's `audit-{lang}-tests` concern inside its isolated context.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — test evidence the change invalidated in a sibling node is invisible to a per-node audit.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`.

**REJECTED -> fix the defect class -> re-dispatch this step.** Loop until APPROVED.

</step>

<step number="7" name="Implement">

Invoke the coding skill for the detected language.

Write implementation code. All tests from Step 5 must pass.

</step>

<step number="8" name="Code audit" gate="true">

Dispatch the `implementation-auditor` agent with the repository path, exact committed changeset scope, no live file list, governing node path, detected language, and deterministic verification already run.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — as Steps 4 and 6 already did at their gates. Widening the three per-node audits is necessary but not sufficient: each inspects through its own lens (architecture, test evidence, code), so the distinct whole-diff review in Step 9 remains required for cross-cutting effects no single audit lens catches.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`.

The implementation-auditor composes the installed `audit-{lang}-{code|tests|architecture}` concern skills and records the run through `spx verification run`. Do not invoke those concern skills directly from the main conversation. Read the returned rendered projection: its `terminalStatus` is the Step 8 verdict — `approved` passes, `rejected` requires repair, and a missing projection or exact blocked command blocks the gate.

**Projection `terminalStatus: rejected` or BLOCKED -> fix the defect class or exact blocked command -> re-dispatch this step.** Loop until the rendered projection reports `terminalStatus: approved`.

</step>

<step number="9" name="Whole-changeset review" gate="true" condition="the change touches files or specs beyond the target node">

Skip this step only when the entire diff is confined to the target node's own directory — its spec, its `tests/`, and the implementation files that node governs. The moment the work touches anything else — a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node — this step is REQUIRED before the flow may be declared complete.

Before invoking the review, run `<evidence_auditor_gate>`, then apply `<verification_checkpoint>`. The reviewer must see the same committed diff whose touched evidence artifacts passed their artifact-type evidence audits.

Run a whole-diff review over the full changeset (not only the target node) via the `changes-reviewer` agent. The per-node gates in Steps 4, 6, and 8 inspect the target node; they do not see cross-node effects — a stale reference a rename left in a sibling, dead code a move orphaned, a spec a consolidation made false. The whole-diff review catches those, and catching them here costs one early review instead of many rounds later at merge time.

Apply `<stabilized_diff_rule>` before invoking the review. Fix every valid finding it surfaces, including every in-scope same-class instance found by the same-class sweep, then re-run. **Unaddressed valid finding -> fix the defect class -> re-run this step.** Loop until the review converges.

</step>

<step number="10" name="Merge" condition="the change is destined for the default branch">

Skip this step only when the user explicitly scoped the work to a proposal, analysis, review, or local-only change — then state that scope and stop. For every other change, the work is destined for the default branch, and the flow is NOT complete at Step 9.

Local readiness is not delivered value. A Step 8 projection with `terminalStatus: approved`, a converged Step 9 review, passing tests, a clean working tree, and a local commit ahead of base are progress. Delivered value is the change merged to the default branch on origin.

Invoke `/merge`. It selects the transport and drives the change to the default branch under its own authority gates — this flow neither re-implements the merge protocol nor re-decides those gates. The `/merge` lifecycle owns commit, push, integration review, and merge.

The flow is complete only when the change reaches the default branch on origin, or an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base is never the endpoint for default-branch work.

Claude tends to report the flow done the moment Step 9 converges and tests pass — while nothing has been committed, pushed, reviewed at integration time, or merged. That treatment of local readiness as completion is the exact failure this step exists to prevent.

</step>

</workflow>

<terminal_full_gate>

When the repository overlay, governing node, or merge lifecycle requires a full deterministic bundle, run the repository's declared full deterministic gate exactly once at the terminal verification point: after Steps 4, 6, 8, applicable evidence-auditor gates, and Step 9 have converged on the same clean committed head. Do not run that full gate before those agentic checks, inside an auditor, or concurrently with another heavy command.

If the full deterministic gate fails, fix the reported defect, run the focused touched-scope checks, create a new checkpoint commit, rerun every invalidated agentic gate, and only then run the declared full gate again. A successful full gate is invalidated by any subsequent source, test, spec, generated-output, or configuration change.

</terminal_full_gate>

<review_gates>

Steps 4, 6, and 8 are blocking audit gates. Steps 4 and 6 emit verdicts from their auditor contracts. Step 8 returns an `spx verification run` token and rendered projection whose `terminalStatus` is authoritative; an exact blocked command is a blocked result. Step 9 is a blocking whole-changeset review gate that runs whenever the change reaches beyond the target node. Step 10 is the terminal lifecycle boundary for default-branch work — not a retry-loop gate, but a hard precondition for declaring the flow complete.

- Before starting Step 5: scan the conversation for the Step 4 verdict. If `APPROVED` is not present, stop — invoke Step 4.
- Before starting Step 7: scan the conversation for the Step 6 verdict. If `APPROVED` is not present, stop — invoke Step 6.
- Before considering implementation complete: inspect the Step 8 rendered projection. If `terminalStatus` is absent or differs from `approved`, stop — invoke or repair Step 8.
- Before declaring the flow complete: if the change touches anything beyond the target node, scan for a converged Step 9 review. If it is absent or has unaddressed valid findings, stop — invoke Step 9.
- Before invoking `/merge` when a full deterministic bundle is required: confirm the repository-declared full deterministic gate ran after every applicable agentic gate and against the current clean committed head. If any source, test, spec, generated-output, or configuration file changed afterward, rerun the invalidated agentic gates before running the declared full gate again.
- Before declaring the flow complete for default-branch work: confirm the change reached the default branch on origin through Step 10's `/merge`, or that the user scoped the work to a proposal, analysis, review, or local-only change, or that an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base does not satisfy this — invoke Step 10.

On `REJECTED`, `UNKNOWN`, or `BLOCKED` at Steps 4 and 6; projection `terminalStatus: rejected` or a blocked result at Step 8; or an unaddressed valid finding at Step 9: fix the defect class or exact blocked command, re-dispatch the same auditor, and inspect the new result.

**3 consecutive rejected, unknown, or blocked results on the same gate (Steps 4, 6, 8), or 3 consecutive Step 9 runs that still surface unresolved valid findings -> STOP.** Surface the stuck gate to the user via `AskUserQuestion`: report the gate, its most recent verdict (for Step 9, the outstanding findings), the same-class sweep already performed, and what did not resolve. A convergence loop that keeps reopening valid findings is a signal Claude's approach is unstable; refactor the approach before asking the same gate again.

</review_gates>

<rationale>
When something breaks or behaves unexpectedly, Claude's instinct is to write ad hoc code — a quick script, a throwaway snippet, a print-and-pray debugging session. That instinct is the symptom, not the fix. The problem surfaced because the tests were insufficient. The ad hoc code patches over one instance; a proper test catches every future instance too.

1. **Do not** write ad hoc code to "see what's happening."
2. **Do** write a test that reproduces the problem. Hitting this issue proves the test coverage has a gap.
3. **Then** fix the implementation until the test passes.

This is not slower. The ad hoc script takes the same effort as a test, but the script gets deleted and the test stays.

</rationale>

<failure_modes>

**Failure 1: Claude closed the flow at Step 9.** Claude reported the flow complete the moment the Step 8 audit passed, tests were green, and the Step 9 review converged — while nothing had been committed, pushed, reviewed at integration time, or merged. Signal: a "done" claim for default-branch work with a clean working tree or a local commit ahead of base and no merged PR. Avoid: for default-branch work the flow is incomplete until Step 10 reaches the default branch on origin; local readiness is progress, never delivered value.

**Failure 2: Claude patched the cited line instead of the defect class.** An audit gate or the Step 9 review cited one instance; Claude fixed that line, re-ran the gate, and the same class reopened on the next iteration elsewhere. Signal: repeated rejected verdicts reopening the same rule, source contract, or evidence pattern. Avoid: per `<stabilized_diff_rule>`, treat each finding as defect-class evidence — sweep the touched node(s), fix every in-scope instance, then run the gate once on the stabilized tree.

**Failure 3: Claude kept running the flow in the main context after dispatching `--agent`.** Invoked with `--agent`, Claude launched the `applier` role and then also ran Steps 1–8 in the main context, duplicating the work. Signal: main-context architect/test/code steps after an `applier` dispatch. Avoid: after `--agent` dispatch, stop the per-node steps in the main context; resume only at Step 9 (when cross-node) and Step 10 once the `applier` returns.

</failure_modes>

<success_criteria>

Scan the conversation for these markers before declaring done:

- [ ] `SPEC_TREE_FOUNDATION` marker present (Step 1)
- [ ] `SPEC_TREE_CONTEXT` marker present (Step 2)
- [ ] Step 4 `adr-auditor` emitted `APPROVED`
- [ ] Step 6 `test-evidence-auditor` emitted `APPROVED` or an equivalent passing JSON verdict
- [ ] Step 8 `implementation-auditor` returned an `spx verification run` token and rendered projection whose `terminalStatus` is `approved`
- [ ] If the change touched `[test]` assertions, linked tests, or imported test-infrastructure artifacts: `test-evidence-auditor` approved the exact diff before Step 9
- [ ] If the change touched `[eval]` assertions, eval artifacts, or producer artifacts for eval-backed assertions: `eval-evidence-auditor` passed the exact diff before Step 9
- [ ] If the change touched anything beyond the target node: the last Step 9 `changes-reviewer` run reported no `BLOCKING` or `DEBT` finding, or every such finding was fixed or individually refuted as unbacked
- [ ] The product's declared touched-scope verification command has passed for the changed node and implementation, using the consumer repository's local verification overlay or root instructions to select the concrete command
- [ ] For default-branch work: the change reached the default branch on origin through Step 10's `/merge`, unless the user scoped the work to a proposal, analysis, review, or local-only change, or an explicit merge lifecycle gate blocks with no independent local action remaining — a clean working tree, a local commit, or a branch ahead of base does not satisfy this

</success_criteria>
