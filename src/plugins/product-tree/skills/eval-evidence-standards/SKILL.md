---
name: eval-evidence-standards
user-invocable: false
description: >-
  Shared eval-evidence standards — producer coupling, oracle independence, assertion alignment, falsifiability, and run evidence. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The shared eval-evidence standards for an `[eval]` suite: five ordered properties — producer coupling, oracle independence, assertion alignment, falsifiability, and run evidence — that define sound eval evidence.
</objective>

<repo_local_overlay>
Inside a repository, check for `spx/local/eval-evidence.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth, and it never weakens a property this reference states.
</repo_local_overlay>

<artifacts>

| Artifact        | Role                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------ |
| `eval.toml`     | Suite definition: thresholds, trials, prompt and case paths                                |
| `prompt.md`     | Model-facing task prompt                                                                   |
| `cases.jsonl`   | Durable case data plus the deterministic expected-verdict fields                           |
| `history.jsonl` | Append-only run summaries the eval harness writes                                          |
| Producer        | The skill, agent, classifier, script, or command whose structured verdict the suite scores |

</artifacts>

<properties>

A suite lacking any property has no evidentiary value for the assertion it claims to verify. Judge them in this order.

1. **Producer coupling.** The suite reaches the real producer. A prompt that restates the producer's rules and asks for the desired verdict is a simulation; metadata that names a producer the prompt or harness never uses is false coupling. A prompt materialized from a named section of the producer is coupled when the claim is about that section's behavior and the committed prompt is current with its source. Replacing the producer with unrelated text must change the suite's result.
2. **Oracle independence.** The model-facing task carries scenario facts and a compact output schema only. Expected verdicts, expected finding identifiers, answer tables, and case labels that reveal the answer stay in grader-only case fields.
3. **Assertion alignment.** Every expected-verdict field corresponds to a claim in the assertion, negative cases target the assertion's failure mode, and the assertion cannot be unfulfilled while every case passes.
4. **Falsifiability.** One concrete mutation to the producer, never to the prompt or cases, fails at least one case.
5. **Run evidence.** The committed history holds a complete, passing run for the current definition, case set, threshold, and producer. Budget-exhausted, timed-out, interrupted, and infrastructure-failed runs prove nothing; a run for a stale definition proves nothing about the current one.

</properties>

<case_provenance>

Derive case inputs from the assertion and the scenario's real-world shape, never from the producer's own text or its prior output. A case whose input was copied from the producer cannot disagree with it.

</case_provenance>

<success_criteria>

- A judgment against these standards evaluates the five properties in the stated order and names each property a suite lacks.
- A suite counts as evidence for its assertion only when it holds all five properties.
- Every case input traces to the assertion and the scenario's real-world shape, never to the producer's text or output.
- The repo-local overlay, when present, is read after this reference and weakens no property.

</success_criteria>
