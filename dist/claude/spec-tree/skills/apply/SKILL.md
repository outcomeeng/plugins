---
name: apply
description: >-
  ALWAYS invoke this skill before implementing any spec-tree work item.
  NEVER write code, tests, or architecture for a spec-tree node without this skill.
---

<objective>
A work item implemented through the spec-tree TDD flow — its node declared, specified, and passing its tests with every audit gate APPROVED — and, for default-branch work, the change merged to the default branch on origin.

</objective>

<quick_start>

0. Plan the slice when the work is a plan or proposal, not a specific node or queue — invoke `/plan-slice` to select the observable slice whose node set becomes the work queue (see `<invocation_modes>`)
1. Load methodology (Step 1 — once per session)
2. Load work item context (Step 2 — every node)
3. Architect -> audit until APPROVED (Steps 3–4)
4. Test -> audit until APPROVED (Steps 5–6)
5. Implement -> audit until APPROVED (Steps 7–8)
6. Whole-changeset review when the change reaches beyond the target node (Step 9)
7. Merge — carry default-branch work through `/merge` until it reaches the default branch on origin (Step 10)

</quick_start>

<invocation_modes>

An optional argument controls what runs before the per-node flow below:

- `--agent [node-path]` → launch the `applier` agent (`Agent` tool, `subagent_type: spec-tree:applier`) on the node; it runs the per-node TDD flow (Steps 1–8, audit gates included) autonomously and returns a status report. Do not run those steps in the main context. The agent does not review the whole changeset or merge — on its return, continue with Step 9 (when the change is cross-node) and Step 10 over the resulting changeset.
- `[node-path]` → the work queue is that single node.
- no argument → determine the work from the conversation; if nothing is clear, read `spx/EXCLUDE` and queue every node path it lists (one per non-comment, non-blank line). If no work is found, report "Nothing to apply" and stop.

When the work is described as a plan or proposal rather than a specific node or queue, invoke `/plan-slice` first: it selects the next executable observable slice and produces the node set that becomes this flow's work queue. Skip the preflight when the queue is already a specific node or an `spx/EXCLUDE` list.

When the queue holds more than one node, order by numeric index prefix (lower first) — lower-indexed nodes constrain higher-indexed ones. For each node in order:

1. If it is listed in `spx/EXCLUDE`, remove its line first — the `spx` CLI then includes its tests in `spx test passing`.
2. Run Steps 1–9 on the node.
3. Commit via `/commit-changes`.
4. Proceed to the next node without stopping or asking, subject to the gate-retry limits in `<review_gates>`.

If a node's flow cannot reach an APPROVED/converged state within the gate retry limit, stop the queue, report the failed node and step, and leave the remaining nodes in `spx/EXCLUDE`. Step 10 (`/merge`) runs once over the whole changeset after the queue completes.

</invocation_modes>

<language_detection>

Before starting Step 3, determine the product language:

- `tsconfig.json` exists -> **TypeScript**
- `pyproject.toml` or `setup.py` exists -> **Python**
- Both exist -> check the spec node for language indicators, or ask the user

Use the detected language for ALL Steps 3–8. Do not switch mid-flow.

</language_detection>

<scope_detection>

Before starting Step 3, determine the change's scope — this determination governs every later gate:

- **Node-local** — the entire diff stays within the target node's own directory (its spec, its `tests/`, and the implementation files that node governs).
- **Cross-node** — the work touches anything else: a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node.

When the scope is cross-node, every audit gate — Steps 4, 6, and 8 — runs at **whole-changeset** scope, not only the target node, and Step 9 is REQUIRED before the flow may be declared complete. A per-node audit reads only the target node's files; it cannot see a regression the change introduced in a file the node does not own. Carry the determination through Steps 4, 6, and 8 — each gate step restates the scope requirement at its point of action.

</scope_detection>

<stabilized_diff_rule>

Before any audit gate or whole-changeset review runs, self-converge the diff: read the changed specs, tests, and implementation together; confirm the model is coherent; and fix obvious contradictions before asking an auditor or reviewer to find them. Audit gates confirm a stabilized design. They are not the design loop.

When a gate returns `REJECT` or a review surfaces a valid finding, treat it as evidence of a defect class. Read the touched node(s) — the files they govern — find same-class instances, and fix the class before re-running the gate. Same-class means the same rule, source contract, evidence pattern, lifecycle step, generated-source relationship, or architectural boundary. A patch to the cited line alone is sufficient only when the sweep proves the defect isolated.

Do not re-run a gate after every micro-edit. Batch the class fix, re-read the affected diff, then run the gate once on the stabilized tree. If repeated findings keep reopening the same design area, stop patching and refactor the model before the next gate.

</stabilized_diff_rule>

<skill_map>

Step 0 and Steps 1–2 are language-independent. Steps 3–8 use the detected language. Steps 9 and 10 are language-independent; Step 0 runs only when the work is described as a plan or proposal rather than a specific node or queue, Step 9 runs only when the change reaches beyond the target node, and Step 10 runs unless the work is explicitly scoped to a proposal, analysis, review, or local-only change.

| Step | Purpose                  | TypeScript                                              | Python                               |
| ---- | ------------------------ | ------------------------------------------------------- | ------------------------------------ |
| 0 §  | Plan the slice           | `Skill("spec-tree:plan-slice")`                         | same                                 |
| 1    | Load methodology         | `Skill("spec-tree:understand")`                         | same                                 |
| 2    | Load context             | `Skill("spec-tree:contextualize", args: "{node-path}")` | same                                 |
| 3    | Architect                | `Skill("architect-typescript")`                         | `Skill("architect-python")`          |
| 4    | Architecture audit       | `Skill("audit-typescript-architecture")`                | `Skill("audit-python-architecture")` |
| 5    | Write tests              | `Skill("test-typescript")`                              | `Skill("test-python")`               |
| 6    | Test audit               | `Skill("audit-typescript-tests")`                       | `Skill("audit-python-tests")`        |
| 7    | Implement                | `Skill("code-typescript")`                              | `Skill("code-python")`               |
| 8    | Code audit               | `Skill("audit-typescript")`                             | `Skill("audit-python")`              |
| 9    | Whole-changeset review † | `changes-reviewer` agent                                | same                                 |
| 10   | Merge ‡                  | `Skill("spec-tree:merge")`                              | same                                 |

§ Step 0 runs only when the work is described as a plan or proposal rather than a specific node or queue; it selects the observable slice whose node set becomes the work queue (see `<invocation_modes>`).
† Step 9 runs only when the change touches files or specs beyond the target node (see the step for the condition).
‡ Step 10 runs for any change destined for the default branch — skip only when the user explicitly scoped the work to a proposal, analysis, review, or local-only change (see the step).

**Invoke the exact Skill tool call shown.** Never substitute, skip, or reorder.

</skill_map>

<steps>

<step number="1" name="Load methodology" frequency="once per session">

Invoke `/understand`.

This loads the spec-tree methodology — node types, assertion formats, durable map rules. Skip if `SPEC_TREE_FOUNDATION` marker is already present in this session.

**Do not proceed until complete.**

</step>

<step number="2" name="Load work item context" frequency="every node">

Invoke `/contextualize` with the node path.

Load the full context hierarchy for the specific node — parent chain, sibling nodes, applicable decisions, assertions.

**Repeat for every new node.** Do not reuse context from a previous node.

**Do not proceed until complete.**

</step>

<step number="3" name="Architect">

Invoke the architecting skill for the detected language.

Produce the ADR(s) for the work item. The architecture must be complete before audit.

</step>

<step number="4" name="Architecture audit" gate="true">

Invoke the architecture audit skill for the detected language.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — an architecture regression the change introduced in a file the node does not own is invisible to a per-node audit.

Before invoking the audit, apply `<stabilized_diff_rule>`.

**REJECT -> fix the defect class -> re-invoke this step.** Loop until APPROVED.

</step>

<step number="5" name="Write tests">

Invoke the testing skill for the detected language.

Write tests for all assertions in the spec. Tests come before implementation — no exceptions.

</step>

<step number="6" name="Test audit" gate="true">

Invoke the test audit skill for the detected language.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — test evidence the change invalidated in a sibling node is invisible to a per-node audit.

Before invoking the audit, apply `<stabilized_diff_rule>`.

**REJECT -> fix the defect class -> re-invoke this step.** Loop until APPROVED.

</step>

<step number="7" name="Implement">

Invoke the coding skill for the detected language.

Write implementation code. All tests from Step 5 must pass.

</step>

<step number="8" name="Code audit" gate="true">

Invoke the code audit skill for the detected language.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — as Steps 4 and 6 already did at their gates. Widening the three per-node audits is necessary but not sufficient: each inspects through its own lens (architecture, test evidence, code), so the distinct whole-diff review in Step 9 remains required for cross-cutting effects no single audit lens catches.

Before invoking the audit, apply `<stabilized_diff_rule>`.

**REJECT -> fix the defect class -> re-invoke this step.** Loop until APPROVED.

</step>

<step number="9" name="Whole-changeset review" gate="true" condition="the change touches files or specs beyond the target node">

Skip this step only when the entire diff is confined to the target node's own directory — its spec, its `tests/`, and the implementation files that node governs. The moment the work touches anything else — a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node — this step is REQUIRED before the flow may be declared complete.

Run a whole-diff review over the full changeset (not only the target node) via the `changes-reviewer` agent. The per-node gates in Steps 4, 6, and 8 inspect the target node; they do not see cross-node effects — a stale reference a rename left in a sibling, dead code a move orphaned, a spec a consolidation made false. The whole-diff review catches those, and catching them here costs one early review instead of many rounds later at merge time.

Apply `<stabilized_diff_rule>` before invoking the review. Fix every valid finding it surfaces, including every in-scope same-class instance found by the same-class sweep, then re-run. **Unaddressed valid finding -> fix the defect class -> re-run this step.** Loop until the review converges.

</step>

<step number="10" name="Merge" condition="the change is destined for the default branch">

Skip this step only when the user explicitly scoped the work to a proposal, analysis, review, or local-only change — then state that scope and stop. For every other change, the work is destined for the default branch, and the flow is NOT complete at Step 9.

Local readiness is not delivered value. An APPROVED Step 8 audit, a converged Step 9 review, passing tests, a clean working tree, and a local commit ahead of base are progress. Delivered value is the change merged to the default branch on origin.

Invoke `/merge`. It selects the transport and drives the change to the default branch under its own authority gates — this flow neither re-implements the merge protocol nor re-decides those gates. The `/merge` lifecycle owns commit, push, integration review, and merge.

The flow is complete only when the change reaches the default branch on origin, or an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base is never the endpoint for default-branch work.

Claude tends to report the flow done the moment Step 9 converges and tests pass — while nothing has been committed, pushed, reviewed at integration time, or merged. That treatment of local readiness as completion is the exact failure this step exists to prevent.

</step>

</steps>

<review_gates>

Steps 4, 6, and 8 are blocking audit gates. Each audit skill emits `APPROVED` or `REJECT`. Step 9 is a blocking whole-changeset review gate that runs whenever the change reaches beyond the target node. Step 10 is the terminal lifecycle boundary for default-branch work — not a REJECT-loop gate, but a hard precondition for declaring the flow complete.

- Before starting Step 5: scan the conversation for the Step 4 verdict. If `APPROVED` is not present, stop — invoke Step 4.
- Before starting Step 7: scan the conversation for the Step 6 verdict. If `APPROVED` is not present, stop — invoke Step 6.
- Before considering implementation complete: scan the conversation for the Step 8 verdict. If `APPROVED` is not present, stop — invoke Step 8.
- Before declaring the flow complete: if the change touches anything beyond the target node, scan for a converged Step 9 review. If it is absent or has unaddressed valid findings, stop — invoke Step 9.
- Before declaring the flow complete for default-branch work: confirm the change reached the default branch on origin through Step 10's `/merge`, or that the user scoped the work to a proposal, analysis, review, or local-only change, or that an explicit merge lifecycle gate blocks with no independent local action remaining. A clean working tree, a local commit, or a branch ahead of base does not satisfy this — invoke Step 10.

On `REJECT` (Steps 4, 6, 8) or an unaddressed valid finding (Step 9): fix the defect class, re-invoke the same skill, and scan again.

**3 consecutive REJECTs on the same gate (Steps 4, 6, 8), or 3 consecutive Step 9 runs that still surface unresolved valid findings -> STOP.** Surface the stuck gate to the user via `AskUserQuestion`: report the gate, its most recent verdict (for Step 9, the outstanding findings), the same-class sweep already performed, and what did not resolve. A convergence loop that keeps reopening valid findings is a signal the model is unstable; refactor the model before asking the same gate again.

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

**Failure 2: Claude patched the cited line instead of the defect class.** An audit gate or the Step 9 review cited one instance; Claude fixed that line, re-ran the gate, and the same class reopened on the next iteration elsewhere. Signal: repeated REJECTs reopening the same rule, source contract, or evidence pattern. Avoid: per `<stabilized_diff_rule>`, treat each finding as defect-class evidence — sweep the touched node(s), fix every in-scope instance, then run the gate once on the stabilized tree.

**Failure 3: Claude kept running the flow in the main context after dispatching `--agent`.** Invoked with `--agent`, Claude launched the `applier` agent and then also ran Steps 1–8 in the main context, duplicating the work. Signal: main-context architect/test/code steps after an `applier` dispatch. Avoid: after `--agent` dispatch, stop the per-node steps in the main context; resume only at Step 9 (when cross-node) and Step 10 once the agent returns.

</failure_modes>

<success_criteria>

Scan the conversation for these markers before declaring done:

- [ ] `SPEC_TREE_FOUNDATION` marker present (Step 1)
- [ ] `SPEC_TREE_CONTEXT` marker present (Step 2)
- [ ] Step 4 audit skill emitted `APPROVED`
- [ ] Step 6 audit skill emitted `APPROVED`
- [ ] Step 8 audit skill emitted `APPROVED`
- [ ] If the change touched anything beyond the target node: the last Step 9 `changes-reviewer` run reported no `BLOCKING` or `DEBT` finding, or every such finding was fixed or individually refuted as unbacked
- [ ] All tests pass
- [ ] For default-branch work: the change reached the default branch on origin through Step 10's `/merge`, unless the user scoped the work to a proposal, analysis, review, or local-only change, or an explicit merge lifecycle gate blocks with no independent local action remaining — a clean working tree, a local commit, or a branch ahead of base does not satisfy this

</success_criteria>
