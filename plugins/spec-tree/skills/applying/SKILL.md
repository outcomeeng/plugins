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
          command: "${CLAUDE_SKILL_DIR}/scripts/enforce-gates.sh"
---

<objective>
Orchestrate the spec-tree TDD flow for a work item. Eight phases, strictly sequential. Three review gates that loop until APPROVED — no exceptions, no soft passes.

</objective>

<quick_start>

1. Load methodology (Phase 1 — once per session)
2. Load work item context (Phase 2 — every node)
3. Architect → audit until APPROVED (Phases 3–4)
4. Test → audit until APPROVED (Phases 5–6)
5. Implement → audit until APPROVED (Phases 7–8)

</quick_start>

<language_detection>

Before starting Phase 3, determine the project language:

- `tsconfig.json` exists → **TypeScript**
- `pyproject.toml` or `setup.py` exists → **Python**
- Both exist → check the spec node for language indicators, or ask the user

Use the detected language for ALL Phases 3–8. Do not switch mid-flow.

</language_detection>

<skill_map>

Phases 1–2 are language-independent. Phases 3–8 use the detected language.

| Phase | Purpose            | TypeScript                                                | Python                                  |
| ----- | ------------------ | --------------------------------------------------------- | --------------------------------------- |
| 1     | Load methodology   | `Skill("spec-tree:understanding")`                        | same                                    |
| 2     | Load context       | `Skill("spec-tree:contextualizing", args: "{node-path}")` | same                                    |
| 3     | Architect          | `Skill("architecting-typescript")`                        | `Skill("architecting-python")`          |
| 4     | Architecture audit | `Skill("auditing-typescript-architecture")`               | `Skill("auditing-python-architecture")` |
| 5     | Write tests        | `Skill("testing-typescript")`                             | `Skill("testing-python")`               |
| 6     | Test audit         | `Skill("auditing-typescript-tests")`                      | `Skill("auditing-python-tests")`        |
| 7     | Implement          | `Skill("coding-typescript")`                              | `Skill("coding-python")`                |
| 8     | Code audit         | `Skill("auditing-typescript")`                            | `Skill("auditing-python")`              |

**You MUST invoke the exact Skill tool call shown.** Do not substitute, skip, or reorder.

</skill_map>

<phases>

<phase number="1" name="Load methodology" frequency="once per session">

Invoke `/understanding`.

This loads the spec-tree methodology — node types, assertion formats, durable map rules. Skip if `SPEC_TREE_FOUNDATION` marker is already present in this session.

**Do not proceed until complete.**

</phase>

<phase number="2" name="Load work item context" frequency="every node">

Invoke `/contextualizing` with the node path.

Load the full context hierarchy for the specific node — parent chain, sibling nodes, applicable decisions, assertions.

**Repeat for every new node.** Do not reuse context from a previous node.

**Do not proceed until complete.**

</phase>

<phase number="3" name="Architect">

Invoke the architecting skill for the detected language.

Produce the ADR(s) for the work item. The architecture must be complete before audit.

</phase>

<phase number="4" name="Architecture audit" gate="true">

Invoke the architecture audit skill for the detected language.

**REJECT → fix → re-invoke this phase.** Loop until APPROVED.

</phase>

<phase number="5" name="Write tests">

Invoke the testing skill for the detected language.

Write tests for all assertions in the spec. Tests come before implementation — no exceptions.

</phase>

<phase number="6" name="Test audit" gate="true">

Invoke the test audit skill for the detected language.

**REJECT → fix → re-invoke this phase.** Loop until APPROVED.

</phase>

<phase number="7" name="Implement">

Invoke the coding skill for the detected language.

Write implementation code. All tests from Phase 5 must pass.

</phase>

<phase number="8" name="Code audit" gate="true">

Invoke the code audit skill for the detected language.

**REJECT → fix → re-invoke this phase.** Loop until APPROVED.

</phase>

</phases>

<review_gates>

Phases 4, 6, and 8 are blocking review gates. Each audit skill emits `APPROVED` or `REJECT`.

- Before starting Phase 5: scan the conversation for the Phase 4 verdict. If `APPROVED` is not present, stop — invoke Phase 4.
- Before starting Phase 7: scan the conversation for the Phase 6 verdict. If `APPROVED` is not present, stop — invoke Phase 6.
- Before declaring success: scan the conversation for the Phase 8 verdict. If `APPROVED` is not present, stop — invoke Phase 8.

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

- [ ] `SPEC_TREE_FOUNDATION` marker present (Phase 1)
- [ ] `SPEC_TREE_CONTEXT` marker present (Phase 2)
- [ ] Phase 4 audit skill emitted `APPROVED`
- [ ] Phase 6 audit skill emitted `APPROVED`
- [ ] Phase 8 audit skill emitted `APPROVED`
- [ ] All tests pass

</success_criteria>
