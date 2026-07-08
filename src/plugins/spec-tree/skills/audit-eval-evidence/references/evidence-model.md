<overview>

Detailed evidence model for eval auditing. Read this before auditing any `[eval]` assertion or eval suite.

Five properties define eval evidence: producer coupling, oracle independence, assertion alignment, falsifiability, and run evidence. This reference provides the taxonomy and procedures for each.

</overview>

<artifact_model>

Eval evidence consists of:

| Artifact        | Role                                                                                               |
| --------------- | -------------------------------------------------------------------------------------------------- |
| Spec assertion  | Product truth the eval claims to prove                                                             |
| `eval.toml`     | Suite definition, thresholds, trials, prompt and case paths                                        |
| `prompt.md`     | Model-facing task prompt                                                                           |
| `cases.jsonl`   | Durable case data plus deterministic expected verdict fields                                       |
| `history.jsonl` | Committed append-only run summaries                                                                |
| `runs/`         | Full transcripts, typically gitignored                                                             |
| Producer        | The skill, agent, classifier, script, or command whose structured verdict the eval claims to score |

Eval evidence proves producer behavior only when the case set drives the producer and the grader checks the producer's structured output against expectations derived from the assertion.

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

`prompt_source.kind = "producer-section"` in `eval.toml` is a supported Prompt-loaded coupling mode. Verify that the producer file, named section, and prompt template exist, and that the committed `prompt.md` is current with the source-derived materialization. The selected producer section is the artifact under audit for the suite: mutating that section changes the materialized prompt. Do not require the eval runner to invoke the whole skill, agent, classifier, or script when the assertion is about the selected section's behavior; the loaded section is the producer artifact for that suite. A hand-authored prompt that copies the same rules without `prompt_source` is Simulation.

For claims about skill, agent, classifier, or script behavior, the mutation test is decisive: replacing the producer with unrelated text must change the eval result. For `producer-section` suites, evaluate that mutation through the materialization path: mutate the selected section, materialize the prompt, and then the suite's result must change when the mutation removes behavior the cases exercise. If it does not, the eval is not coupled.

</producer_coupling>

<oracle_independence>

Oracle independence means the model-facing task does not contain the answer key.

Allowed:

- Expected verdict fields in `cases.jsonl` when they are consumed only by the deterministic grader.
- Scenario facts the producer must inspect.
- A compact output schema the producer must return.

Rejected:

- Prompt text that includes the exact expected verdict for each case.
- A decision table mapping the case identifiers or scenario labels directly to answers.
- A prompt that restates the producing skill's policy in simplified form while the real skill is absent.
- Case input fields named or shaped so the answer is visible without applying the producer methodology.

Oracle leakage is a REJECT finding even when the run history passes.

</oracle_independence>

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

Budget-exhausted and other operational failures are neither passes nor behavioral rejections. They only show the suite did not produce complete evidence.

</run_evidence>

<rejection_categories>

Use these `rule` values in findings:

| Rule                  | Meaning                                                             |
| --------------------- | ------------------------------------------------------------------- |
| `missing-artifact`    | Required eval artifact is absent                                    |
| `producer-coupling`   | Suite does not reach the real producer                              |
| `oracle-leakage`      | Prompt or case input exposes the expected answer                    |
| `assertion-alignment` | Expected verdict fields do not prove the assertion                  |
| `falsifiability`      | No mutation to the producer changes the result                      |
| `run-evidence`        | Passing run evidence is missing, stale, or operationally incomplete |

</rejection_categories>
