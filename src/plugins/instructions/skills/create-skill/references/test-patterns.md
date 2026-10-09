<contents>

- `<overview>` — what skill testing covers
- `<evaluation_driven_development>` — writing evaluations before the skill
- `<case_contract>` — the shape of one test case
- `<scenario_selection>` — choosing scenarios
- `<fresh_context_testing>` — testing in a fresh context
- `<multi_model_and_runtime_coverage>` — coverage across models and agents
- `<feedback_loop>` — turning results into revisions
- `<success_criteria>` — when testing is complete

</contents>

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

Run the same cases with the changed skill in the execution context `<fresh_context_testing>` obtains. Compare against the baseline, record regressions, and repeat until the expected behavior holds without displacing adjacent behavior.

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

Obtain the execution context, and load the built bundle into it, by the first of these that applies:

1. When the target repository declares a skill-exercise or eval command in its agent guide or skill-authoring overlay, run that command against the built bundle; the command owns how the bundle loads.

{!% if target == 'claude' %!}

2. Otherwise, start one non-interactive session that loads the built plugin directory for that session only — the plugin directory the build emitted, or the authored plugin directory where the harness loads authored source unrendered:

   ```bash
   claude -p --verbose --output-format stream-json --plugin-dir <built-plugin-dir> "<representative request>"
   ```

   The run counts only when the stream's `Base directory for this skill:` line names a path under `<built-plugin-dir>`. A base directory under an installed plugin cache means the session loaded an installed copy rather than the edited bundle.

{!% else %!}

2. Otherwise, stop and return a blocked result naming the missing repository exercise command. Codex loads a plugin only after installing it into a Codex home, so no command loads the built bundle into a fresh session without changing installed state.

{!% endif %!}

Never count a run of the edited files inside the authoring session as the exercise.

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
3. Exercise the affected cases in the execution context `<fresh_context_testing>` obtains.
4. Compare with the recorded baseline and prior passing cases.
5. Repair regressions before widening the change.
6. Return the bundle for independent verification once the deterministic checks pass on it.

</feedback_loop>

<success_criteria>

- Every changed behavior traces to a reproduced gap or explicit new requirement.
- Cases describe observable evidence and reject the original failure.
- Fresh-context results pass without relying on authoring history.
- Adjacent triggers and prior passing cases remain intact.
- Repository checks pass on the exact bundle the cases passed on.

</success_criteria>
