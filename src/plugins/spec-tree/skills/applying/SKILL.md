---
name: applying
description: >-
  ALWAYS invoke this skill before implementing any spec-tree work item.
  NEVER write code for a spec-tree node without this skill.
---

<objective>
Orchestrate the spec-tree TDD flow for a work item. Eight steps, strictly sequential, plus a conditional ninth that reviews the whole changeset when the work reaches beyond the target node. Three unconditional audit gates (Steps 4, 6, 8) loop until APPROVED, and a conditional whole-changeset review gate (Step 9) is required whenever the change is cross-node — no soft passes on any active gate. Spans all three methodology steps (declare → spec → apply) because agents skip declaring prerequisites without guardrails.

</objective>

<quick_start>

1. Load methodology (Step 1 — once per session)
2. Load work item context (Step 2 — every node)
3. Architect → audit until APPROVED (Steps 3–4)
4. Test → audit until APPROVED (Steps 5–6)
5. Implement → audit until APPROVED (Steps 7–8)
6. Whole-changeset review when the change reaches beyond the target node (Step 9)

</quick_start>

<language_detection>

Before starting Step 3, determine the product language:

- `tsconfig.json` exists → **TypeScript**
- `pyproject.toml` or `setup.py` exists → **Python**
- Both exist → check the spec node for language indicators, or ask the user

Use the detected language for ALL Steps 3–8. Do not switch mid-flow.

</language_detection>

<scope_detection>

Before starting Step 3, determine the change's scope — this determination governs every later gate:

- **Node-local** — the entire diff stays within the target node's own directory (its spec, its `tests/`, and the implementation files that node governs).
- **Cross-node** — the work touches anything else: a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node.

When the scope is cross-node, every audit gate — Steps 4, 6, and 8 — runs at **whole-changeset** scope, not only the target node, and Step 9 is REQUIRED before the flow may be declared complete. A per-node audit reads only the target node's files; it cannot see a regression the change introduced in a file the node does not own. Carry the determination through Steps 4, 6, and 8 — each gate step restates the scope requirement at its point of action.

</scope_detection>

<skill_map>

Steps 1–2 are language-independent. Steps 3–8 use the detected language. Step 9 is language-independent and runs only when the change reaches beyond the target node.

| Step | Purpose                  | TypeScript                                                         | Python                                  |
| ---- | ------------------------ | ------------------------------------------------------------------ | --------------------------------------- |
| 1    | Load methodology         | `Skill("spec-tree:understanding")`                                 | same                                    |
| 2    | Load context             | `Skill("spec-tree:contextualizing", args: "{node-path}")`          | same                                    |
| 3    | Architect                | `Skill("architecting-typescript")`                                 | `Skill("architecting-python")`          |
| 4    | Architecture audit       | `Skill("auditing-typescript-architecture")`                        | `Skill("auditing-python-architecture")` |
| 5    | Write tests              | `Skill("testing-typescript")`                                      | `Skill("testing-python")`               |
| 6    | Test audit               | `Skill("auditing-typescript-tests")`                               | `Skill("auditing-python-tests")`        |
| 7    | Implement                | `Skill("coding-typescript")`                                       | `Skill("coding-python")`                |
| 8    | Code audit               | `Skill("auditing-typescript")`                                     | `Skill("auditing-python")`              |
| 9    | Whole-changeset review † | `changes-reviewer` agent or `Skill("spec-tree:reviewing-changes")` | same                                    |

† Step 9 runs only when the change touches files or specs beyond the target node (see the step for the condition).

**Invoke the exact Skill tool call shown.** Never substitute, skip, or reorder.

</skill_map>

<steps>

<step number="1" name="Load methodology" frequency="once per session">

Invoke `/understanding`.

This loads the spec-tree methodology — node types, assertion formats, durable map rules. Skip if `SPEC_TREE_FOUNDATION` marker is already present in this session.

**Do not proceed until complete.**

</step>

<step number="2" name="Load work item context" frequency="every node">

Invoke `/contextualizing` with the node path.

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

**REJECT → fix → re-invoke this step.** Loop until APPROVED.

</step>

<step number="5" name="Write tests">

Invoke the testing skill for the detected language.

Write tests for all assertions in the spec. Tests come before implementation — no exceptions.

</step>

<step number="6" name="Test audit" gate="true">

Invoke the test audit skill for the detected language.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — test evidence the change invalidated in a sibling node is invisible to a per-node audit.

**REJECT → fix → re-invoke this step.** Loop until APPROVED.

</step>

<step number="7" name="Implement">

Invoke the coding skill for the detected language.

Write implementation code. All tests from Step 5 must pass.

</step>

<step number="8" name="Code audit" gate="true">

Invoke the code audit skill for the detected language.

When the scope is cross-node (see `<scope_detection>`), point this audit at the **whole changeset**, not only the target node — as Steps 4 and 6 already did at their gates. Widening the three per-node audits is necessary but not sufficient: each inspects through its own lens (architecture, test evidence, code), so the distinct whole-diff review in Step 9 remains required for cross-cutting effects no single audit lens catches.

**REJECT → fix → re-invoke this step.** Loop until APPROVED.

</step>

<step number="9" name="Whole-changeset review" gate="true" condition="the change touches files or specs beyond the target node">

Skip this step only when the entire diff is confined to the target node's own directory — its spec, its `tests/`, and the implementation files that node governs. The moment the work touches anything else — a refactor, a move, a consolidation, a cross-cutting rename, a shared enabler, a sibling spec, or any file outside the target node — this step is REQUIRED before the flow may be declared complete.

Run a whole-diff review over the full changeset (not only the target node) via the `changes-reviewer` agent, or `/reviewing-changes` when the agent is not installed. The per-node gates in Steps 4, 6, and 8 inspect the target node; they do not see cross-node effects — a stale reference a rename left in a sibling, dead code a move orphaned, a spec a consolidation made false. The whole-diff review catches those, and catching them here costs one early review instead of many rounds later at merge time.

Fix every valid finding it surfaces, then re-run. **Unaddressed valid finding → fix → re-run this step.** Loop until the review converges.

</step>

</steps>

<review_gates>

Steps 4, 6, and 8 are blocking audit gates. Each audit skill emits `APPROVED` or `REJECT`. Step 9 is a blocking whole-changeset review gate that runs whenever the change reaches beyond the target node.

- Before starting Step 5: scan the conversation for the Step 4 verdict. If `APPROVED` is not present, stop — invoke Step 4.
- Before starting Step 7: scan the conversation for the Step 6 verdict. If `APPROVED` is not present, stop — invoke Step 6.
- Before considering implementation complete: scan the conversation for the Step 8 verdict. If `APPROVED` is not present, stop — invoke Step 8.
- Before declaring the flow complete: if the change touches anything beyond the target node, scan for a converged Step 9 review. If it is absent or has unaddressed valid findings, stop — invoke Step 9.

On `REJECT` (Steps 4, 6, 8) or an unaddressed valid finding (Step 9): fix the findings, re-invoke the same skill, and scan again.

**3 consecutive REJECTs on the same gate (Steps 4, 6, 8), or 3 consecutive Step 9 runs that still surface unresolved valid findings → STOP.** Surface the stuck gate to the user via `AskUserQuestion`: report the gate, its most recent verdict (for Step 9, the outstanding findings), and what did not resolve. A convergence loop that keeps reopening valid findings is a signal the change needs human direction, not unbounded iteration.

</review_gates>

<rationale>
When something breaks or behaves unexpectedly, Claude's instinct is to write ad hoc code — a quick script, a throwaway snippet, a print-and-pray debugging session. That instinct is the symptom, not the fix. The problem surfaced because the tests were insufficient. The ad hoc code patches over one instance; a proper test catches every future instance too.

1. **Do not** write ad hoc code to "see what's happening."
2. **Do** write a test that reproduces the problem. Hitting this issue proves the test coverage has a gap.
3. **Then** fix the implementation until the test passes.

This is not slower. The ad hoc script takes the same effort as a test, but the script gets deleted and the test stays.

</rationale>

<success_criteria>

Scan the conversation for these markers before declaring done:

- [ ] `SPEC_TREE_FOUNDATION` marker present (Step 1)
- [ ] `SPEC_TREE_CONTEXT` marker present (Step 2)
- [ ] Step 4 audit skill emitted `APPROVED`
- [ ] Step 6 audit skill emitted `APPROVED`
- [ ] Step 8 audit skill emitted `APPROVED`
- [ ] If the change touched anything beyond the target node: the last Step 9 `changes-reviewer` run reported no `BLOCKING` or `DEBT` finding, or every such finding was fixed or individually refuted as unbacked
- [ ] All tests pass

</success_criteria>
