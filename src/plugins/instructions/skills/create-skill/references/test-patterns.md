<overview>

Develop behavior-producing skills from representative evaluations and fresh-context use. Establish the failure before adding extensive guidance, then keep only content that changes the observed result.

</overview>

<evaluation_driven_development>

<step name="identify_gap">

Run representative tasks without the proposed skill or with the current skill. Record specific incorrect choices, missing context, invalid output, or activation failures.

</step>

<step name="define_cases">

Create cases that isolate each observed gap. Include a normal case, a boundary case, and a failure case when the capability owns those behaviors. State expected behavior as observable output or state, never as free-form quality praise.

</step>

<step name="establish_baseline">

Record the result without the change. A case with no reproduced gap cannot prove the new guidance caused an improvement.

</step>

<step name="author_minimum">

Add the smallest instruction, reference, template, or executable contract that addresses the reproduced gap. Keep unrelated domain knowledge out of the eager payload.

</step>

<step name="compare_and_iterate">

Run the same cases with the changed skill in a fresh context. Compare against the baseline, record regressions, and repeat until the expected behavior holds without displacing adjacent behavior.

</step>

</evaluation_driven_development>

<case_contract>

Each case records:

| Field               | Required content                                       |
| ------------------- | ------------------------------------------------------ |
| Name                | Stable case identifier                                 |
| Trigger             | Representative operator request                        |
| Inputs              | Required files, repository state, or external fixtures |
| Expected behavior   | Observable actions, output fields, or terminal state   |
| Prohibited behavior | Specific regression the case rejects                   |
| Evidence            | Deterministic check or structured grading contract     |

Use the target repository's declared eval or test format. Never invent a parallel case schema when the repository already owns one.

</case_contract>

<scenario_selection>

| Scenario         | Purpose                                                                      |
| ---------------- | ---------------------------------------------------------------------------- |
| Normal           | Prove the primary route and output                                           |
| Boundary         | Prove behavior near a valid limit or ambiguous route                         |
| Failure          | Prove actionable handling of invalid input or unavailable capability         |
| Adjacent trigger | Prove description or router changes do not steal another skill's request     |
| Portability      | Prove bundled paths and instructions work on every supported runtime surface |

Select scenarios from the skill's actual contracts; a fixed minimum never substitutes for covering every distinct behavior.

</scenario_selection>

<fresh_context_testing>

Use separate authoring and execution contexts. The authoring context carries design history that can hide missing instructions; the execution context sees only the shipped skill and task inputs.

Observe:

- Unexpected exploration paths indicate unclear routing or missing constraints.
- Unread required references indicate weak citations or incorrect progressive disclosure.
- Repeated dependence on one section indicates content may belong in the eager skill body.
- Never-read content indicates a candidate for removal or a missing route.
- A passing result that depends on conversation history indicates the skill bundle is incomplete.

</fresh_context_testing>

<multi_model_and_runtime_coverage>

Run cases against every model class and runtime surface the skill officially supports when behavior can differ across them. Preserve one contract across targets; add target-specific rendering only where the platform contract differs.

</multi_model_and_runtime_coverage>

<feedback_loop>

For each iteration:

1. Apply one coherent change.
2. Run the narrow deterministic checks.
3. Exercise the affected cases in a fresh context.
4. Compare with the recorded baseline and prior passing cases.
5. Repair regressions before widening the change.
6. Obtain the required independent audit after deterministic checks pass.

</feedback_loop>

<success_criteria>

- Every changed behavior traces to a reproduced gap or explicit new requirement.
- Cases describe observable evidence and reject the original failure.
- Fresh-context results pass without relying on authoring history.
- Adjacent triggers and prior passing cases remain intact.
- Repository checks and the required independent audit pass on the exact committed bundle.

</success_criteria>
