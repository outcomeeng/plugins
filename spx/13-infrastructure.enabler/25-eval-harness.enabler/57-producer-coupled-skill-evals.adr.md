# Producer-Coupled Skill Evals

Skill and agent eval prompts are generated from declared producer artifacts. An eval for skill, agent, classifier, script, or command behavior declares the producer in `eval.toml`; prompt materialization reads the producer and derives the model-facing prompt from a named producer section. A prompt that restates the producer's rules without reading the producer is invalid evidence for that producer.

## Rationale

Eval evidence must fail when the behavior it claims to prove changes. A hand-authored `prompt.md` that simulates a skill can keep passing after the shipped skill is replaced, so it proves only the prompt author's copy of the rules. Shipped skill content is a rendered artifact with its own source-to-runtime contract, and the eval harness owns per-eval TOML, prompt, cases, run reports, and CI selection. Placing producer coupling in the eval definition lets deterministic tooling materialize reviewable prompts while preserving structured JSON grading.

Named producer sections are the supported coupling mode because skill bodies already use stable XML-like sections and step tags. The generated prompt can focus the eval on one sub-prompt while still deriving that sub-prompt from the shipped producer text. Whole-skill or harness-invoked evals remain valid only when the suite exercises the real producer directly rather than through a materialized prompt.

## Invariants

- The same producer text, section selector, prompt template, and case input produce the same rendered prompt.
- A change to the selected producer section changes the materialized prompt unless the change is outside the selected section.

## Verification

### Testing

- ALWAYS: an eval definition with `prompt_source.kind = "producer-section"` resolves the prompt template relative to the eval directory and resolves the producer path against the repository root, then materializes `prompt.md` from the selected producer section ([conformance])
- ALWAYS: producer-section extraction selects exactly one named XML-like section from the producer text and fails when no matching section or multiple matching sections exist ([mapping])
- ALWAYS: prompt materialization changes when the selected producer section changes and stays unchanged when unrelated producer text changes ([property])
- ALWAYS: the `outcomeeng-evals materialize-prompts --check` command fails when a generated `prompt.md` differs from its source-derived rendering and exits successfully when every generated prompt is current ([compliance])
- NEVER: a producer-coupled eval definition accepts a missing producer path, missing prompt template, missing section name, or unsupported prompt source kind ([conformance])

### Audit

- ALWAYS: skill, agent, classifier, script, or command behavior evals are coupled to the real producer through direct invocation, harness-mediated invocation, or source-derived prompt materialization ([audit])
- NEVER: a prompt-only simulation that restates the producing artifact's policy is accepted as evidence for that producer ([audit])
