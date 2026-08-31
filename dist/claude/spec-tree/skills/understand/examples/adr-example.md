# Node State Derivation

Node state is derived from the presence of a spec, linked evidence, implementation, and the evidence result. The derived states are `Declared`, `Specified`, `Failing`, and `Passing`; no state field exists in a committed artifact.

## Rationale

Stored state requires manual synchronization and drifts from the artifacts it summarizes. Derivation keeps the state tied to the declaration → evidence → implementation chain. Rejected alternatives: a `status.yaml` per node and CI-badge integration.

## Invariants

- State is a pure function of the spec, linked evidence, implementation presence, and evidence result.
- `Declared` means the spec exists without evidence; `Specified` means spec and evidence exist while implementation is absent; `Failing` and `Passing` distinguish the evidence result when implementation exists.

## Verification

### Testing

- ALWAYS: compute node state from the current declaration, evidence, implementation, and evidence result ([property])
- ALWAYS: map each artifact combination to exactly one of `Declared`, `Specified`, `Failing`, or `Passing` ([mapping])
- NEVER: store node state in a committed file ([compliance])
- NEVER: allow a manual state override ([scenario])
