---
name: audit-eval-evidence
description: >-
  Eval-evidence audit methodology preloaded by the eval-evidence-auditor agent.
  Dispatch eval-evidence-auditor to audit eval evidence against spec assertions;
  the main conversation reaches this audit only through that agent.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

<dispatch_gate>

This audit runs in the eval-evidence-auditor agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch the eval-evidence-auditor agent instead of running this audit here. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

A verdict on whether a spec node's eval suite provides evidence that its `[eval]` assertions are fulfilled — PASS, FAIL, or UNKNOWN, with each finding naming the assertion or eval artifact, the failed evidence property, and the evidentiary gap.

</objective>

<essential_principles>

**PRODUCER COUPLING FIRST.**

An eval that never exercises the actual producing skill, agent, classifier, or script will pass regardless of what that producer contains. Check coupling before oracle quality or run history. For claims about skill behavior, a prompt that merely asks for a simulated verdict while restating the desired rules is not evidence about the skill.

Five properties must hold, checked in strict order: producer coupling, oracle independence, assertion alignment, falsifiability, and run evidence. A suite missing any property has zero evidentiary value for the assertion it claims to verify.

**JUDGE BY READING.**

A dispatched audit context runs no deterministic verification. The main conversation brings the eval to passing on the changeset before dispatch when eval execution is required, and CI re-runs deterministic verification over the whole repository. Establish evidence quality by reading `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, relevant run summaries, and the producing artifact.

**SCHEMA VERDICT.**

PASS, FAIL, or UNKNOWN. If any required evidence property is missing for any `[eval]` assertion, FAIL.

</essential_principles>

<constraints>

- NEVER modify eval artifacts, skill bodies, prompts, cases, history, or any other file — this audit produces a verdict, never a fix or a commit.
- NEVER run evals, tests, validation, coverage, linters, type-checkers, or other deterministic verification inside the audit — the main conversation and CI own those commands.
- ALWAYS name the assertion, the failed property, and the evidentiary gap in every REJECT finding.
- NEVER approve prompt-only simulation as evidence for skill, agent, classifier, or script behavior.
- NEVER issue a finding the evidence model does not support — drop an unbacked finding rather than reject the eval evidence for it.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Read the evidence model before auditing: `${CLAUDE_SKILL_DIR}/references/evidence-model.md`

Invoke `/contextualize` on the spec node whose eval evidence is being audited. This loads the spec's assertions, ancestor ADRs/PDRs, and hierarchy context.

Do not proceed without a `<SPEC_TREE_CONTEXT>` marker.

</step>

<step name="map_assertions">

**Step 2: Map `[eval]` assertions to eval artifacts**

Read the spec's Assertions section. For each `[eval]` assertion, extract:

| Field          | Extract                                                                                            |
| -------------- | -------------------------------------------------------------------------------------------------- |
| Assertion text | The claim being evaluated                                                                          |
| Eval link      | Path from `([eval](path/to/eval.toml))`                                                            |
| Eval directory | Directory containing `eval.toml`, prompt, and cases                                                |
| Producer       | The skill, agent, classifier, script, or command the assertion claims emits the structured verdict |
| Link status    | File exists or missing                                                                             |

Missing eval definition, prompt, cases, or history file is a finding. Record it and continue to the next assertion.

Skip `[test]` and `[audit]` assertions. They belong to their own evidence lanes.

</step>

<step name="audit_producer_coupling">

**Step 3a: Producer coupling**

Classify how the eval reaches the producer:

| Category         | Definition                                                                                  | Verdict                                                                |
| ---------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Direct           | The eval runner invokes the producing skill, agent, classifier, script, or command directly | Proceed                                                                |
| Harness-mediated | The eval invokes a harness that loads and runs the producer without replacing its behavior  | Proceed after verifying the harness chain                              |
| Prompt-loaded    | The prompt loads the producer body as context while the case drives a verdict task          | Proceed only when the artifact under audit is the loaded producer text |
| Simulation       | The prompt restates the desired policy or asks for a simulated verdict without the producer | REJECT                                                                 |
| False            | Metadata names the producer but the prompt or harness never uses it                         | REJECT                                                                 |
| Unknown          | The artifact path cannot establish how the producer is reached                              | REJECT                                                                 |

For skill, agent, classifier, or script behavior claims, changing the real producer to unrelated text must change the eval result. If the eval would still pass after such a mutation, classify as Simulation or False and REJECT.

</step>

<step name="audit_oracle_independence">

**Step 3b: Oracle independence**

Read `prompt.md` and `cases.jsonl` side by side. Check whether the prompt sent to the producer leaks the expected verdict, expected finding IDs, exact answer table, or rule mapping in a way that makes the case self-answering.

Expected fields belong in the grader input, not in the task prompt the producer answers. A case may include expected verdict data for deterministic scoring; the model-facing prompt must still require the producer to infer the verdict from the scenario and its own methodology.

Self-answering prompt or case construction is REJECT — "oracle leakage."

</step>

<step name="audit_alignment">

**Step 3c: Assertion alignment**

Read the spec assertion, the eval cases, and the expected verdict fields. Answer:

1. Does each expected verdict field correspond to behavior the assertion claims?
2. Do the negative cases target the assertion's failure mode?
3. Could the assertion be unfulfilled while the eval suite passes?

If the assertion could be unfulfilled while the suite passes, REJECT — "misaligned."

</step>

<step name="audit_falsifiability">

**Step 3d: Falsifiability**

Name a concrete mutation to the producing artifact that would make at least one case fail. Write it down:

```text
Producer: ${CLAUDE_SKILL_DIR}/../manage-pr/SKILL.md
Mutation: replace the post-merge marketplace sync rule with unrelated text
Impact: the post-merge-sync-required case returns REJECT because the producer omits the required follow-up
```

Cannot name a mutation to the producer that changes the eval result -> REJECT — "unfalsifiable."

</step>

<step name="audit_run_evidence">

**Step 3e: Run evidence**

Read `history.jsonl` and, when available, the referenced run summary. Check that the committed history contains a successful run for the current eval definition, threshold, and case set.

Budget-exhausted, timeout, interrupted, or infrastructure-failed runs are operational evidence only. They do not prove behavior. A passing history row for a stale prompt, stale case set, or different producer does not prove the current assertion.

Missing or stale run evidence is REJECT — "missing run evidence" or "stale run evidence."

</step>

<step name="verdict">

**Step 4: Issue verdict**

Scan all findings across all `[eval]` assertions. If any assertion has a property failure: FAIL.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as JSON conforming to the canonical audit-verdict schema consumed by the composing audit workflow. The skill's entire output is the JSON verdict. Skills never hand-format markdown verdicts.

The skill's `overall` is `PASS` iff every applicable gate row is `PASS`; `FAIL` if any gate is `FAIL`; `UNKNOWN` if a gate could not be evaluated. Findings within each row carry severity `REJECT` for blocking findings, `WARNING` or `INFO` for non-blocking observations.

```json
{
  "schema_version": 1,
  "skill": "audit-eval-evidence",
  "target": "<spec-node-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    {
      "name": "gate-1-producer-coupling",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": [
        {
          "id": "f-001",
          "file": "<eval-artifact-or-producer-file>",
          "line": null,
          "rule": "producer-coupling",
          "severity": "REJECT",
          "message": "<one-line evidentiary gap>"
        }
      ]
    },
    {
      "name": "gate-2-oracle-quality",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": []
    },
    {
      "name": "gate-3-assertion-alignment",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": []
    },
    {
      "name": "gate-4-falsifiability",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": []
    },
    {
      "name": "gate-5-run-evidence",
      "status": "PASS | FAIL | UNKNOWN",
      "findings": []
    }
  ],
  "metadata": { "branch": "<branch>" }
}
```

</verdict_format>

<failure_modes>

**Failure 1: Approved a prompt-only skill simulation**

Claude accepted an eval that asked Claude to simulate a skill verdict from inline rules while never loading or invoking the real skill. Replacing the real skill body with unrelated text did not change the eval result, so the eval proved the prompt's rubric, not the skill.

How to avoid: Step 3a checks producer coupling first. Prompt-only simulation is REJECT for claims about producer behavior.

**Failure 2: Treated a budget failure as behavioral evidence**

Claude read a budget-exhausted eval run and treated the failed suite as evidence the rule was wrong. The run never completed enough cases to prove behavior.

How to avoid: Step 3e separates operational failures from behavioral pass evidence. Budget, timeout, and interruption rows never prove assertion fulfillment.

</failure_modes>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/evidence-model.md` — eval evidence properties, artifact taxonomy, and rejection categories.

</reference_guides>

<success_criteria>

The verdict is sound when:

- Every `[eval]` assertion's suite was judged on all five evidence properties with none skipped — producer coupling, oracle independence, assertion alignment, falsifiability, and run evidence.
- The verdict states an overall PASS/FAIL/UNKNOWN through the JSON `overall` field and every applicable gate row carries its determination.
- Each REJECT finding is falsifiable: it names the assertion or eval artifact, the failed evidence property, the evidentiary gap, and how the eval could pass while the assertion is unfulfilled.
- No deterministic command was run inside the audit; evidence quality was established by reading the eval artifacts, producing artifact, and committed run summaries.

</success_criteria>
