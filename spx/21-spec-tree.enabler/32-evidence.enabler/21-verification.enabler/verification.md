# Verification

PROVIDES a shared contract — persistence shape, validation discipline, wrapper-agent shape — under which verification skills (judgment-style review of working changes, mechanical audit of spec-tree nodes, and any future skill that ships under this umbrella) produce branch-scoped evidence records
SO THAT authors of verification skills and the thin wrapper agents that drive them
CAN compose against one persistence model, one validation discipline, and one agent shape

## Assertions

### Compliance

- ALWAYS: every verification skill persists its machine-readable result and human-readable surface through `spx/21-spec-tree.enabler/32-evidence.enabler/21-verification.enabler/21-thread-store.enabler/thread-store.md` — direct filesystem writes from skill prose or agent prose break backend pluggability ([review])
- ALWAYS: every verification skill emits one structured machine-readable result document conforming to its own JSON schema, alongside one human-readable markdown surface — the carrier+payload pair is the skill's externally observable output ([review])
- ALWAYS: every verification skill's validation policy — schema conformance plus any consistency invariants — is encoded in a Python module under the skill's `scripts/` directory and exposed through a CLI arbiter that the wrapper agent invokes to validate every result before persistence ([review])
- ALWAYS: every verification skill is driven by a thin wrapper agent declared under `plugins/spec-tree/agents/` with `model: sonnet`, `tools: Bash, Read, Skill`, and `skills:` listing the skill — the wrapper agent holds no validation policy and no I/O policy of its own ([review])
- ALWAYS: every verification skill addresses branch-scoped records through the slug helper re-exported by thread-store — one slug rule across all verification skills keeps a branch's records co-located on disk and addressable by the same key across surfaces ([review])
- NEVER: a verification skill reads or writes a backend-specific path directly from skill prose or agent prose — every read and write routes through the thread-store CRUD interface so backend swap is a configuration concern, never a content change ([review])
- NEVER: a verification skill hand-validates the JSON it just emitted — the wrapper agent invokes the skill's CLI arbiter and treats its exit code as the validity signal; duplicate validation policy in agent prose drifts from the policy module ([review])
- NEVER: a verification skill duplicates the branch-slug derivation rule or invents its own — slug derivation is one function, re-exported by thread-store from the canonical helper ([review])
