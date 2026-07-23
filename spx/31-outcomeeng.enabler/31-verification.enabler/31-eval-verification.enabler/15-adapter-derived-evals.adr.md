# Adapter-Derived Evals

Eval evidence for skill, agent, or command behavior comes from invoking the real coding agent on the installed plugin under test through the adapter contract in `spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/21-adapter-contract.adr.md`. A case declares its skill selection, its prepared workspace, and its expected structural outcome, and is scored against the artifacts one trial produces: the adapter's result envelope, the workflow trace the run emits, and the workspace's final state. Evidence over those artifacts is layered, one layer being the deterministic workflow-conformance verdict computed per `spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/conformance-verification.md`, and every layer resolves to a deterministic score. Materializing a model-facing prompt from a producer artifact's text is outside the evidence paths this decision admits.

## Rationale

A prompt derived from a producer's text establishes what a model does when handed that text. The artifact a consumer installs behaves through a different path: the agent loads the skill itself, its description drives activation, progressive disclosure decides what reaches context, its tool restriction bounds what it may do, and its scripts execute. Transplanting the text into a prompt exercises none of that, so a producer-derived eval passes while the installed plugin never activates — and the plugin's activation surface is where consumer-visible failure concentrates. Crossing the runtime boundary makes the installed plugin itself the producer the run reaches, so the evidence covers the delivery path a consumer depends on rather than a copy of the words inside it.

Deriving a prompt from producer text obliges the harness to keep that copy faithful to its source, which costs path resolution, templating, and drift detection. Reaching the source directly removes the copy and the machinery guarding it. The workflow trace carries the participation proof a faithful copy can only approximate: script-emitted states show the shipped skill's own scripts ran, which prompt-level evidence cannot show at all.

Runtime non-determinism is bounded rather than admitted into the verdict — the agent varies, while the function scoring its artifacts stays pure — preserving the deterministic verdict mode the evaluate type binds in `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`. The rejected alternative keeps producer-derived prompts as a second lane beside runtime invocation; it sustains the compensation machinery for evidence the runtime lane already subsumes and leaves two eval shapes whose verdicts answer different questions while reading as one number.

## Invariants

- A verdict is a pure function of the case's declared expectations and the artifacts one trial produced; runtime variation reaches the verdict only through those artifacts.
- Withholding the plugin under test from the invocation makes its evals fail.

## Verification

### Testing

- ALWAYS: a case declares its skill selection, its prepared workspace, and its expected structural outcome, and is scored against the adapter's result envelope, the trace the run emits, and the workspace's final state ([conformance])
- NEVER: an eval declares a producer path, producer section, or producer set from which to materialize a prompt — the installed plugin is the producer the run reaches ([compliance])

### Eval

- ALWAYS: an eval whose invocation withholds the plugin under test fails — a suite that passes with the plugin absent measures the model alone ([eval])

### Audit

- ALWAYS: an eval for skill, agent, or command behavior invokes the real coding agent on the installed plugin under test through `spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/21-adapter-contract.adr.md` ([audit])
- ALWAYS: a workflow-conformance verdict computed per `spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/conformance-verification.md` is one evidence layer of a skill eval, scored beside the run's structural output, final state, and telemetry ([audit])
- ALWAYS: every evidence layer resolves to a deterministic score over structured artifacts, so no layer's verdict comes from a model reading prose ([audit])
- NEVER: a model-facing prompt derived from a producer artifact's text stands as evidence for that producer's shipped behavior ([audit])
- NEVER: a generated-prompt drift check stands as evidence of producer coupling — coupling is established by the run reaching the installed artifact ([audit])
