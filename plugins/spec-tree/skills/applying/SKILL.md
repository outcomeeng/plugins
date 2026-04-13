---
name: applying
description: >-
  ALWAYS invoke this skill before implementing any spec-tree work item.
  NEVER write code for a spec-tree node without this skill.
hooks:
  PostToolUse:
    - matcher: "Skill"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/skills/applying/scripts/enforce-gates.sh"
---

<objective>
Orchestrate the spec-tree TDD flow for a work item. Eight steps, strictly sequential. Three review gates that loop until APPROVED — no exceptions, no soft passes. Spans all three methodology steps (declare → spec → apply) because agents skip declaring prerequisites without guardrails.

</objective>

<quick_start>

1. Load methodology (Step 1 — once per session)
2. Load work item context (Step 2 — every node)
3. Architect → audit until APPROVED (Steps 3–4)
4. Test → audit until APPROVED (Steps 5–6)
5. Implement → audit until APPROVED (Steps 7–8)

</quick_start>

<language_detection>

Before starting Step 3, determine the project language:

- `tsconfig.json` exists → **TypeScript**
- `pyproject.toml` or `setup.py` exists → **Python**
- Both exist → check the spec node for language indicators, or ask the user

Use the detected language for ALL Steps 3–8. Do not switch mid-flow.

</language_detection>

<skill_map>

Steps 1–2 are language-independent. Steps 3–8 use the detected language.

| Step | Purpose            | TypeScript                                                | Python                                  |
| ---- | ------------------ | --------------------------------------------------------- | --------------------------------------- |
| 1    | Load methodology   | `Skill("spec-tree:understanding")`                        | same                                    |
| 2    | Load context       | `Skill("spec-tree:contextualizing", args: "{node-path}")` | same                                    |
| 3    | Architect          | `Skill("architecting-typescript")`                        | `Skill("architecting-python")`          |
| 4    | Architecture audit | `Skill("auditing-typescript-architecture")`               | `Skill("auditing-python-architecture")` |
| 5    | Write tests        | `Skill("testing-typescript")`                             | `Skill("testing-python")`               |
| 6    | Test audit         | `Skill("auditing-typescript-tests")`                      | `Skill("auditing-python-tests")`        |
| 7    | Implement          | `Skill("coding-typescript")`                              | `Skill("coding-python")`                |
| 8    | Code audit         | `Skill("auditing-typescript")`                            | `Skill("auditing-python")`              |

**You MUST invoke the exact Skill tool call shown.** Do not substitute, skip, or reorder.

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

**REJECT → fix → re-invoke this step.** Loop until APPROVED.

</step>

<step number="5" name="Write tests">

Invoke the testing skill for the detected language.

Write tests for all assertions in the spec. Tests come before implementation — no exceptions.

</step>

<step number="6" name="Test audit" gate="true">

Invoke the test audit skill for the detected language.

**REJECT → fix → re-invoke this step.** Loop until APPROVED.

</step>

<step number="7" name="Implement">

Invoke the coding skill for the detected language.

Write implementation code. All tests from Step 5 must pass.

</step>

<step number="8" name="Code audit" gate="true">

Invoke the code audit skill for the detected language.

**REJECT → fix → re-invoke this step.** Loop until APPROVED.

</step>

</steps>

<review_gates>

Steps 4, 6, and 8 are blocking review gates. Each audit skill emits `APPROVED` or `REJECT`.

- Before starting Step 5: scan the conversation for the Step 4 verdict. If `APPROVED` is not present, stop — invoke Step 4.
- Before starting Step 7: scan the conversation for the Step 6 verdict. If `APPROVED` is not present, stop — invoke Step 6.
- Before declaring success: scan the conversation for the Step 8 verdict. If `APPROVED` is not present, stop — invoke Step 8.

On `REJECT`: fix the findings, re-invoke the same audit skill, and scan again.

**3 consecutive REJECTs on the same gate → STOP.** Report which gate failed and why, and ask the user for guidance.

</review_gates>

<rationale>
When something breaks or behaves unexpectedly, your instinct will be to write ad hoc code — a quick script, a throwaway snippet, a print-and-pray debugging session. That instinct is the symptom, not the fix. The problem you hit exists because your tests were insufficient. The ad hoc code patches over one instance; a proper test catches every future instance too.

1. **Do not** write ad hoc code to "see what's happening."
2. **Do** write a test that reproduces the problem. The fact that you hit this issue proves your test coverage has a gap.
3. **Then** fix the implementation until the test passes.

This is not slower. The ad hoc script you were about to write takes the same effort as a test, but the script gets deleted and the test stays.

</rationale>

<success_criteria>

Scan the conversation for these markers before declaring done:

- [ ] `SPEC_TREE_FOUNDATION` marker present (Step 1)
- [ ] `SPEC_TREE_CONTEXT` marker present (Step 2)
- [ ] Step 4 audit skill emitted `APPROVED`
- [ ] Step 6 audit skill emitted `APPROVED`
- [ ] Step 8 audit skill emitted `APPROVED`
- [ ] All tests pass

</success_criteria>
