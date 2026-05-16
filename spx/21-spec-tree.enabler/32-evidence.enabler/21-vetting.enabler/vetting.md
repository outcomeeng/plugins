# Vetting

PROVIDES the cross-lens contract — persistence shape, validation discipline, agent shape — under which every vetting lens (judgment-style review of working changes, mechanical audit of spec-tree nodes, and any other lens conforming to this contract) operates against a branch-scoped record of evidence
SO THAT lens authors and the thin wrapper agents that wrap each lens
CAN write and consume lenses against one persistence model, one validation discipline, and one agent shape

## Assertions

### Compliance

- ALWAYS: every lens persists its machine-readable result and human-readable surface through `spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/21-thread-store.enabler/thread-store.md` — direct filesystem writes from a lens skill or agent break backend pluggability ([review])
- ALWAYS: every lens emits one structured machine-readable result document conforming to its own JSON schema, alongside one human-readable markdown surface — the carrier+payload pair is the lens's externally observable output ([review])
- ALWAYS: every lens's validation policy — schema conformance plus any consistency invariants — is encoded in a Python module under the lens skill's `scripts/` directory and exposed through a CLI arbiter that the wrapper agent invokes to validate every result it emits ([review])
- ALWAYS: every lens is invoked through a thin wrapper agent declared under `plugins/spec-tree/agents/` with `model: sonnet`, `tools: Bash, Read, Skill`, and `skills:` listing the lens skill — the agent holds no validation policy and no I/O policy of its own ([review])
- ALWAYS: every lens uses the branch-slug derivation re-exported by thread-store — slug consistency across lenses keeps a branch's vetting records co-located on disk and addressable by the same key across surfaces ([review])
- NEVER: a lens reads or writes a backend-specific path directly from skill prose or agent prose — every read and write routes through the thread-store CRUD interface so backend swap is a configuration concern, never a content change ([review])
- NEVER: a lens hand-validates the JSON it just emitted — the wrapper agent invokes the lens's CLI arbiter and treats its exit code as the validity signal; duplicate validation policy in agent prose drifts from the policy module ([review])
- NEVER: a lens duplicates the branch-slug derivation rule or invents its own — slug derivation is one function, re-exported by thread-store from the canonical helper ([review])
