# Native Agent Recovery

PROVIDES two-phase native-agent preparation and recovery through exact pre-restart identity and launch evidence, visible exact-root post-restart Prowl activation, pane rebinding, serialized exact native-session launch, exact correlation verification, and separately submitted continuation delivery
SO THAT interrupted coding-agent sessions
CAN resume the complete intended live set and its unsatisfied operator interactions without reviving stale work, duplicating one native session, or depending on restart-stable pane identities

## Assertions

### Mappings

- Each exactly identified native session maps during prepare to one durable candidate containing its original pane, absolute worktree, agent type, complete native session identity, exact native resume locator, applicable native home, evidence, role, and secondary authorization; incomplete, duplicate, and mismatched entries map to a named non-mutating failure while every Prowl status maps to the same eligibility result ([test](tests/test_native_agent_recovery.mapping.l1.py))
- Each prepared candidate maps after restart to one exact existing pane or one source-owned Prowl activation request for its worktree; an absent pane binds only from an `exact-root` result whose returned path and pane identify that prepared target, never from blind worktree enumeration ([test](tests/test_native_agent_recovery.mapping.l1.py))
- Each bound candidate maps to `resumed` when unoccupied, `already-correlated` when occupied by its exact agent type and session, or a named non-mutating failure when absent, duplicated, mismatched, or occupied by another process ([test](tests/test_native_agent_recovery.mapping.l1.py))
- Each verified candidate other than the active controller maps to one separately delivered reassessment instruction until its session identity appears in the durable reassessed set; the active controller maps to no self-delivery ([test](tests/test_native_agent_recovery.mapping.l1.py))
- One candidate per worktree maps to primary recovery; multiple candidates in one worktree map to rejection unless exactly one is primary and every distinct secondary session carries explicit operator authorization ([test](tests/test_native_agent_recovery.mapping.l1.py))

### Properties

- Repeating recovery after every prepared candidate has one exact distinct post-restart correlation and every non-controller session is durably reassessed emits no activation, native command, or reassessment instruction ([test](tests/test_native_agent_recovery.property.l1.py))
- Preparation and verification reject every evidence value outside the source-owned process, native-status, current-session, exact-public-agent, and operator-confirmation contract ([test](tests/test_native_agent_recovery.property.l1.py))

### Compliance

- ALWAYS: prepare captures a fresh allowlist before restart and preserves every original pane, worktree, agent type, session, resume locator, applicable native home, evidence, role, secondary-authorization identity, and reassessed-session identity in a versioned manifest ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery activates absent panes through authorized `/operate-prowl` `open` against prepared paths only, requires exact-root path-and-pane results, preserves Prowl-returned post-restart pane identities, and never scans Git worktrees or filesystem directories for activation targets ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery serializes exact native launches sharing one native home through input-ready state and selects Claude's recommended summary resumption when that exact-session prompt appears ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: exact native launch and reassessment use separate checked sends whose public input records prove trailing Enter was sent, so interactive launch cannot buffer continuation prose and editor prefill cannot masquerade as delivery ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery verifies one process-backed, native-status, current-session, or exact public-agent correlation matching each candidate's distinct post-restart pane, worktree, agent type, and complete native session identity ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery preserves absolute public Prowl path identities verbatim and rejects non-absolute path identities without filesystem expansion or resolution ([test](tests/test_native_agent_recovery.compliance.l1.py))
- NEVER: recovery uses `spx agent resume --latest`, Prowl status, transcript or rollout recency, terminal presentation, or a sessionless roster entry to select or verify a native session ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: reassessment treats restart, authentication repair, and tool failure as transport interruption; completes the last unsatisfied operator request under its original constraints; restores pending questions, selections, approvals, and blockers without choosing for the operator; and stops only after every operator request is satisfied and the workflow completes or is explicitly cancelled ([audit])
- NEVER: recovery closes a pane, launches an identity absent from the prepared manifest, types into an occupied mismatched pane, treats delivery as workflow success, asks again for authority already granted, or substitutes repository completion for an unsatisfied operator response ([audit])
