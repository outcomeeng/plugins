# Conformance Verification

PROVIDES Outcome Engineering governance for workflow-conformance evidence — script-emitted trace semantics, conformance contracts, deterministic conformance verdicts, and contract provenance
SO THAT skill and subagent behavior across every product consuming the methodology
CAN be judged against declared workflow contracts by a deterministic checker instead of model self-report or model judgment

## Assertions

- ALWAYS: skill-instrumentation, trace, contract, and verdict semantics derive from `spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/15-skill-instrumentation.pdr.md`
- ALWAYS: trace-emission governance lives under `spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/21-trace-emission.enabler/trace-emission.md` when it concerns the trace event schema, emitter mechanics, or sidecar discipline
- ALWAYS: conformance-checking governance lives under `spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/31-conformance-checking.enabler/conformance-checking.md` when it concerns verdict computation, violation evidence, or checker purity
- ALWAYS: contract-inference governance lives under `spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/31-contract-inference.enabler/contract-inference.md` when it concerns deriving proposed contracts from observed traces or ratifying them
