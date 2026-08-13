---
name: apply
description: >-
  ALWAYS invoke this skill before implementing any spec-tree work item.
  NEVER write code, tests, or architecture for a spec-tree node without this skill.
argument-hint: "[full-spx-node-path | plan-or-proposal]"
allowed-tools: Read, Edit, Skill, Agent, AskUserQuestion, Bash(git status:*), Bash(git rev-parse:*), Bash(git diff:*), Bash(spx validation:*), Bash(spx spec status:*), Bash(spx test:*), Bash(just test:*), Bash(just check:*), Bash(just check-full:*), Bash(just verify:*), Bash(just validate:*), Bash(pnpm test:*), Bash(pnpm run test:*), Bash(pnpm run check:*), Bash(pnpm run lint:*), Bash(pnpm run typecheck:*), Bash(pnpm run validate:*), Bash(pnpm run verify:*), Bash(npm test:*), Bash(npm run test:*), Bash(npm run check:*), Bash(npm run lint:*), Bash(npm run typecheck:*), Bash(npm run validate:*), Bash(npm run verify:*), Bash(yarn test:*), Bash(yarn run test:*), Bash(yarn run check:*), Bash(yarn run lint:*), Bash(yarn run typecheck:*), Bash(yarn run validate:*), Bash(yarn run verify:*), Bash(bun test:*), Bash(bun run test:*), Bash(bun run check:*), Bash(bun run lint:*), Bash(bun run typecheck:*), Bash(bun run validate:*), Bash(bun run verify:*), Bash(uv run pytest:*), Bash(pytest:*), Bash(cargo test:*), Bash(cargo check:*), Bash(cargo clippy:*), Bash(cargo fmt --check:*), Bash(go test:*), Bash(go vet:*), Bash(make test:*), Bash(make check:*), Bash(make verify:*), Bash(make validate:*)
---

<objective>
A spec-tree work item implemented and ready for the delivery boundary the user requested.

</objective>

<invocation_modes>

The raw invocation string `$ARGUMENTS` controls what runs before the per-node flow below. Parse it exactly once before Step 0:

- `$ARGUMENTS` containing a canonical full `spx/...` node path → the work queue is that single node.
- Empty `$ARGUMENTS` → determine the work from the conversation. If nothing is clear, complete Step 1 first — invoke `/understand` when the live `SPEC_TREE_FOUNDATION` marker is absent — then read `spx/EXCLUDE`, whose entries are relative to `spx/`, and prefix each non-comment, non-blank entry with `spx/` before adding it to the work queue. Never access `spx/EXCLUDE` before the foundation is live, and never pass a bare entry to `/contextualize`. If no work is found, report "Nothing to apply" and stop.

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

1. Changes may remain uncommitted until another agent session or human is expected or asked to read them. Before dispatching an audit or review, run the touched-scope deterministic verification required by the repository overlay when preparing a gate. Do not run an aggregate gate whose generated-output drift check requires committed `src/` and `dist/` files before creating the checkpoint.
2. When the relevant tracked or untracked files differ from `HEAD`, invoke `/commit-changes` before dispatch to commit the exact current version regardless of whether the latest verification state is `passing`, `failing`, or `not-run`; preserve that state in the checkpoint result. After any further change, commit the new version before another audit or review.
3. Confirm the worktree is clean and record the checkpoint's full `HEAD` commit ID.
4. Dispatch the gate only when the required deterministic verification is `passing`, against the committed `<base>..<head>` scope. A `failing` or `not-run` checkpoint remains valid local history for recovery and collaboration while withholding gate dispatch. Do not supply a live file list for a gating run. The repository's declared full deterministic gate, when required, runs once against the clean checkpoint head as a later lifecycle step rather than before every checkpoint.

An audit or review over modified or untracked files is advisory. It may provide early feedback, but it never satisfies a Step 4, Step 6, Step 8, evidence-auditor, Step 9, or merge-readiness predicate. Commit the exact version before dispatching any persisted gate or asking another agent session or human to read a reusable verification subject.

After a rejected audit or valid review finding, repair the defect class, rerun deterministic verification, and create a new checkpoint commit before redispatch. Preserve the earlier checkpoint identity while its run remains prior context; do not amend the audited commit in place.

</verification_checkpoint>

<evidence_auditor_gate>

After Step 8, run the applicable artifact-type evidence auditors over the stabilized diff. This gate applies to node-local and cross-node changes. It is separate from the Step 6 evidence audit: Step 6 checks the test and eval evidence authored for the target node at that checkpoint in the TDD flow; Step 8a checks every evidence artifact the final changeset would publish.

Run deterministic verification first. Bring local validation, tests, and required eval runs to passing for the touched scope before dispatching evidence auditors. An evidence auditor reads and judges evidence quality; it never runs deterministic verification.

Dispatch `test-evidence-auditor` during Step 8a when the diff creates or modifies any `[test]` assertion, linked test file, or test-infrastructure artifact imported by a linked test. Include the governing node, assertion text or spec path plus assertion headings, and the test files in the dispatch prompt. If the auditor returns `REJECTED`, `UNKNOWN`, a failing row, an unknown row, or a reject finding, fix the evidence defect class, re-run deterministic verification, and re-dispatch Step 8a.

Dispatch `eval-evidence-auditor` during Step 8a when the diff creates or modifies any `[eval]` assertion, `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, or producer artifact for an eval-backed assertion. Include the governing node, assertion text or spec path plus assertion headings, the eval artifacts, and the producer artifacts in the dispatch prompt. If the auditor returns `FAIL`, `UNKNOWN`, a failing row, an unknown row, or a reject finding, fix the evidence defect class, re-run the required eval evidence, and re-dispatch Step 8a.

Before dispatching an applicable evidence auditor, apply `<verification_checkpoint>`. When both evidence classes changed, dispatch both auditors against the same checkpoint. Step 8a completes only after every applicable evidence-auditor verdict is clean on the exact committed diff it reviews.

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
| 5    | Establish evidence       | `Skill("spec-tree:verify")`                                      | same                        | same                      |
| 6    | Evidence audit           | `test-evidence-auditor`, `eval-evidence-auditor` agents          | same                        | same                      |
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

Before the architecture audit, invoke `/verify` separately for every new or changed ADR/PDR path. This moves each decision rule into its canonical verification subsection and supplies that subsection's tag before the auditor judges the decision. Keep target-node assertion routing in Step 5; this pre-audit decision routing creates no executable evidence link inside the decision record.

</step>

<step number="4" name="Architecture audit" gate="true">

Classify the ADR itself before dispatch: use `language-neutral` when the decision constrains no implementation language; otherwise enumerate every implementation-language partition the decision constrains. Derive the partitions from the ADR's governed implementation surface and the committed audit scope, preserving every language for a cross-language decision instead of collapsing the classification to the flow's detected language.

Dispatch `adr-auditor` with the ADR path, governing node path, exact committed audit scope chosen in `<scope_detection>`, and `Scope classification: language-neutral` or `Scope classification: implementation-language partitions: <comma-separated languages>`. Require only the structured JSON verdict specified by `audit-adr`. The auditor composes each declared language's `audit-{lang}-architecture` concern inside its isolated agent session.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — an architecture regression the change introduced in a file the node does not own is invisible to a per-node audit.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`.

**REJECTED -> fix the defect class -> re-dispatch this step.** Loop until APPROVED.

</step>

<step number="5" name="Establish evidence">

Invoke `/verify` for the target node. It selects each assertion's verification type and routes selected test work through `/test` to the detected language specialist. It routes eval work through `/eval` when that capability is installed and records pathless audit requirements without producing their verdict.

Establish every selected path-bearing evidence definition before implementation. When `/verify` selects test, the linked tests exist before implementation. When it selects evaluate, the eval definition, cases, prompt, and producer contract exist before implementation. A pathless audit selection records the isolated-verifier requirement and creates no preimplementation artifact.

</step>

<step number="6" name="Evidence audit" gate="true">

Dispatch the auditor matching every path-bearing evidence artifact Step 5 created or changed:

- For test evidence, dispatch `test-evidence-auditor` with the router-owned prompt contract: repository path, governing node, assertion text or spec path plus assertion headings, and linked test files. The auditor detects and composes the applicable `audit-{lang}-tests` concern inside its isolated agent session.
- For eval evidence, dispatch `eval-evidence-auditor` with the governing node, `[eval]` assertions, eval definition, materialized prompt, cases, history, and real producer artifacts. Require the audit-eval-evidence JSON verdict.
- A pathless audit requirement creates no authoring artifact for Step 6. Its isolated verifier remains the workflow that produces the eventual audit verdict.

When the scope is cross-node (see `<scope_detection>`), enumerate every governed node whose current linked test or eval evidence the change creates, modifies, or invalidates. Dispatch one router-owned singular-node prompt per governed node and evidence type, in parallel when independent. Step 6 passes only when every applicable dispatched audit approves. Never pass a whole changeset as one singular `Governing node` prompt; Step 8a covers the final changed evidence set and Step 9 reviews the whole changeset.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`.

**REJECTED -> fix the defect class -> re-dispatch this step.** Loop until APPROVED.

</step>

<step number="7" name="Implement">

Invoke the coding skill for the detected language.

Write implementation code, then run every applicable deterministic check selected in Step 5: selected tests pass and selected evals meet their declared completion threshold. Preserve each pathless audit requirement for its isolated verifier; never fabricate a test artifact for it.

</step>

<step number="8" name="Code audit" gate="true">

Dispatch the `implementation-auditor` agent with the canonical request fields: repository path, exact committed changeset scope, governing node paths, deterministic verification already run, and run-driver identity. The wrapper and orchestration skill derive language partitions from that scope.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — Step 4 audits the committed scope while Step 6 fans out across every affected governed evidence node and type. Those audit lenses remain necessary but insufficient, so the distinct whole-diff review in Step 9 stays required for cross-cutting effects no single audit lens catches.

Before invoking the audit, apply `<stabilized_diff_rule>` and `<verification_checkpoint>`.

The implementation-auditor composes the installed `audit-{lang}-{code|tests|architecture}` concern skills and records the run through `spx verification run`. Do not invoke those concern skills directly from this workflow. Read the returned rendered projection: its `terminalStatus` is the Step 8 verdict — `approved` passes, `rejected` requires repair, and a missing projection or `BLOCKED` result blocks the gate. A command-failure `BLOCKED` result is complete only when it carries the run token or `not-started`, exact command, payload source, payload key, exit code, and stderr. A pre-run skill-load `BLOCKED` result is complete only when it carries run token `not-started`, required skill `spec-tree:audit-implementation`, and the exact load or availability failure.

**Projection `terminalStatus: rejected` -> fix the defect class; command-failure `BLOCKED` -> repair the failed command or payload boundary; pre-run skill-load `BLOCKED` -> repair the `spec-tree:audit-implementation` installation or load boundary; then re-dispatch this step.** Loop until the rendered projection reports `terminalStatus: approved`.

</step>

<step number="8a" name="Evidence-auditor gates" gate="true" condition="the change creates or modifies test or eval evidence">

Run `<evidence_auditor_gate>` whenever the stabilized diff creates or modifies a `[test]` assertion, linked test file, imported test-infrastructure artifact, `[eval]` assertion, eval artifact, or producer artifact for eval-backed evidence. The condition applies whether the change is node-local or cross-node.

Skip this step only when the diff changes no test or eval evidence surface named by `<evidence_auditor_gate>`.

</step>

<step number="9" name="Whole-changeset review" gate="true" condition="the change touches files or specs beyond the target node">

Skip this step only when the entire diff is confined to the target node's own directory — its spec, its `tests/`, and the implementation files that node governs. The moment the work touches anything else — a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node — this step is REQUIRED before the flow may be declared complete.

Before invoking the review, confirm every applicable Step 8a evidence-auditor verdict is clean, then apply `<verification_checkpoint>`. The reviewer must see the same committed diff whose touched evidence artifacts passed their artifact-type evidence audits.

Dispatch `changes-reviewer` over the full committed changeset, passing only the raw scope token the runtime contract accepts — never a prose prompt, severity filter, or emphasis instruction. Collect the agent's final message through the typed wait capability and require it to be the raw review run token. A timeout, tool error, missing final status, or non-token final message blocks Step 9.

Invoke `/project-run-journal`, then inspect the returned token through its `render_review_run.py` helper exactly as that skill directs. Treat the helper output as the inspection projection of the sealed journal prefix; the sealed prefix remains the only review result. Read the rendered terminal status, full head/base identity, scope coverage, blocking/debt counts, and findings before deciding whether Step 9 converged.

The per-node gates in Steps 4, 6, and 8 inspect through distinct audit lenses; they do not see every cross-node effect — a stale reference a rename left in a sibling, dead code a move orphaned, or a spec a consolidation made false. The whole-diff review catches those effects.

Apply `<stabilized_diff_rule>` before invoking the review. Fix every valid finding in the rendered sealed projection, including every in-scope same-class instance found by the same-class sweep, then create a new checkpoint and re-run. **Missing raw token, blocked render, or unaddressed valid finding -> repair the blocked collection or fix the defect class -> re-run this step.** Loop until the rendered sealed review converges.

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

Steps 4, 6, 8, and applicable Step 8a are blocking audit gates. Steps 4, 6, and 8a emit verdicts from their auditor contracts. Step 8 returns an `spx verification run` token and rendered projection whose `terminalStatus` is authoritative; a `BLOCKED` result must relay either the complete SPX command-failure diagnostic or the complete pre-run `spec-tree:audit-implementation` load-failure diagnostic from the implementation-auditor contract. Step 9 is a blocking whole-changeset review gate that runs whenever the change reaches beyond the target node. Step 10 is the terminal lifecycle boundary for default-branch work — not a retry-loop gate, but a hard precondition for declaring the flow complete.

- Before starting Step 5: require Step 4's workflow-local result to be `APPROVED`. If it is absent or differs, stop and invoke or repair Step 4.
- Before starting Step 7: require Step 6's workflow-local result to be `APPROVED`. If it is absent or differs, stop and invoke or repair Step 6.
- Before considering implementation complete: inspect the Step 8 rendered projection. If `terminalStatus` is absent or differs from `approved`, stop — invoke or repair Step 8.
- Before starting Step 9, the terminal full deterministic gate, Step 10, or completion: if the diff touches a test or eval evidence surface named by `<evidence_auditor_gate>`, require a clean Step 8a verdict over the exact committed diff and invoke or repair Step 8a when that verdict is absent. When the diff touches no named evidence surface, skip Step 8a.
- Before declaring the flow complete: if the change touches anything beyond the target node, require a raw Step 9 review run token collected through the typed wait and a rendered sealed projection from `/project-run-journal`. If either is absent, blocked, or reports unaddressed valid findings, stop — invoke or repair Step 9.
- Before invoking `/merge` when a full deterministic bundle is required: confirm the repository-declared full deterministic gate ran after every applicable agentic gate and against the current clean committed head. If any source, test, spec, generated-output, or configuration file changed afterward, rerun the invalidated agentic gates before running the declared full gate again.
- Before declaring the flow complete for default-branch work: confirm the change reached the default branch on origin through Step 10's `/merge`, or that the user scoped the work to a proposal, analysis, review, or local-only change, or that an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base does not satisfy this — invoke Step 10.

On `REJECTED`, `UNKNOWN`, or `BLOCKED` at Steps 4 and 6; projection `terminalStatus: rejected` or a blocked result at Step 8; or a missing raw token, blocked journal render, or unaddressed valid finding at Step 9: fix the defect class, repair the failed collection boundary, or use Step 8's complete blocked diagnostic to repair the failed command, payload, installation, or skill-load boundary, then re-dispatch and inspect the new result.

**3 consecutive rejected, unknown, or blocked results on the same gate (Steps 4, 6, 8, 8a), or 3 consecutive Step 9 runs that still lack a valid rendered sealed result or surface unresolved valid findings -> STOP.** Surface the stuck gate to the user via `AskUserQuestion`: report the gate, its most recent verdict (for Step 9, the collection failure or outstanding findings), the same-class sweep already performed, and what did not resolve. A convergence loop that keeps reopening valid findings is a signal Claude's approach is unstable; refactor the approach before asking the same gate again.

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
- A cross-node changeset carries a raw Step 9 review run token whose sealed projection renders successfully, with every finding fixed, tracked as a separate larger concern, or dropped as unbacked.
- `git rev-parse HEAD` matches the final gate subject and `git status --porcelain` is empty.
- The requested delivery boundary has observable completion: default-branch work has reached the default branch on origin through `/merge`'s selected transport and every declared release action reports success or no-op; proposal, analysis, review, or local-only work reaches its explicitly selected boundary; an explicit lifecycle gate reports its blocking token only after no independent action remains.

</success_criteria>
