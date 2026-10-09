---
name: apply
description: >-
  ALWAYS invoke this skill before implementing any spec-tree work item.
  NEVER write code, tests, or architecture for a spec-tree node without this skill.
argument-hint: "[full-spx-node-path | plan-or-proposal]"
allowed-tools: Read, Edit, Write, Grep, Glob, collaboration.spawn_agent, collaboration.wait_agent, request_user_input, Bash(git status:*), Bash(git rev-parse:*)
---

<objective>
A spec-tree work item implemented, verified, and delivered to the boundary the user requested — the default branch on origin unless the request names a narrower one.

</objective>

<invocation_modes>

The raw invocation string `$ARGUMENTS` controls what runs before the per-node flow below. Parse it exactly once before Step 0:

- `$ARGUMENTS` containing a canonical full `spx/...` node path → the work queue is that single node.
- Empty `$ARGUMENTS` → determine the work from the conversation. If nothing is clear, complete Step 1 first — use skill `spec-tree:understand` when the live `SPEC_TREE_FOUNDATION` marker is absent — then read `spx/EXCLUDE`, whose entries are relative to `spx/`, and prefix each non-comment, non-blank entry with `spx/` before adding it to the work queue. Never access `spx/EXCLUDE` before the foundation is live, and never pass a bare entry to `/contextualize`. If no work is found, report "Nothing to apply" and stop.

When the work is described as a plan or proposal rather than a specific node or queue, use skill `spec-tree:slice` first: it selects the next executable observable slice and produces the node set that becomes this flow's work queue. Skip the preflight when the queue is already a specific node or an `spx/EXCLUDE` list.

Complete Step 1 before the queue loop in every mode, so the foundation is live before the loop reads or edits `spx/EXCLUDE`. When the queue holds more than one node, order by numeric index prefix (lower first) — lower-indexed nodes constrain higher-indexed ones. For each node in order:

1. Strip the canonical node path's leading `spx/` to derive its `spx/EXCLUDE` entry. If that relative entry is listed, remove its exact line first — the `spx` CLI then includes its tests in `spx test passing`.
2. Run Steps 2–9 on the node, and Step 1 again first when a compaction has made the foundation marker absent.
3. Confirm the final gate subject is committed and the worktree is clean.
4. Proceed to the next node without stopping or asking, subject to the gate-retry limits in `<review_gates>`.

If a node's flow cannot reach its gate-specific passing state or a converged review within the retry limit, stop the queue, report the failed node and step, and leave the remaining nodes in `spx/EXCLUDE`. Step 10 (`/merge`) runs once over the whole changeset after the queue completes.

</invocation_modes>

<language_detection>

Before starting Step 3, determine the product language:

- `tsconfig.json` exists -> **TypeScript**
- `pyproject.toml` or `setup.py` exists -> **Python**
- `Cargo.toml` or `rust-toolchain.toml` exists -> **Rust**
- `go.mod` exists -> **Go**
- Multiple supported language markers exist -> inspect the loaded spec node for a single applicable language; when ambiguity remains, ask the operator and stop before Step 3 until one language is selected
- No supported marker exists, or the selected language has no installed architecture, test, and code skills -> stop before Step 3 and report the exact marker state plus the missing language-plugin capability

Proceed to Step 3 only after exactly one supported language and its required skill surface resolve. Use that language for ALL Steps 3–8. Do not switch mid-flow.

</language_detection>

<scope_detection>

Before starting Step 3, determine the change's scope — this determination governs every later gate:

- **Node-local** — the entire diff stays within the target node's own directory (its spec, its `tests/`, and the implementation files that node governs).
- **Cross-node** — the work touches anything else: a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node.

When the scope is cross-node, each audit gate covers the **whole changeset** in the form its dispatch takes — Step 4 every ADR and PDR governing an affected surface, Step 6 every governed node whose evidence the change touches, Step 8 the committed changeset selector it always receives — and Step 9 is REQUIRED before the flow may be declared complete. A target-node-only audit cannot see a regression the change introduced in a file the node does not own. Carry the determination through Steps 4 and 6, which restate their cross-node dispatch at the point of action.

</scope_detection>

<launch_contract>

Each audit or review step below requests exactly one native launch with its mapped subagent name and target-only prompt. Use the native tool schema and result-collection capabilities. A failed launch or unusable final result stops that invocation: analyze and report the exact failure without another launch, a substitute subagent or model, an alternative launch mechanism, or an audit in this conversation.

Persist accepted requirements in decisions and specs before dispatch. Start each Verifier without authoring history, following the root guide's isolation mechanics. Never append an author-written context packet, reasoning, summary, or suggested verdict. The invoked skill independently discovers its evidence from the target and configured instructions.

A sealed run or complete `BLOCKED` diagnostic under `<auditor_verdict>`, and a raw review run token, follow the existing finding-repair workflow: repair the defect class or the named boundary, verify and checkpoint the changed subject, then make one launch for that new subject. Never use a repair loop to replace a failed launch or unusable result. While the native capability reports work still running, collect that same invocation; an observation timeout never authorizes a new launch.

</launch_contract>

<auditor_verdict>

The `spec-tree_adr-auditor`, `spec-tree_pdr-auditor`, `spec-tree_test-evidence-auditor`, `spec-tree_eval-evidence-auditor`, and `spec-tree_implementation-auditor` agents this flow dispatches each record their audit as a sealed `spx verification run`. Each returns exactly one of two final results, and the gate reads its verdict from that result alone:

- **Sealed run** — the `spx verification run` token and the rendered projection. The projection's `terminalStatus` is the verdict: `approved` approves the subject; `rejected` rejects it whatever its finding count, including a run that records no finding because a required unit stayed uncovered.
- **`BLOCKED` diagnostic** — the gate is blocked and holds no verdict. The diagnostic is complete when it carries every field the dispatched agent's output contract declares, beginning with the run token or `not-started`. A run whose payload or finish `spx` refused is blocked even though the run started. Repair the boundary the diagnostic names — the request, a prerequisite, the refused payload or finish, the installation, or the skill load — before a new launch.

Any other final result is unusable and follows `<launch_contract>`: no approval comes from legacy `APPROVED`/`REJECTED`, `PASS`/`FAIL`/`UNKNOWN`, or coherence-verdict JSON, from a transcript or task-output file, or from prose. Preserve the run token and carry the result forward under `<result_carryover>`.

</auditor_verdict>

<stabilized_diff_rule>

Before any audit gate or whole-changeset review runs, self-converge the diff: read the changed specs, tests, and implementation together; confirm the design is coherent; and fix obvious contradictions before asking an auditor or reviewer to find them. Audit gates confirm a stabilized design. They are not the design loop.

When a gate's sealed run renders `terminalStatus: rejected`, or when a review surfaces a valid finding, treat it as evidence of a defect class. Read the touched node(s) — the files they govern — find same-class instances, and fix the class before re-running the gate. Same-class means the same rule, source contract, evidence pattern, lifecycle step, generated-source relationship, or architectural boundary. A patch to the cited line alone is sufficient only when the sweep proves the defect isolated.

Do not re-run a gate after every micro-edit. Batch the class fix, re-read the affected diff, then run the gate once on the stabilized tree.

A rejection whose defect class a prior repair already claimed to close invalidates that repair invariant. Stop localized patching, analyze why the class survived, widen the repair and the same-class scan, and amend the governing workflow, standard, or source contract before the next dispatch. The work queue stops at the node that raised the repeat until that amendment lands; a new line number, file, or example does not make it a new class.

</stabilized_diff_rule>

<verification_checkpoint>

Use skill `spec-tree:merging-standards` and read its `merge-policy.md` reference before the first dispatch of the flow; `<verification_dispatch_readiness>` and `<verification_result_projection>` are its sections, and invoking the compact loader alone does not load them.

Before dispatching any persisted audit or review gate, bind its subject to an exact local commit:

1. Use skill `spec-tree:sync-base` before every deterministic verification command and before every dispatch, and record the result it returns — `already_current` or `rebased` — for the exact head, read from the command and never from memory. Only origin knows the base moved; a result established on a head behind the fetched base tip is a verdict on a tree that cannot merge, and every verifier's resolver refuses that head as a `stale-base` block. A `rebased` result reopens the deterministic results and Verifier verdicts its preservation proof does not cover.
2. Changes may remain uncommitted until another agent session or human is expected or asked to read them. Before dispatching an audit or review, run the touched-scope deterministic verification required by the repository overlay when preparing a gate. Do not run an aggregate gate whose generated-output drift check requires committed generator sources and generated output before creating the checkpoint.
3. When the relevant tracked or untracked files differ from `HEAD`, use skill `spec-tree:commit-changes` before dispatch to commit the exact current version regardless of whether the latest verification state is `passing`, `failing`, or `not-run`; preserve that state in the checkpoint result. After any further change, commit the new version before another audit or review.
4. Confirm the worktree is clean and record the checkpoint's full `HEAD` commit ID.
5. Dispatch the gate only when the required deterministic verification is `passing`, against the committed `<base>..<head>` scope. A `failing` or `not-run` checkpoint remains valid local history for recovery and collaboration while withholding gate dispatch. Do not supply a live file list for a gating run. The repository's declared full deterministic gate, when required, runs once against the clean checkpoint head as a later lifecycle step rather than before every checkpoint.
6. Emit the complete `VERIFICATION_DISPATCH_READY` record `/merging-standards` `<verification_dispatch_readiness>` defines, bound to that exact clean head, and dispatch only once it is complete. `VERIFICATION_DISPATCH_BLOCKED` withholds the dispatch until the named field, subject, result, writer, or defect class is resolved.

An audit or review over modified or untracked files is advisory. It may provide early feedback, but it never satisfies a Step 4, Step 6, Step 8, evidence-auditor, Step 9, or merge-readiness predicate. Commit the exact version before dispatching any persisted gate or asking another agent session or human to read a reusable verification subject.

A Verifier that returns a `stale-base` block returned no verdict: use skill `spec-tree:sync-base`, re-establish the deterministic results on the rebased head, checkpoint, and dispatch again. After a rejected audit or valid review finding, repair the defect class, rerun deterministic verification, and create a new checkpoint commit before redispatch. Append the rejection to the record's `priorRejections` — Verifier, exact head, finding identifiers, defect classes, failed repair invariant, root cause, widened repair rule, and same-class scan — and redispatch only once the new head's record proves every rejection resolved. Preserve the earlier checkpoint identity while its run remains prior context; do not amend the audited commit in place.

</verification_checkpoint>

<result_carryover>

Each Verifier result is preserved once where that Verifier's own skill records it — the review journal for `changes-reviewer`, and the `spx verification run` record for every Auditor `<auditor_verdict>` names. What the flow carries forward from there is the bounded projection `/merging-standards` `<verification_result_projection>` defines: the result reference or raw run token, exact head, verdict, finding identifiers, defect classes, and next required action.

Reopen the complete result by reference when a finding needs exact detail. Never re-paste a complete Verifier payload into a later step, a queue transition to the next node, or the closeout.

</result_carryover>

<evidence_auditor_gate>

After Step 8, run the applicable artifact-type evidence auditors over the stabilized diff. This gate applies to node-local and cross-node changes. It is separate from the Step 6 evidence audit: Step 6 checks the test and eval evidence authored for the target node at that checkpoint in the TDD flow; Step 8a checks every evidence artifact the final changeset would publish.

Run deterministic verification first. Bring local validation, tests, and required eval runs to passing for the touched scope before dispatching evidence auditors. An evidence auditor reads and judges evidence quality; it never runs deterministic verification.

Dispatch `spec-tree_test-evidence-auditor` during Step 8a when the diff creates or modifies any `[test]` assertion, linked test file, or test-infrastructure artifact imported by a linked test. For each affected governing node, pass only its canonical node path. The invoked audit discovers the assertions, linked tests, and complete evidence chain. When its sealed run renders `terminalStatus: rejected`, fix the evidence defect class, re-run deterministic verification, and re-dispatch Step 8a.

Dispatch `spec-tree_eval-evidence-auditor` during Step 8a when the diff creates or modifies any `[eval]` assertion, `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, or producer artifact for an eval-backed assertion. For each affected governing node, pass only its canonical node path. The invoked audit discovers the assertions, eval artifacts, and producers. When its sealed run renders `terminalStatus: rejected`, fix the evidence defect class, re-run the required eval evidence, and re-dispatch Step 8a.

A complete `BLOCKED` diagnostic from either auditor blocks Step 8a until the named boundary is repaired, per `<auditor_verdict>`. Before dispatching an applicable evidence auditor, apply `<verification_checkpoint>`; carry each result forward under `<result_carryover>`. When both evidence classes changed, dispatch both auditors against the same checkpoint. Step 8a completes only after every applicable evidence-auditor run renders `terminalStatus: approved` for the exact committed head it audits.

</evidence_auditor_gate>

<skill_map>

Step 0 and Steps 1–2 are language-independent. Steps 3–8 use the detected language. Steps 9 and 10 are language-independent; Step 0 runs only when the work is described as a plan or proposal rather than a specific node or queue, Step 9 runs only when the change reaches beyond the target node, and Step 10 runs unless the work is explicitly scoped to a proposal, analysis, review, or local-only change.

| Step | Purpose                  | TypeScript                                                                  | Python                               | Rust                             | Go                           |
| ---- | ------------------------ | --------------------------------------------------------------------------- | ------------------------------------ | -------------------------------- | ---------------------------- |
| 0 §  | Select the slice         | Use skill `spec-tree:slice`.                                                | same                                 | same                             | same                         |
| 1    | Load methodology         | Use skill `spec-tree:understand`.                                           | same                                 | same                             | same                         |
| 2    | Load context             | Use skill `spec-tree:contextualize` for `{full-spx-node-path}`.             | same                                 | same                             | same                         |
| 3    | Architect                | Use skill `typescript:architect-typescript`.                                | Use skill `python:architect-python`. | Use skill `rust:architect-rust`. | Use skill `go:architect-go`. |
| 4    | Decision audit           | `spec-tree_adr-auditor`, `spec-tree_pdr-auditor` agents                     | same                                 | same                             | same                         |
| 5    | Establish evidence       | Use skill `spec-tree:verify`.                                               | same                                 | same                             | same                         |
| 6    | Evidence audit           | `spec-tree_test-evidence-auditor`, `spec-tree_eval-evidence-auditor` agents | same                                 | same                             | same                         |
| 7    | Implement                | Use skill `typescript:code-typescript`.                                     | Use skill `python:code-python`.      | Use skill `rust:code-rust`.      | Use skill `go:code-go`.      |
| 7a   | Simplify implementation  | Use skill `typescript:simplify-typescript`.                                 | no simplification skill              | Use skill `rust:simplify-rust`.  | Use skill `go:simplify-go`.  |
| 8    | Implementation audit     | `spec-tree_implementation-auditor` agent                                    | same                                 | same                             | same                         |
| 8a   | Evidence-auditor gates   | `spec-tree_test-evidence-auditor`, `spec-tree_eval-evidence-auditor` agents | same                                 | same                             | same                         |
| 9    | Whole-changeset review † | `spec-tree_changes-reviewer` agent                                          | same                                 | same                             | same                         |
| 10   | Merge ‡                  | Use skill `spec-tree:merge`.                                                | same                                 | same                             | same                         |

§ Step 0 runs only when the work is described as a plan or proposal rather than a specific node or queue; it selects the observable slice whose node set becomes the work queue (see `<invocation_modes>`).
† Step 9 runs only when the change touches files or specs beyond the target node (see the step for the condition).
‡ Step 10 runs for any change destined for the default branch — skip only when the user explicitly scoped the work to a proposal, analysis, review, or local-only change (see the step).

Invoke the exact skill or agent surface shown. Never substitute, skip, or reorder.

</skill_map>

<workflow>

<step number="0" name="Select the slice" frequency="only for a plan or proposal">

Use skill `spec-tree:slice` when the work is described as a plan or proposal rather than a specific node or queue, per `<invocation_modes>`; its node set becomes the work queue. Skip this step for a specific node or an `spx/EXCLUDE` list.

</step>

<step number="1" name="Load methodology" frequency="once per session and after every compaction">

Use skill `spec-tree:understand`.

This loads the spec-tree methodology — node types, assertion formats, durable map rules. Skip only while a live `<SPEC_TREE_FOUNDATION>` marker is present: after a compaction the marker counts as absent until this step emits it again.

**Do not proceed until complete.**

</step>

<step number="2" name="Load work item context" frequency="every node and after every compaction">

Use skill `spec-tree:contextualize` with the canonical full `spx/...` node path from the work queue.

Load the full context hierarchy for the specific node — parent chain, sibling nodes, applicable decisions, assertions.

**Repeat for every new node, and for the current node after every compaction**, which empties the set of contextualized nodes. Do not reuse context from a previous node.

**Do not proceed until complete.**

</step>

<step number="3" name="Architect">

Invoke the architecting skill for the detected language.

Produce every ADR or PDR the work item needs and record the paths of the decisions this step creates or changes. The architecture must be complete before audit. When the governing decisions already decide the work item, the recorded set is empty.

Before the Step 4 decision audit, use skill `spec-tree:verify` separately for every new or changed ADR/PDR path. This moves each decision rule into its canonical verification subsection and supplies that subsection's tag before the auditor judges the decision. Keep target-node assertion routing in Step 5; this pre-audit decision routing creates no executable evidence link inside the decision record.

</step>

<step number="4" name="Decision audit" gate="true">

For each ADR path Step 3 recorded, dispatch `spec-tree_adr-auditor` with only that ADR path. The invoked `audit-adr` discovers its governing node, committed changeset, and implementation-language partitions, then composes each applicable `audit-{lang}-architecture` concern inside its isolated agent session. For each PDR path Step 3 recorded, dispatch `spec-tree_pdr-auditor` with only that PDR path. Read every result under `<auditor_verdict>`. When Step 3 recorded no decision path, this step dispatches nothing and its gate holds.

When the scope is cross-node (see `<scope_detection>`), enumerate the ADRs and PDRs governing every affected surface across the whole changeset and dispatch each decision path separately to its auditor. This gate passes only when every dispatched decision audit's sealed run renders `terminalStatus: approved`.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`; carry its result forward under `<result_carryover>`.

**`terminalStatus: rejected` -> fix the defect class; complete `BLOCKED` diagnostic -> repair the named boundary -> re-dispatch this step.** Loop until every run renders `terminalStatus: approved`.

</step>

<step number="5" name="Establish evidence">

Use skill `spec-tree:verify` for the target node. It selects each assertion's verification type and routes selected test work through `/test` to the detected language specialist. It routes selected eval work through its own eval routing and records pathless audit requirements without producing their verdict.

Establish every selected path-bearing evidence definition before implementation. When `/verify` selects test, the linked tests exist before implementation. When it selects evaluate, the eval definition, cases, prompt, and producer contract exist before implementation. A pathless audit selection records the isolated-verifier requirement and creates no preimplementation artifact.

</step>

<step number="6" name="Evidence audit" gate="true">

Dispatch the auditor matching every path-bearing evidence artifact Step 5 created or changed:

- For test evidence, dispatch `spec-tree_test-evidence-auditor` with only the canonical governing node path. The invoked audit discovers its assertions and complete test-evidence chain, then detects and composes the applicable `audit-{lang}-tests` concern inside its isolated agent session.
- For eval evidence, dispatch `spec-tree_eval-evidence-auditor` with only the canonical governing node path. The invoked audit discovers its `[eval]` assertions, eval artifacts, and real producers.
- A pathless audit requirement creates no authoring artifact for Step 6. Its isolated verifier remains the workflow that produces the eventual audit verdict.

When the scope is cross-node (see `<scope_detection>`), enumerate every governed node whose current linked test or eval evidence the change creates, modifies, or invalidates. Dispatch only each canonical node path, once per governed node and evidence type, in parallel when independent. Step 6 passes only when every applicable dispatched audit's sealed run renders `terminalStatus: approved`. A singular-node audit receives one node path; Step 8a covers the final changed evidence set and Step 9 reviews the whole changeset.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`. Read each result under `<auditor_verdict>` and carry it forward under `<result_carryover>`.

**`terminalStatus: rejected` -> fix the defect class; complete `BLOCKED` diagnostic -> repair the named boundary -> re-dispatch this step.** Loop until every dispatched auditor's run renders `terminalStatus: approved`.

</step>

<step number="7" name="Implement">

Invoke the coding skill for the detected language.

Write implementation code, then run every applicable deterministic check selected in Step 5: selected tests pass and selected evals meet their declared completion threshold. Preserve each pathless audit requirement for its isolated verifier; never fabricate a test artifact for it.

</step>

<step number="7a" name="Simplify implementation">

For Go, Rust, or TypeScript, run the language's simplification skill selected in `<skill_map>` in this conversation after Step 7. A language that ships no simplification skill skips this step.

Before running it, use skill `spec-tree:commit-changes` when needed and require a clean worktree. Record the full committed head. Supply only `HEAD`, or the explicit three-dot range used for the selected base, as its target. The language skill independently selects the changed implementation and its governing evidence.

Require the skill's JSON result with `status`, `reason`, `target`, `base`, `head`, `scope`, `changed_paths`, `changes`, `evidence`, `verification`, `blockers`, and `recovery`. Check the returned target and full head against the committed subject, inspect every retained edit and command result, and apply the result contract:

- `simplified`: inspect the retained patch for scope and behavior preservation. Complete any still-required deterministic checks, then checkpoint every resulting edit before Step 8. Preserve the successful command results against that exact content; do not repeat commands whose subject is unchanged.
- `unchanged`: require no retained edit and a reason explaining the empty scope or absence of a safe improvement, then continue.
- `blocked` or `failed`: preserve the complete prerequisite or verification diagnostic and recovery outcome; stop this node before Step 8. Repair the named prerequisite or implementation through its owning workflow. A new simplification run requires a repaired, verified, committed subject.

An absent or malformed result stops this node before Step 8 with the exact failure. A simplification result supplies no independent audit approval. Step 8 and every applicable evidence and review gate remain required. If later repair changes implementation, repeat Step 7a on the repaired committed subject before its final audits.

</step>

<step number="8" name="Implementation audit" gate="true">

Dispatch `spec-tree_implementation-auditor` with only the committed scope selector: `HEAD` for the current branch, or an explicit three-dot range for a selected base. The invoked skill discovers the repository, governing nodes, verification context, and language partitions; the wrapper supplies its own run-driver identity internally.

The committed scope selector already spans the whole changeset, so a cross-node change needs no other Step 8 dispatch. The audit lenses of Steps 4, 6, and 8 remain necessary but insufficient, so the distinct whole-diff review in Step 9 stays required for cross-cutting effects no single audit lens catches.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`; carry its result forward under `<result_carryover>`.

The implementation-auditor composes the installed `audit-{lang}-{code|tests|architecture}` concern skills and records the run through `spx verification run`. Do not invoke those concern skills directly from this workflow. Read its result under `<auditor_verdict>`. Its command-failure `BLOCKED` result also names the payload source, including for a failed preparation command. A missing-input diagnostic carries `runToken: not-started` and the exact missing selector or identity. A pre-run skill-load `BLOCKED` result is complete only when it carries run token `not-started`, required skill `spec-tree:audit-implementation`, and the exact load or availability failure.

**Projection `terminalStatus: rejected` -> fix the defect class; complete `BLOCKED` diagnostic -> repair the named preparation, input, command, payload, installation, or skill-load boundary.** Verify and checkpoint the changed subject before a new audit. A failed launch or unusable result follows `<launch_contract>` immediately.

</step>

<step number="8a" name="Evidence-auditor gates" gate="true" condition="the change creates or modifies test or eval evidence">

Run `<evidence_auditor_gate>` whenever the stabilized diff creates or modifies a `[test]` assertion, linked test file, imported test-infrastructure artifact, `[eval]` assertion, eval artifact, or producer artifact for eval-backed evidence. The condition applies whether the change is node-local or cross-node.

Skip this step only when the diff changes no test or eval evidence surface named by `<evidence_auditor_gate>`.

</step>

<step number="9" name="Whole-changeset review" gate="true" condition="the change touches files or specs beyond the target node">

Skip this step only when the entire diff is confined to the target node's own directory — its spec, its `tests/`, and the implementation files that node governs. The moment the work touches anything else — a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node — this step is REQUIRED before the flow may be declared complete.

Before invoking the review, confirm every applicable Step 8a evidence-auditor run renders `terminalStatus: approved`, then apply `<verification_checkpoint>`. The reviewer must see the same committed diff whose touched evidence artifacts passed their artifact-type evidence audits.

Dispatch `spec-tree_changes-reviewer` over the full committed changeset, passing only the raw scope token: `HEAD` for the current branch or an explicit committed range for a selected base. Never add a prose prompt, severity filter, or emphasis instruction. Collect the final message through the native result-collection capabilities and require it to be the raw review run token. A tool failure, terminal result without a final message, or non-token final message blocks Step 9 and follows `<launch_contract>`.

Use skill `spec-tree:project-run-journal`, then inspect the returned token through its `render_review_run.py` helper exactly as that skill directs. Treat the helper output as the inspection projection of the sealed journal prefix; the sealed prefix remains the only review result. Read the rendered terminal status, full head/base identity, scope coverage, blocking/debt counts, and findings before deciding whether Step 9 converged. Carry the review forward as the bounded projection `<result_carryover>` defines.

The per-node gates in Steps 4, 6, and 8 inspect through distinct audit lenses; they do not see every cross-node effect — a stale reference a rename left in a sibling, dead code a move orphaned, or a spec a consolidation made false. The whole-diff review catches those effects.

Apply `<stabilized_diff_rule>` before invoking the review. Fix every valid finding in the rendered sealed projection, including every in-scope same-class instance found by the same-class sweep, then verify and checkpoint the changed subject before reviewing it. A missing or unusable raw token follows `<launch_contract>`. If rendering a valid token fails, preserve that token and diagnose the inspection failure through `/project-run-journal`; never launch another reviewer to replace the recorded result. The gate remains blocked until the sealed result is readable and every valid finding is resolved.

</step>

<step number="10" name="Merge" condition="the change is destined for the default branch">

Skip this step only when the user explicitly scoped the work to a proposal, analysis, review, or local-only change — then state that scope and stop. For every other change, the work is destined for the default branch, and the flow is NOT complete at Step 9.

Local readiness is not delivered value. A Step 8 projection with `terminalStatus: approved`, a converged Step 9 review, passing tests, a clean working tree, and a local commit ahead of base are progress. Delivered value is the change merged to the default branch on origin.

Use skill `spec-tree:merge`. It selects the transport and drives the change to the default branch under its own authority gates — this flow neither re-implements the merge protocol nor re-decides those gates. The `/merge` lifecycle owns commit, push, integration review, and merge.

The flow is complete only when the change reaches the default branch on origin, or an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base is never the endpoint for default-branch work.

</step>

</workflow>

<terminal_full_gate>

When the repository overlay, governing node, or merge lifecycle requires a full deterministic bundle, run the repository's declared full deterministic gate exactly once at the terminal verification point: after Steps 4, 6, 8, applicable evidence-auditor gates, and Step 9 have converged on the same clean committed head. Do not run that full gate before those agentic checks, inside an auditor, or concurrently with another heavy command.

If the full deterministic gate fails, fix the reported defect, run the focused touched-scope checks, create a new checkpoint commit, rerun every invalidated agentic gate, and only then run the declared full gate again. A successful full gate is invalidated by any subsequent source, test, spec, generated-output, or configuration change.

</terminal_full_gate>

<review_gates>

Steps 4, 6, 8, and applicable Step 8a are blocking audit gates; each reads its Auditor's sealed run or complete `BLOCKED` diagnostic under `<auditor_verdict>`. Step 9 is a blocking whole-changeset review gate that runs whenever the change reaches beyond the target node. Step 10 is the terminal lifecycle boundary for default-branch work.

- Before starting Step 5: require a Step 4 sealed run rendering `terminalStatus: approved` for every decision path Step 4 dispatched. If a run is absent or its status differs, stop and invoke or repair Step 4.
- Before starting Step 7: require every Step 6 sealed run to render `terminalStatus: approved`. If a run is absent or its status differs, stop and invoke or repair Step 6.
- Before considering implementation complete: inspect the Step 8 rendered projection. If `terminalStatus` is absent or differs from `approved`, stop — invoke or repair Step 8.
- Before Step 8 for Go, Rust, or TypeScript, require Step 7a's usable `simplified` or `unchanged` result for the implementation being verified, with every resulting edit inspected, verified, and committed.
- Before starting Step 9, the terminal full deterministic gate, Step 10, or completion: if the diff touches a test or eval evidence surface named by `<evidence_auditor_gate>`, require every applicable Step 8a sealed run to render `terminalStatus: approved` for the exact committed head, and invoke or repair Step 8a when a run is absent or its status differs. When the diff touches no named evidence surface, skip Step 8a.
- Before declaring the flow complete: if the change touches anything beyond the target node, require a raw Step 9 review run token from the native final result and a rendered sealed projection from `/project-run-journal`. If no invocation has occurred, invoke Step 9. A failed invocation or unusable final result follows `<launch_contract>`; a blocked inspection preserves its token; valid findings follow the repair workflow.
- Before invoking `/merge` when a full deterministic bundle is required: confirm the repository-declared full deterministic gate ran after every applicable agentic gate and against the current clean committed head. If any source, test, spec, generated-output, or configuration file changed afterward, rerun the invalidated agentic gates before running the declared full gate again.
- Before declaring the flow complete for default-branch work: confirm the change reached the default branch on origin through Step 10's `/merge`, or that the user scoped the work to a proposal, analysis, review, or local-only change, or that an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base does not satisfy this — invoke Step 10.

For a sealed run rendering `terminalStatus: rejected` or a complete `BLOCKED` diagnostic at Steps 4, 6, 8, or 8a, or valid findings at Step 9: fix the defect class or repair the named boundary, verify and checkpoint the changed subject, then audit that subject. Launch failures, unusable results, and blocked inspection of a valid review token follow `<launch_contract>` and Step 9; they never enter this relaunch loop.

**3 consecutive `rejected` runs or complete `BLOCKED` diagnostics on the same audit gate (Steps 4, 6, 8, 8a) -> STOP.** Surface the stuck gate to the user via `request_user_input`: report the gate, its most recent verdict and outstanding findings, the same-class sweep already performed, and what did not resolve. A convergence loop that keeps reopening valid findings is a signal Claude's approach is unstable; refactor the approach before asking the same gate again. Repeated valid Step 9 review findings never become this stop or an operator call: the loaded merging standard governs them, and `<stabilized_diff_rule>` widens the same-class repair and amends the invariant before the next review. A failed launch or unusable result stops on its first occurrence under `<launch_contract>`.

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

</failure_modes>

<success_criteria>

- Every product-declared touched-scope deterministic command exits zero on the final committed subject.
- Every applicable decision, test-evidence, eval-evidence, and implementation audit carries a run token whose rendered projection shows `terminalStatus: approved` for the exact committed subject.
- A cross-node changeset carries a raw Step 9 review run token whose sealed projection renders successfully, with every valid finding fixed, including every in-scope same-class instance; unbacked findings are dropped.
- `git rev-parse HEAD` matches the final gate subject and `git status --porcelain` is empty.
- The requested delivery boundary has observable completion: default-branch work has reached the default branch on origin through `/merge`'s selected transport and every declared release action reports success or no-op; proposal, analysis, review, or local-only work reaches its explicitly selected boundary; an explicit lifecycle gate reports its blocking token only after no independent action remains.

</success_criteria>
