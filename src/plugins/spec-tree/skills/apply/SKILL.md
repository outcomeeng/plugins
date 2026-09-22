---
name: apply
description: >-
  ALWAYS invoke this skill before implementing any spec-tree work item.
  NEVER write code, tests, or architecture for a spec-tree node without this skill.
argument-hint: "[full-spx-node-path | plan-or-proposal]"
allowed-tools: Read, Glob, Grep, Edit, Write, {{! tool('use_skill') !}},{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}},{!% endif %!} {{! tool('ask_user') !}}, Bash(git status:*), Bash(git rev-parse:*), Bash(git diff:*), Bash(spx validation:*), Bash(spx spec status:*), Bash(spx test:*), Bash(just test:*), Bash(just check:*), Bash(just check-full:*), Bash(just verify:*), Bash(just validate:*), Bash(pnpm test:*), Bash(pnpm run test:*), Bash(pnpm run check:*), Bash(pnpm run lint:*), Bash(pnpm run typecheck:*), Bash(pnpm run validate:*), Bash(pnpm run verify:*), Bash(npm test:*), Bash(npm run test:*), Bash(npm run check:*), Bash(npm run lint:*), Bash(npm run typecheck:*), Bash(npm run validate:*), Bash(npm run verify:*), Bash(yarn test:*), Bash(yarn run test:*), Bash(yarn run check:*), Bash(yarn run lint:*), Bash(yarn run typecheck:*), Bash(yarn run validate:*), Bash(yarn run verify:*), Bash(bun test:*), Bash(bun run test:*), Bash(bun run check:*), Bash(bun run lint:*), Bash(bun run typecheck:*), Bash(bun run validate:*), Bash(bun run verify:*), Bash(uv run pytest:*), Bash(pytest:*), Bash(cargo test:*), Bash(cargo check:*), Bash(cargo clippy:*), Bash(cargo fmt --check:*), Bash(go test:*), Bash(go vet:*), Bash(make test:*), Bash(make check:*), Bash(make verify:*), Bash(make validate:*)
---

<objective>
A spec-tree work item delivered to the boundary the user requested — for default-branch work, merged to the default branch on origin.

</objective>

<invocation_modes>

The raw invocation string `$ARGUMENTS` controls what runs before the per-node flow below. Parse it exactly once before Step 0:

- `$ARGUMENTS` containing a canonical full `spx/...` node path → the work queue is that single node.
- Non-empty `$ARGUMENTS` that is not a canonical node path → treat it as the plan or proposal `argument-hint` advertises and route it to Step 0, whose node set becomes the work queue.
- Empty `$ARGUMENTS` → determine the work from the conversation. If nothing is clear, complete Step 1 first — invoke `/understand` when the live `SPEC_TREE_FOUNDATION` marker is absent — then read `spx/EXCLUDE`, whose entries are relative to `spx/`, and prefix each non-comment, non-blank entry with `spx/` before adding it to the work queue. Never access `spx/EXCLUDE` before the foundation is live, and never pass a bare entry to `/contextualize`. If no work is found, report "Nothing to apply" and stop.

Construct the work queue through Step 0 when its condition applies; otherwise use the specific node or `spx/EXCLUDE` list resolved above.

When the queue holds more than one node, order by numeric index prefix (lower first) — lower-indexed nodes constrain higher-indexed ones. For each node in order:

1. Strip the canonical node path's leading `spx/` to derive its `spx/EXCLUDE` entry. If that relative entry is listed, remove its exact line first — the `spx` CLI then includes its tests in `spx test passing`.
2. Run Steps 1–9 on the node.
3. Confirm the final gate subject is committed and the worktree is clean.
4. Proceed to the next node without stopping or asking, subject to the gate-retry limits in `<review_gates>`.

If a node's flow cannot reach its gate-specific passing state or a converged review within the retry limit, stop the queue, report the failed node and step, and leave the remaining nodes in `spx/EXCLUDE`. Step 10 (`/merge`) runs once over the whole changeset after the queue completes.

</invocation_modes>

<lane_table>

Classify every Output in the changeset before selecting a language. This table is the Output-kind selector: it decides which artifact auditors judge the artifacts the changeset contains, and malleability neither selects nor deselects them. Select every row present, compose the rows, and run the union of their deterministic lanes. Each selected artifact auditor covers the whole changeset for its kind: once per kind where its subject is that kind's changed surface, and once per artifact where its subject is a single artifact, as a decision auditor's is. A changeset with no code row never stops for language detection. A changed surface matching no row selects no authoring row and still enters the deterministic lane and the whole-changeset review.

| Output kind      | Authoring skill and standards                                                                                                                                                  | Deterministic lane                                                                                   | Artifact auditors                                                                                                                                                                                                                                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Code             | The detected language's architecture, test, code, and optional simplification skills from `<skill_map>`, with that language's architecture, test, and code standards           | The selected language's repository-declared focused validation, tests, evals, formatting, and typing | Step 4 through `{{! subagent_name('spec-tree', 'adr-auditor') !}}` or `{{! subagent_name('spec-tree', 'pdr-auditor') !}}` for each changed decision; Steps 6, 8, and 8a when malleability selects them; Step 9 when malleability selects it                                                                                    |
| Test evidence    | `spec-tree:test` and each applicable installed language specialist, with `spec-tree:test-evidence-standards` and the language's test standards; Step 5 routes its verification | Every selected linked test and eval                                                                  | Steps 6 and 8a through `{{! subagent_name('spec-tree', 'test-evidence-auditor') !}}` and `{{! subagent_name('spec-tree', 'eval-evidence-auditor') !}}` when malleability selects them; Step 9 when malleability selects it                                                                                                     |
| Spec or decision | `spec-tree:author`, with the live `/understand` templates and foundation; Step 5 routes its verification                                                                       | The repository-declared spec validation and status projection                                        | Step 4 through `{{! subagent_name('spec-tree', 'adr-auditor') !}}` or `{{! subagent_name('spec-tree', 'pdr-auditor') !}}` for each changed decision; `{{! subagent_name('spec-tree', 'spec-auditor') !}}` for each changed spec at the artifact-auditor gate, independent of malleability; Step 9 when malleability selects it |
| Skill            | `instructions:create-skill`, with `instructions:skill-standards` and `instructions:agent-prompt-standards`                                                                     | The repository-declared skill build and deterministic skill or documentation checks                  | `{{! subagent_name('instructions', 'skill-auditor') !}}` once over the complete changed skill surface at the artifact-auditor gate when the `instructions` plugin is installed, independent of malleability; Step 9 when malleability selects it                                                                               |
| Prose            | `prose:author-prose`, with `prose:prose-standards`                                                                                                                             | The repository-declared documentation and prose checks                                               | `{{! subagent_name('prose', 'prose-auditor') !}}` once over the complete changed prose surface at the artifact-auditor gate when the `prose` plugin is installed, independent of malleability; Step 9 when malleability selects it                                                                                             |

For the code row only, determine one product language before its first language-specific authoring step:

- `tsconfig.json` exists -> **TypeScript**
- `pyproject.toml` or `setup.py` exists -> **Python**
- `Cargo.toml` or `rust-toolchain.toml` exists -> **Rust**
- `go.mod` exists -> **Go**
- Multiple supported language markers exist -> inspect the loaded spec node for a single applicable language; when ambiguity remains, ask the operator and stop the code row until one language is selected
- No supported marker exists, or the selected language has no installed architecture, test, and code skills -> stop the code row and report the exact marker state plus the missing language-plugin capability

Use that language for every language-specific step in the code row. Do not switch mid-flow. Other selected rows continue independently when the code row is absent.

</lane_table>

<scope_detection>

Before starting the selected authoring lanes, determine the change's scope — this determination governs each selected gate's subject, never which gates run:

- **Node-local** — the entire diff stays within the target node's own directory (its spec, its `tests/`, and the implementation files that node governs).
- **Cross-node** — the work touches anything else: a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node.

Select the numbered evidence gates and the review from the least malleable touched node, and the artifact auditors from the Output kinds present, both under `<evidence_auditor_gate>`. When the scope is cross-node, widen each selected gate to the complete governed subject set: every affected decision for Step 4, every affected evidence node and type for Steps 6 and 8a, and the whole changeset for Step 8. A per-node audit reads only one node's files and cannot see a regression introduced in another governed surface. Step 9 always reviews the full committed changeset when malleability selects it, whether the scope is node-local or cross-node.

</scope_detection>

<launch_contract>

Each simplification, audit, or review step below requests exactly one native launch with its mapped subagent name and target-only prompt. Use the native tool schema and result-collection capabilities. A failed launch or unusable final result stops that invocation: analyze and report the exact failure without another launch, a substitute subagent or model, an alternative launch mechanism, or an audit in this conversation.

Persist accepted requirements in decisions and specs before dispatch. Start each Verifier without authoring history. Never append an author-written context packet, reasoning, summary, or suggested verdict. The invoked skill independently discovers its evidence from the target and configured instructions.

Completed structured verdicts follow the existing finding-repair workflow: repair the defect class, verify and checkpoint the changed subject, then make one launch for that new subject. Never use a repair loop to replace a failed launch or unusable result. While the native capability reports work still running, collect that same invocation; an observation timeout never authorizes a new launch.

</launch_contract>

<stabilized_diff_rule>

Before any audit gate or whole-changeset review runs, self-converge the diff: read the changed specs, tests, and implementation together; confirm the design is coherent; and fix obvious contradictions before asking an auditor or reviewer to find them. Audit gates confirm a stabilized design. They are not the design loop.

When a gate returns `REJECTED`, `UNKNOWN`, or `BLOCKED`, or when a review surfaces a valid finding, treat it as evidence of a defect class. Read the touched node(s) — the files they govern — find same-class instances, and fix the class before re-running the gate. Same-class means the same rule, source contract, evidence pattern, lifecycle step, generated-source relationship, or architectural boundary. A patch to the cited line alone is sufficient only when the sweep proves the defect isolated.

Do not re-run a gate after every micro-edit. Batch the class fix, re-read the affected diff, then run the gate once on the stabilized tree.

A rejection whose defect class a prior repair already claimed to close invalidates that repair invariant. Stop localized patching, analyze why the class survived, widen the repair and the same-class scan, and amend the governing workflow, standard, or source contract before the next dispatch. The work queue stops at the node that raised the repeat until that amendment lands; a new line number, file, or example does not make it a new class.

</stabilized_diff_rule>

<verification_checkpoint>

{!% require_skill 'spec-tree:merging-standards' %!} Read its `merge-policy.md` reference before the first dispatch of the flow; `<verification_dispatch_readiness>` and `<verification_result_projection>` are its sections, and invoking the compact loader alone does not load them.

Before dispatching any persisted audit or review gate, bind its subject to an exact local commit:

1. {!% require_skill 'spec-tree:sync-base' %!} Run it before every deterministic verification command and before every dispatch, and record the result it returns — `already_current` or `rebased` — for the exact head, read from the command and never from memory. Only origin knows the base moved; a result established on a head behind the fetched base tip is a verdict on a tree that cannot merge, and every verifier's resolver refuses that head as a `stale-base` block. A `rebased` result reopens the deterministic results and Verifier verdicts its preservation proof does not cover.
2. Changes may remain uncommitted until another agent session or human is expected or asked to read them. Before dispatching an audit or review, run the touched-scope deterministic verification required by the repository overlay when preparing a gate. Do not run an aggregate gate whose generated-output drift check requires committed generator sources and generated output before creating the checkpoint.
3. When the relevant tracked or untracked files differ from `HEAD`, commit before dispatch: {!% require_skill 'spec-tree:commit-changes' %!} Commit the exact current version regardless of whether the latest verification state is `passing`, `failing`, or `not-run`; preserve that state in the checkpoint result. After any further change, commit the new version before another audit or review.
4. Confirm the worktree is clean and record the checkpoint's full `HEAD` commit ID.
5. Dispatch the gate only when the required deterministic verification is `passing`, against the committed `<base>..<head>` scope. A `failing` or `not-run` checkpoint remains valid local history for recovery and collaboration while withholding gate dispatch. Do not supply a live file list for a gating run. The repository's declared full deterministic gate, when required, runs once against the clean checkpoint head as a later lifecycle step rather than before every checkpoint.
6. Emit the complete `VERIFICATION_DISPATCH_READY` record `/merging-standards` `<verification_dispatch_readiness>` defines, bound to that exact clean head, and dispatch only once it is complete. `VERIFICATION_DISPATCH_BLOCKED` withholds the dispatch until the named field, subject, result, writer, or defect class is resolved.

An audit or review over modified or untracked files is advisory. It may provide early feedback, but it never satisfies a Step 4, Step 6, Step 8, evidence-auditor, Step 9, or merge-readiness predicate. Commit the exact version before dispatching any persisted gate or asking another agent session or human to read a reusable verification subject.

A Verifier that returns a `stale-base` block returned no verdict: {!% require_skill 'spec-tree:sync-base' %!} Then re-establish the deterministic results on the rebased head, checkpoint, and dispatch again. After a rejected audit or valid review finding, repair the defect class, rerun deterministic verification, and create a new checkpoint commit before redispatch. Append the rejection to the record's `priorRejections` — Verifier, exact head, finding identifiers, defect classes, failed repair invariant, root cause, widened repair rule, and same-class scan — and redispatch only once the new head's record proves every rejection resolved. Preserve the earlier checkpoint identity while its run remains prior context; do not amend the audited commit in place.

</verification_checkpoint>

<result_carryover>

Each Verifier result is preserved once where that Verifier's own skill records it — the review journal for `changes-reviewer`, the `spx verification run` record for `implementation-auditor`, the returned structured verdict for every Auditor that returns one. What the flow carries forward from there is the bounded projection `/merging-standards` `<verification_result_projection>` defines: the result reference or raw run token, exact head, verdict, finding identifiers, defect classes, and next required action.

Reopen the complete result by reference when a finding needs exact detail. Never re-paste a complete Verifier payload into a later step, a queue transition to the next node, or the closeout.

</result_carryover>

<evidence_auditor_gate>

Two selectors run side by side, and neither subsumes the other. Malleability selects how much of the evidence chain the changeset must verify — the numbered evidence gates and the whole-changeset review. Output kind selects which artifact auditors judge the artifacts the changeset actually contains, through `<lane_table>`. The flow owes the union of the two selections.

Read every touched node's `malleability` from its spec front matter; an absent field means `implementation`. Select the numbered evidence gates from the least malleable touched node: the deterministic lane always; Step 9 for `verification` or `implementation`; Steps 6, 8, and 8a for `implementation` only. Product and outcome-record changes select the deterministic lane and Step 9 regardless. Step 4 remains independent of malleability and runs whenever a decision changed.

When Step 8a is selected, run the applicable artifact-type evidence auditors over the stabilized diff at Step 8a after every preceding selected lane has completed. This gate applies to node-local and cross-node changes. It is separate from the Step 6 evidence audit: Step 6 checks the test and eval evidence authored for the target node at that checkpoint in the code or test-evidence flow; Step 8a checks every evidence artifact the final changeset would publish.

Run deterministic verification first. Bring local validation, tests, and required eval runs to passing for the touched scope before dispatching evidence auditors. An evidence auditor reads and judges evidence quality; it never runs deterministic verification.

Dispatch `{{! subagent_name('spec-tree', 'test-evidence-auditor') !}}` during Step 8a when the diff creates or modifies any `[test]` assertion, linked test file, or test-infrastructure artifact imported by a linked test. For each affected governing node, pass only its canonical node path. The invoked audit discovers the assertions, linked tests, and complete evidence chain. If the auditor returns `REJECTED`, `UNKNOWN`, a failing row, an unknown row, or a reject finding, fix the evidence defect class, re-run deterministic verification, and re-dispatch Step 8a.

Dispatch `{{! subagent_name('spec-tree', 'eval-evidence-auditor') !}}` during Step 8a when the diff creates or modifies any `[eval]` assertion, `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, or producer artifact for an eval-backed assertion. For each affected governing node, pass only its canonical node path. The invoked audit discovers the assertions, eval artifacts, and producers. If the auditor returns `FAIL`, `UNKNOWN`, a failing row, an unknown row, or a reject finding, fix the evidence defect class, re-run the required eval evidence, and re-dispatch Step 8a.

Before dispatching an applicable evidence auditor, apply `<verification_checkpoint>`; carry each verdict forward under `<result_carryover>`. When both evidence classes changed, dispatch both auditors against the same checkpoint. Step 8a completes only after every applicable evidence-auditor verdict is clean on the exact committed diff it reviews. The artifact-auditor gate is the Output-kind selector's gate rather than part of the numbered evidence selection. `<lane_table>` selects it from the Output kinds the changeset contains, and each artifact auditor runs once over the complete changed surface for its kind, against the same `<verification_checkpoint>` head, after that row's deterministic lane and before the terminal full gate, merge, and completion. Only the numbered evidence gates precede Step 9; an artifact auditor is never a review-dispatch predicate. The skill row dispatches `{{! subagent_name('instructions', 'skill-auditor') !}}`, the prose row dispatches `{{! subagent_name('prose', 'prose-auditor') !}}`, the spec row dispatches `{{! subagent_name('spec-tree', 'spec-auditor') !}}`, and the decision row dispatches `{{! subagent_name('spec-tree', 'adr-auditor') !}}` or `{{! subagent_name('spec-tree', 'pdr-auditor') !}}`; the skill and prose auditors run when their plugins are installed. Malleability neither selects nor deselects an artifact auditor: a `spec`-malleable node that changes a skill still owes the skill auditor, because that auditor judges the artifact in front of it and reads no node's evidence chain, while an implementation-malleable node that changes no skill owes no skill auditor however hard its numbered gates are.

</evidence_auditor_gate>

<skill_map>

This map is the code row's language-specific flow. Steps 0–2, 9, and 10 are language-independent. Apply the conditional steps through their owning workflow steps and `<lane_table>`.

| Step | Purpose                 | TypeScript                                                                                                                          | Python                                          | Rust                                               | Go                                             |
| ---- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------- | ---------------------------------------------- |
| 0    | Select the slice        | {!% require_skill 'spec-tree:slice' %!}                                                                                             | same                                            | same                                               | same                                           |
| 1    | Load methodology        | {!% require_skill 'spec-tree:understand' %!}                                                                                        | same                                            | same                                               | same                                           |
| 2    | Load context            | Use skill `spec-tree:contextualize` for `{full-spx-node-path}`.                                                                     | same                                            | same                                               | same                                           |
| 3    | Author                  | {!% require_skill 'typescript:architect-typescript' %!}                                                                             | {!% require_skill 'python:architect-python' %!} | {!% require_skill 'rust:architect-rust' %!}        | {!% require_skill 'go:architect-go' %!}        |
| 4    | Architecture audit      | `{{! subagent_name('spec-tree', 'adr-auditor') !}}` or `{{! subagent_name('spec-tree', 'pdr-auditor') !}}` agent                    | same                                            | same                                               | same                                           |
| 5    | Establish evidence      | {!% require_skill 'spec-tree:verify' %!}                                                                                            | same                                            | same                                               | same                                           |
| 6    | Evidence audit          | `{{! subagent_name('spec-tree', 'test-evidence-auditor') !}}`, `{{! subagent_name('spec-tree', 'eval-evidence-auditor') !}}` agents | same                                            | same                                               | same                                           |
| 7    | Implement               | {!% require_skill 'typescript:code-typescript' %!}                                                                                  | {!% require_skill 'python:code-python' %!}      | {!% require_skill 'rust:code-rust' %!}             | {!% require_skill 'go:code-go' %!}             |
| 7a   | Simplify implementation | `{{! subagent_name('typescript', 'typescript-simplifier') !}}`                                                                      | no declared simplifier                          | `{{! subagent_name('rust', 'rust-simplifier') !}}` | `{{! subagent_name('go', 'go-simplifier') !}}` |
| 8    | Implementation audit    | `{{! subagent_name('spec-tree', 'implementation-auditor') !}}` agent                                                                | same                                            | same                                               | same                                           |
| 8a   | Evidence-auditor gates  | `{{! subagent_name('spec-tree', 'test-evidence-auditor') !}}`, `{{! subagent_name('spec-tree', 'eval-evidence-auditor') !}}` agents | same                                            | same                                               | same                                           |
| 9    | Whole-changeset review  | `{{! subagent_name('spec-tree', 'changes-reviewer') !}}` agent                                                                      | same                                            | same                                               | same                                           |
| 10   | Merge                   | {!% require_skill 'spec-tree:merge' %!}                                                                                             | same                                            | same                                               | same                                           |

Invoke the exact skill or agent surface shown. Never substitute, skip, or reorder.

</skill_map>

<workflow>

<step number="0" name="Select the slice" frequency="only for a plan or proposal">

When the work is described as a plan or proposal rather than a specific node or queue, per `<invocation_modes>`: {!% require_skill 'spec-tree:slice' %!} Its node set becomes the work queue. Skip this step for a specific node or an `spx/EXCLUDE` list.

</step>

<step number="1" name="Load methodology" frequency="once per session">

{!% require_skill 'spec-tree:understand' %!}

This loads the spec-tree methodology — node types, assertion formats, durable map rules. Skip if `SPEC_TREE_FOUNDATION` marker is already present in this session.

**Do not proceed until complete.**

</step>

<step number="2" name="Load work item context" frequency="every node">

Invoke `/contextualize` with the canonical full `spx/...` node path from the work queue.

Load the full context hierarchy for the specific node — parent chain, sibling nodes, applicable decisions, assertions.

**Repeat for every new node.** Do not reuse context from a previous node.

**Do not proceed until complete.**

</step>

<step number="3" name="Author">

Load and run the authoring skill of every row `<lane_table>` selected. For the code row, invoke the architecting skill for the detected language from `<skill_map>` and produce the ADRs the work item requires before audit. Each other selected row loads its own:

- Test evidence: {!% require_skill 'spec-tree:test' %!} {!% require_skill 'spec-tree:test-evidence-standards' %!}
- Spec or decision: {!% require_skill 'spec-tree:author' %!}
- Skill: {!% require_skill 'instructions:create-skill' %!} {!% require_skill 'instructions:skill-standards' %!} {!% require_skill 'instructions:agent-prompt-standards' %!}
- Prose: {!% require_skill 'prose:author-prose' %!} {!% require_skill 'prose:prose-standards' %!}

A row authors only the artifacts its own skill owns. Step 5 is the single owner of verification routing for every row — no row dispatches `spec-tree:verify`, or the test work it routes, here.

Before the architecture audit, invoke `/verify` separately for every new or changed ADR/PDR path. This moves each decision rule into its canonical verification subsection and supplies that subsection's tag before the auditor judges the decision. Keep target-node assertion routing in Step 5; this pre-audit decision routing creates no executable evidence link inside the decision record.

</step>

<step number="4" name="Architecture audit" gate="true">

When a decision changed, dispatch its configured decision Auditor with only the decision path: `{{! subagent_name('spec-tree', 'adr-auditor') !}}` for an ADR or `{{! subagent_name('spec-tree', 'pdr-auditor') !}}` for a PDR. The invoked audit discovers its governing node and committed changeset; `audit-adr` additionally discovers implementation-language partitions and composes each applicable `audit-{lang}-architecture` concern inside its isolated agent session. Require the Auditor's structured JSON verdict. Skip Step 4 when no decision changed.

When the scope is cross-node (see `<scope_detection>`), enumerate the decisions governing every affected surface across the whole changeset and dispatch each decision path separately. This gate passes only when every required decision audit approves.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`; carry its verdict forward under `<result_carryover>`.

**REJECTED -> fix the defect class -> re-dispatch this step.** Loop until APPROVED.

</step>

<step number="5" name="Establish evidence">

{!% require_skill 'spec-tree:verify' %!} Run it for every selected row whose changed declaration requires verification routing. It selects each assertion's verification type, routes selected test work through `/test` to each applicable installed language specialist, routes selected evaluate work through its own eval routing, and records pathless audit requirements without producing their verdict.

Establish every selected path-bearing evidence definition before implementation. When `/verify` selects test, the linked tests exist before implementation. When it selects evaluate, the eval definition, cases, prompt, and producer contract exist before implementation. A pathless audit selection records the isolated-verifier requirement and creates no preimplementation artifact.

</step>

<step number="6" name="Evidence audit" gate="true">

When the least malleable touched node is `implementation`, dispatch the auditor matching every path-bearing evidence artifact Step 5 created or changed. Otherwise skip Step 6.

- For test evidence, dispatch `{{! subagent_name('spec-tree', 'test-evidence-auditor') !}}` with only the canonical governing node path. The invoked audit discovers its assertions and complete test-evidence chain, then detects and composes the applicable `audit-{lang}-tests` concern inside its isolated agent session.
- For eval evidence, dispatch `{{! subagent_name('spec-tree', 'eval-evidence-auditor') !}}` with only the canonical governing node path. The invoked audit discovers its `[eval]` assertions, eval artifacts, and real producers. Require the audit-eval-evidence JSON verdict.
- A pathless audit requirement creates no authoring artifact for Step 6. Its isolated verifier remains the workflow that produces the eventual audit verdict.

When the scope is cross-node (see `<scope_detection>`), enumerate every governed node whose current linked test or eval evidence the change creates, modifies, or invalidates. Dispatch only each canonical node path, once per governed node and evidence type, in parallel when independent. Step 6 passes only when every applicable dispatched audit approves. A singular-node audit receives one node path; Step 8a covers the final changed evidence set, and Step 9 reviews the whole changeset when malleability selects it.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`; carry its verdict forward under `<result_carryover>`.

**A rejection -> fix the defect class -> re-dispatch this step.** Loop until every dispatched auditor passes: `APPROVED` from the test-evidence auditor, and `overall: PASS` with no `FAIL` or `UNKNOWN` row from the eval-evidence auditor.

</step>

<step number="7" name="Implement">

For the code row, invoke the coding skill for the detected language. Other rows complete their artifact authoring through the skill selected in Step 3 and skip this step.

Write implementation code, then run every applicable deterministic check selected in Step 5: selected tests pass and selected evals meet their declared completion threshold. Preserve each pathless audit requirement for its isolated verifier; never fabricate a test artifact for it.

</step>

<step number="7a" name="Simplify implementation">

For a code row in Go, Rust, or TypeScript, dispatch the configured simplifier selected in `<skill_map>` after Step 7. Python and changesets without a code row skip this step. Never infer another subagent from a language name.

Before dispatch, require a clean worktree. When it is dirty: {!% require_skill 'spec-tree:commit-changes' %!} Record the full committed head. Pass only `HEAD`, or the explicit three-dot range used for the selected base. The invoked language skill independently selects the changed implementation and its governing evidence. Run one simplifier at a time, with no concurrent writer to its implementation scope.

Require the skill's JSON result with `status`, `reason`, `target`, `base`, `head`, `scope`, `changed_paths`, `changes`, `evidence`, `verification`, `blockers`, and `recovery`. Check the returned target and full head against the dispatched subject, inspect every retained edit and command result, and apply the result contract:

- `simplified`: inspect the retained patch for scope and behavior preservation. Complete any still-required deterministic checks, then checkpoint every resulting edit before Step 8. Preserve the successful command results against that exact content; do not repeat commands whose subject is unchanged.
- `unchanged`: require no retained edit and a reason explaining the empty scope or absence of a safe improvement, then continue.
- `blocked` or `failed`: preserve the complete prerequisite or verification diagnostic and recovery outcome; stop this node before Step 8. Repair the named prerequisite or implementation through its owning workflow. A new simplifier invocation requires a repaired, verified, committed subject and follows the same one-call contract.

An absent or malformed result follows `<launch_contract>`. A simplification result supplies no independent audit approval. Step 8 and every applicable evidence and review gate remain required. If later repair changes implementation, repeat Step 7a on the repaired committed subject before its final audits.

</step>

<step number="8" name="Code audit" gate="true">

When the least malleable touched node is `implementation` and the code row is selected, dispatch `{{! subagent_name('spec-tree', 'implementation-auditor') !}}` with only the committed scope selector: `HEAD` for the current branch, or an explicit three-dot range for a selected base. The invoked skill discovers the repository, governing nodes, verification context, and language partitions; the wrapper supplies its own run-driver identity internally. Otherwise skip Step 8.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — Step 4 audits every affected decision while Step 6 fans out across every affected governed evidence node and type. Those audit lenses remain necessary but insufficient when malleability also selects Step 9, whose distinct whole-diff review catches cross-cutting effects no single audit lens catches.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`; carry its verdict forward under `<result_carryover>`.

The implementation-auditor composes the installed `audit-{lang}-{code|tests|architecture}` concern skills and records the run through `spx verification run`. Do not invoke those concern skills directly from this workflow. Read the returned rendered projection: its `terminalStatus` is the Step 8 verdict — `approved` passes, `rejected` requires repair, and a missing projection or `BLOCKED` result blocks the gate. A command-failure `BLOCKED` result is complete only when it carries the run token or `not-started`, exact command, payload source, payload key, exit code, and stderr, including a failed preparation command. A missing-input diagnostic carries `runToken: not-started` and the exact missing selector or identity. A pre-run skill-load `BLOCKED` result is complete only when it carries run token `not-started`, required skill `spec-tree:audit-implementation`, and the exact load or availability failure.

**Projection `terminalStatus: rejected` -> fix the defect class; complete `BLOCKED` diagnostic -> repair the named preparation, input, command, payload, installation, or skill-load boundary.** Verify and checkpoint the changed subject before a new audit. A failed launch or unusable result follows `<launch_contract>` immediately.

</step>

<step number="8a" name="Evidence and artifact auditor gates" gate="true">

Run each gate family `<evidence_auditor_gate>` selected. The numbered evidence gate additionally requires that the stabilized diff create or modify a `[test]` assertion, linked test file, imported test-infrastructure artifact, `[eval]` assertion, eval artifact, or eval-backed producer artifact.

</step>

<step number="9" name="Whole-changeset review" gate="true" condition="malleability selects review">

Run this step when the least malleable touched node is `verification` or `implementation`. Product and outcome-record changes also run it regardless of malleability. Skip it for a `spec`-malleable changeset containing neither product nor outcome-record changes.

Before invoking the review, apply `<verification_checkpoint>` and satisfy exactly the review-dispatch readiness predicates that `/merging-standards` declares. Do not turn another apply-flow gate into an additional review-dispatch predicate. Selected evidence and artifact audits remain blocking gates for the terminal full gate, merge, and completion, and their verdicts stay bound to the exact committed diff they reviewed.

Dispatch `{{! subagent_name('spec-tree', 'changes-reviewer') !}}` over the full committed changeset, passing only the raw scope token: `HEAD` for the current branch or an explicit committed range for a selected base. Never add a prose prompt, severity filter, or emphasis instruction. Collect the final message through the native result-collection capabilities and require it to be the raw review run token. A tool failure, terminal result without a final message, or non-token final message blocks Step 9 and follows `<launch_contract>`.

{!% require_skill 'spec-tree:project-run-journal' %!} Then inspect the returned token through its `render_review_run.py` helper exactly as that skill directs. Treat the helper output as the inspection projection of the sealed journal prefix; the sealed prefix remains the only review result. Read the rendered terminal status, full head/base identity, scope coverage, blocking/debt counts, and findings before deciding whether Step 9 converged. Carry the review forward as the bounded projection `<result_carryover>` defines.

The selected artifact gates inspect through distinct audit lenses; they do not see every cross-node effect — a stale reference a rename left in a sibling, dead code a move orphaned, or a spec a consolidation made false. The whole-diff review catches those effects.

Apply `<stabilized_diff_rule>` before invoking the review. Fix every valid finding in the rendered sealed projection, including every in-scope same-class instance found by the same-class sweep, then verify and checkpoint the changed subject before reviewing it. A missing or unusable raw token follows `<launch_contract>`. If rendering a valid token fails, preserve that token and diagnose the inspection failure through `/project-run-journal`; never launch another reviewer to replace the recorded result. The gate remains blocked until the sealed result is readable and every valid finding is resolved.

</step>

<step number="10" name="Merge" condition="the change is destined for the default branch">

Skip this step only when the user explicitly scoped the work to a proposal, analysis, review, or local-only change — then state that scope and stop. For every other change, the work is destined for the default branch, and the flow is NOT complete at Step 9.

Local readiness is not delivered value. A Step 8 projection with `terminalStatus: approved`, a converged Step 9 review, passing tests, a clean working tree, and a local commit ahead of base are progress. Delivered value is the change merged to the default branch on origin.

{!% require_skill 'spec-tree:merge' %!} It selects the transport and drives the change to the default branch under its own authority gates — this flow neither re-implements the merge protocol nor re-decides those gates. The `/merge` lifecycle owns commit, push, integration review, and merge.

The flow is complete only when the change reaches the default branch on origin, or an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base is never the endpoint for default-branch work.

</step>

</workflow>

<terminal_full_gate>

When the repository overlay, governing node, or merge lifecycle requires a full deterministic bundle, run the repository's declared full deterministic gate exactly once at the terminal verification point: after every selected Step 4, 6, 8, and 8a evidence gate, every selected artifact-auditor gate, and Step 9 when selected have converged on the same clean committed head. Do not run that full gate before those agentic checks, inside an auditor, or concurrently with another heavy command.

If the full deterministic gate fails, fix the reported defect, run the focused touched-scope checks, create a new checkpoint commit, rerun every invalidated agentic gate, and only then run the declared full gate again. A successful full gate is invalidated by any subsequent source, test, spec, generated-output, or configuration change.

</terminal_full_gate>

<review_gates>

Select every gate as `<evidence_auditor_gate>` defines. Step 4 is a blocking audit whenever a decision changed, independent of malleability. Selected Steps 6, 8, and 8a are blocking audit gates, and every selected artifact-auditor gate is blocking. Steps 4, 6, 8a, and the artifact-auditor gates emit verdicts from their Auditor contracts. Step 8 returns an `spx verification run` token and rendered projection whose `terminalStatus` is authoritative; a `BLOCKED` result must relay a complete diagnostic from the implementation-auditor contract as described in Step 8. Selected Step 9 is a blocking whole-changeset review. Step 10 is the terminal lifecycle boundary for default-branch work.

- Before starting Step 5: when a decision changed, require Step 4's workflow-local result to be `APPROVED`; otherwise skip Step 4.
- Before starting Step 7: when Step 6 is selected, require `APPROVED` from the test-evidence auditor and `overall: PASS` with no `FAIL` or `UNKNOWN` row from the eval-evidence auditor; otherwise skip Step 6.
- Before considering the code row complete: when Step 8 is selected, require its rendered projection to carry `terminalStatus: approved`; otherwise skip Step 8.
- Before selected Step 8 for a Go, Rust, or TypeScript code row, require Step 7a's usable `simplified` or `unchanged` result for the implementation being verified, with every resulting edit inspected, verified, and committed.
- Before starting Step 9: require exactly the review-dispatch readiness predicates that `/merging-standards` declares; apply names no additional readiness predicate.
- Before the terminal full deterministic gate, Step 10, or completion: require every artifact Auditor selected by `<lane_table>` and every evidence Auditor selected by `<evidence_auditor_gate>` to carry a clean verdict over the exact committed diff.
- Before declaring the flow complete: when Step 9 is selected, require a raw review run token from the native final result and a rendered sealed projection from `/project-run-journal`. If no invocation has occurred, invoke Step 9. A failed invocation or unusable final result follows `<launch_contract>`; a blocked inspection preserves its token; valid findings follow the repair workflow.
- Before invoking `/merge` when a full deterministic bundle is required: confirm the repository-declared full deterministic gate ran after every applicable agentic gate and against the current clean committed head. If any source, test, spec, generated-output, or configuration file changed afterward, rerun the invalidated agentic gates before running the declared full gate again.
- Before declaring the flow complete for default-branch work: confirm the change reached the default branch on origin through Step 10's `/merge`, or that the user scoped the work to a proposal, analysis, review, or local-only change, or that an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base does not satisfy this — invoke Step 10.

For completed verdicts of `REJECTED`, `UNKNOWN`, or a complete `BLOCKED` diagnostic at Steps 4 and 6; projection `terminalStatus: rejected` or a complete blocked diagnostic at Step 8; or valid findings at Step 9: fix the defect class, verify and checkpoint the changed subject, then audit that subject. Use Step 8's complete blocked diagnostic to identify the failed command, payload, installation, or skill-load boundary. Launch failures, unusable results, and blocked inspection of a valid review token follow `<launch_contract>` and Step 9; they never enter this relaunch loop.

One stop rule has two triggers. A Verifier rejection in a defect class that a prior repair claimed to close stops the queue at any pass until a widened repair, same-class scan, and governing-workflow, standard, or source-contract amendment land, per `<stabilized_diff_rule>`. Otherwise, a second consecutive completed rejected, unknown, or blocked Verifier verdict on one gate (Steps 4, 6, 8, 8a), or a second consecutive completed Step 9 review with unresolved valid findings, stops the flow. A launch with no run token and no verdict is no result under `<launch_contract>` and counts as neither a pass nor a rejection. On either trigger, surface one structured question through `{{! tool('ask_user') !}}` carrying the gate, the classes that survived, the repeated-class check, the latest verdict and outstanding findings, and one proposal: split, track, or stop. A failed launch or unusable result follows `<launch_contract>` and never enters the verdict count.

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
- Each applicable architecture and test-evidence auditor returns `APPROVED`; each applicable eval-evidence auditor returns JSON `overall: PASS` with no `FAIL` or `UNKNOWN` row; and each implementation-audit run renders `terminalStatus: approved` for the exact committed subject.
- A changeset that selects Step 9 carries a raw review run token whose sealed projection renders successfully, with every valid finding fixed, including every in-scope same-class instance; unbacked findings are dropped.
- `git rev-parse HEAD` matches the final gate subject and `git status --porcelain` is empty.
- The requested delivery boundary has observable completion: default-branch work has reached the default branch on origin through `/merge`'s selected transport and every declared release action reports success or no-op; proposal, analysis, review, or local-only work reaches its explicitly selected boundary; an explicit lifecycle gate reports its blocking token only after no independent action remains.

</success_criteria>
