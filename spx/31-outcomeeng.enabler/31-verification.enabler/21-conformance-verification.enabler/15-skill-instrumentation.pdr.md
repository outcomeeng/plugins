# Skill Instrumentation

Skill workflow behavior is observable through state tokens emitted only by skill scripts as a side effect of performing work, written to a sidecar trace path and judged against a declared conformance contract by a deterministic checker. A workflow state that matters to a contract is a script action; the model never prints, announces, or relays a state token. Contracts bind in two modes — normative for first-party skills, where a violation gates, and descriptive for third-party or not-yet-ratified contracts, where violations are reported as drift — and contract rules express required states, forbidden states and transitions, partial ordering, cardinality bounds, terminal states, delegation, and budget ceilings, never strict whole-sequence equality.

## Rationale

A model-printed token is a self-report, and feeding self-reports to a deterministic checker launders a probabilistic signal into false ground truth — worse than no conformance layer, because the verdict would be believed. Prose-carried markers change behavior and instrumentation at once, confounding any comparison between skill versions, and instructing a model to announce workflow stages measurably alters its adherence to that workflow — so tokens are script side effects, invariant across compared skill versions, and sidecar emission keeps them out of the agent's context where echoes would reintroduce the contamination. Tolerant contract rules survive legitimate workflow variation where strict sequence equality breaks on the first benign reordering. A skill whose scripts the agent routinely bypasses is a defective skill design, so a missing expected token is a finding about the skill, never a blind spot to paper over. States genuinely internal to model reasoning stay outside normative contracts and are graded in the eval lane, where noise is expected and priced in.

## Product properties

1. A production skill run with no trace sink configured behaves identically to an instrumented run and emits nothing — the emitter is a silent no-op when the trace path is unset and never writes a token to stdout or stderr.
2. A conformance verdict is a pure function of trace and contract — byte-identical for identical inputs — and every violation carries evidence locating it in the trace.
3. An inferred contract is descriptive until a human ratifies it; forbidden states and transitions never enter a contract by inference.

## Verification

- ALWAYS: state tokens are emitted only by skill scripts as side effects of performed actions — a contract-relevant workflow state is realized as a script call
- NEVER: a model-emitted, prose-instructed, or narrative-derived token enters conformance evidence
- ALWAYS: trace events are written to the sidecar path named by the environment, one event per line in append mode; when the path is unset the emitter is a silent no-op and the skill runs unchanged
- NEVER: a token or emitter diagnostic reaches stdout or stderr
- ALWAYS: the emitter shipped inside a plugin is standard-library-only Python per `spx/13-plugin-and-runtime-conventions.adr.md`
- ALWAYS: contract rules express required states, forbidden states and transitions, partial ordering, cardinality bounds, terminal states, delegation, and budget ceilings — never strict whole-sequence equality
- ALWAYS: a conformance verdict derives from the ordered, instance-partitioned trace through a pure function with no model, network, clock, or filesystem access beyond its two inputs
- ALWAYS: a state counts as reached only when its event records success; a failed attempt stays visible in the trace without satisfying a requirement or cardinality bound
- ALWAYS: a normative-contract violation gates the run that produced it; a descriptive-contract violation is recorded as drift and never gates
- NEVER: an inferred contract binds normatively without human ratification
- ALWAYS: a missing expected token is a reported finding about the skill under contract
- NEVER: contract violation and trace absence are conflated — a run that produced no trace is a harness failure, distinct from a skill that violated its contract
