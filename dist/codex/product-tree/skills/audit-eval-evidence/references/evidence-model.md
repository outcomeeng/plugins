<overview>

Audit procedures for eval evidence. Read this before auditing any `[eval]` assertion or eval suite.

`/eval-evidence-standards` defines the evidence properties and the case-provenance rule. This reference provides the taxonomy and procedures that apply them in an audit; the case-provenance rule is judged beside oracle independence.

</overview>

<contents>
- `artifact_model`
- `producer_coupling`
- `oracle_independence`
- `case_provenance`
- `alignment_model`
- `falsifiability_model`
- `run_evidence`
- `rejection_categories`

</contents>

<artifact_model>

`/eval-evidence-standards` states the role of `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, and the producer. An audit also reads two artifacts that the standard does not list:

| Artifact       | Role                                   |
| -------------- | -------------------------------------- |
| Spec assertion | Product truth the eval claims to prove |
| `runs/`        | Full transcripts, typically gitignored |

</artifact_model>

<producer_coupling>

Coupling is the first gate. An eval that does not reach the real producer is a simulation, even when its cases and grader are well-formed.

| Category         | Definition                                                                                         | Verdict                                                              |
| ---------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Direct           | Runner invokes the producer directly.                                                              | Proceed                                                              |
| Harness-mediated | Runner invokes a harness that loads and runs the producer without replacing its behavior.          | Proceed after chain inspection                                       |
| Prompt-loaded    | Prompt includes the producer body or governing artifact and asks for a verdict from that artifact. | Proceed only when the claim is about that loaded artifact's behavior |
| Simulation       | Prompt restates expected rules and asks for the desired verdict without using the producer.        | REJECT                                                               |
| False            | Metadata names the producer but prompt or harness never uses it.                                   | REJECT                                                               |
| Unknown          | Artifact path cannot establish how the producer is reached.                                        | REJECT                                                               |

`prompt_source.kind = "producer-section"` in `eval.toml` is a supported Prompt-loaded coupling mode. Verify that the producer file, named section, and prompt template exist, and that the committed `prompt.md` is current with the source-derived materialization. The selected producer section is the artifact under audit for the suite: mutating that section changes the materialized prompt. Do not require the eval runner to invoke the whole skill, agent, classifier, script, or command when the assertion is about the selected section's behavior; the loaded section is the producer artifact for that suite. A hand-authored prompt that copies the same rules without `prompt_source` is Simulation.

For claims about skill, agent, classifier, script, or command behavior, replacing the producer with unrelated text must change the eval result. Assess this counterfactual by reading the producer, materialization logic, cases, and grading rules. For `producer-section` suites, identify a mutation that removes behavior the cases exercise and trace how it would change the materialized prompt and the suite's result; do not edit the section, materialize a prompt, or execute the suite. If the eval would still pass after that producer mutation, it is not coupled.

</producer_coupling>

<oracle_independence>

`/eval-evidence-standards` states the oracle-independence property. This section supplies the audit-level case that the standard does not state, and the rejection value.

A case input field named or shaped so that the answer is visible without applying the producer methodology leaks the oracle.

Oracle leakage is a REJECT finding even when the run history passes.

</oracle_independence>

<case_provenance>

`/eval-evidence-standards` states the case-provenance rule. This section supplies the procedure that locates a violation and the rejection value.

Procedure:

1. Read each case input in `cases.jsonl`.
2. Search the producer artifact and the recorded run output for the input's distinctive text.
3. Trace each input to the assertion and the scenario's real-world shape.

An input found verbatim, or as a near copy, in the producer's text or its recorded output is REJECT as `case-provenance`. An input that traces to the assertion and the scenario passes. An input whose source the artifacts cannot establish is reported as `INFO`, never rejected without a located copy.

</case_provenance>

<alignment_model>

Assertion alignment checks whether the suite proves the spec assertion, not an adjacent behavior.

Procedure:

1. Read the `[eval]` assertion text.
2. Read each case's scenario and expected verdict fields.
3. Map every expected field to a claim in the assertion.
4. Confirm negative cases target the assertion's failure mode.
5. Ask whether the assertion could be unfulfilled while every case still passes.

If the assertion could be unfulfilled while the suite passes, REJECT as misaligned.

</alignment_model>

<falsifiability_model>

For each suite, name one concrete mutation to the producer that would fail at least one case. For `producer-section` suites, the mutation targets the selected producer section and reaches the eval through prompt materialization.

Valid mutation:

```text
Producer: the producing audit skill named by the eval assertion
Mutation: remove the invalid-tag rule from the audit workflow
Expected eval impact: the invalid-tag case returns PASS instead of REJECT, so the grader fails it
```

Invalid mutation:

```text
Producer: prompt.md
Mutation: edit the prompt answer key
Problem: falsifies the eval prompt, not the real producer
```

If no producer mutation changes the result, the suite is unfalsifiable for the assertion.

</falsifiability_model>

<run_evidence>

Run evidence shows the current eval definition has passed at least once.

Read `history.jsonl` and the referenced run summary when available. Confirm:

- The run uses the current `eval.toml`, prompt, cases, threshold, and producer.
- The run completed enough cases/trials to satisfy the threshold.
- The recorded outcome is passing.
- The row is not budget-exhausted, timed out, interrupted, or infrastructure-failed.

When the newest passing row's `git_sha` names a direct ancestor of HEAD, inspect
the diff from that SHA to HEAD before rejecting it as stale. Accept the row only
when every changed path is the audited suite's own `history.jsonl` append and no
`eval.toml`, `prompt.md`, `cases.jsonl`, producer artifact, grader, harness, or
threshold-affecting code changed. This history-only exception is required
because committing an append-only history row necessarily advances HEAD after
the run records `git rev-parse HEAD`.

Use `git merge-base --is-ancestor <recorded-git-sha> HEAD` to establish ancestry
and `git diff --no-ext-diff --no-textconv <recorded-git-sha> HEAD --` to inspect
the complete change, including whether the history modification is append-only.
Treat an unavailable commit or failed inspection as unavailable provenance,
never as proof that the exception applies.

Budget-exhausted and other operational failures are neither passes nor behavioral rejections. They only show the suite did not produce complete evidence.

</run_evidence>

<rejection_categories>

Use these `rule` values in findings:

| Rule                  | Meaning                                                                |
| --------------------- | ---------------------------------------------------------------------- |
| `missing-artifact`    | Required eval artifact is absent                                       |
| `missing-target`      | Request carries no spec-node target to audit                           |
| `producer-coupling`   | Suite does not reach the real producer                                 |
| `oracle-leakage`      | Prompt or case input exposes the expected answer                       |
| `case-provenance`     | Case input is copied from the producer's text or its recorded output   |
| `assertion-alignment` | Expected verdict fields do not prove the assertion                     |
| `falsifiability`      | No mutation to the producer changes the result                         |
| `run-evidence`        | Passing run evidence is missing, stale, or operationally incomplete    |
| `no-eval-assertions`  | Target spec carries no `[eval]` assertion, so no eval evidence applies |

</rejection_categories>
