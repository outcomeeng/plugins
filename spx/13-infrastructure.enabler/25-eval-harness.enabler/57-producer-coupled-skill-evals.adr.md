# Producer-Coupled Skill Evals

The `outcomeeng_evals` harness generates skill and agent eval prompts from declared producer artifacts. An eval this harness runs for skill, agent, classifier, script, or command behavior declares one whole producer, one named producer section, or an ordered set of whole producers in `eval.toml`; prompt materialization reads every declared producer and derives the model-facing prompt from that source set. A prompt that restates a producer's rules without reading that producer is invalid evidence for that producer. Eval coupling for the methodology is decided by `spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/15-adapter-derived-evals.adr.md`, and this decision reaches the `outcomeeng_evals` harness alone.

## Rationale

Eval evidence must fail when the behavior it claims to prove changes. A hand-authored `prompt.md` that simulates a skill can keep passing after the shipped skill is replaced, so it proves only the prompt author's copy of the rules. Shipped skill content is a rendered artifact with its own source-to-runtime contract, and the eval harness owns per-eval TOML, prompt, cases, run reports, and CI selection. Placing producer coupling in the eval definition lets deterministic tooling materialize reviewable prompts while preserving structured JSON grading.

Whole producer files, named producer sections, and ordered whole-producer sets are the supported source-derived coupling modes. A whole-skill assertion uses `producer-file`, so every change to the producing skill changes the materialized prompt. A concern-scoped assertion uses `producer-section`, so the generated prompt focuses on one stable XML-like step while deriving that step from shipped producer text. A composed-skill assertion uses `producer-files`, so every skill participating in the composed verdict appears in the generated prompt and a change to any participant changes the materialized subject. Harness-invoked evals remain valid when the suite preserves observable evidence that the real producer executed.

## Invariants

- The same producer text, source kind, optional section selector, prompt template, and case input produce the same rendered prompt.
- A change anywhere in a `producer-file` source changes the materialized prompt.
- The same ordered, duplicate-free `producer-files` source set produces the same path-labeled materialized prompt, and changing any member changes that prompt.
- A change to the selected producer section changes the materialized prompt unless the change is outside the selected section.

## Verification

### Testing

- ALWAYS: an eval definition with `prompt_source.kind = "producer-section"` resolves the prompt template relative to the eval directory and resolves the producer path against the repository root, then materializes `prompt.md` from the selected producer section ([conformance])
- ALWAYS: an eval definition with `prompt_source.kind = "producer-file"` resolves the same paths and materializes `prompt.md` from the complete producer file without parsing it as text ([conformance])
- ALWAYS: an eval definition with `prompt_source.kind = "producer-files"` resolves a non-empty, ordered, duplicate-free `producers` list against the repository root and materializes `prompt.md` from the complete path-labeled contents of every listed producer ([conformance])
- ALWAYS: producer-section extraction selects exactly one named XML-like section from the producer text and fails when no matching section or multiple matching sections exist ([mapping])
- ALWAYS: prompt materialization changes when the selected producer section changes and stays unchanged when unrelated producer text changes ([property])
- ALWAYS: prompt materialization changes when any member of a `producer-files` source set changes ([property])
- ALWAYS: the `outcomeeng-evals materialize-prompts --check` command fails when a generated `prompt.md` differs from its source-derived rendering and exits successfully when every generated prompt is current ([compliance])
- NEVER: a producer-coupled eval definition accepts a missing producer path, an empty or duplicate `producers` list, a missing prompt template, a missing section name for `producer-section`, a section name for a whole-file mode, or an unsupported prompt source kind ([conformance])

### Audit

- ALWAYS: skill, agent, classifier, script, or command behavior evals are coupled to the real producer through direct invocation, harness-mediated invocation, or source-derived prompt materialization ([audit])
- ALWAYS: producer-prompt rendering exposes its source-kind and path resolution through explicit definition values so tests exercise the real filesystem boundary without replacing collaborators ([audit])
- NEVER: a prompt-only simulation that restates the producing artifact's policy is accepted as evidence for that producer ([audit])
- NEVER: producer-prompt tests use framework mocks or monkeypatching to replace definition loading, path resolution, producer reads, or prompt writes; temporary real workspaces provide the evidence ([audit])
