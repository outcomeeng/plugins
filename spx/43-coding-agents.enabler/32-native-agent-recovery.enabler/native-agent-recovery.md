# Native Agent Recovery

PROVIDES two-phase native-agent preparation and recovery through exact pre-restart identity evidence, lazy post-restart Prowl activation, pane rebinding, exact native-session launch, and exact correlation verification
SO THAT interrupted coding-agent sessions
CAN resume as the complete intended live set without reviving stale work, duplicating one native session, or depending on restart-stable pane identities

## Assertions

### Mappings

- Each process-backed live native session maps during prepare to one durable candidate containing its original pane, absolute worktree, agent type, complete native session identity, evidence, role, and secondary authorization; done, stale, incomplete, duplicate, and mismatched entries map to a named non-mutating failure ([test](tests/test_native_agent_recovery.mapping.l1.py))
- Each prepared candidate maps after restart to one exact existing pane or one source-owned Prowl activation request for its worktree, then to one distinct post-restart pane binding that preserves the original pane identity ([test](tests/test_native_agent_recovery.mapping.l1.py))
- Each bound candidate maps to `resumed` when unoccupied, `already-correlated` when occupied by its exact agent type and session, or a named non-mutating failure when absent, duplicated, mismatched, or occupied by another process ([test](tests/test_native_agent_recovery.mapping.l1.py))
- One candidate per worktree maps to primary recovery; multiple candidates in one worktree map to rejection unless exactly one is primary and every distinct secondary session carries explicit operator authorization ([test](tests/test_native_agent_recovery.mapping.l1.py))

### Properties

- Repeating recovery after every prepared candidate has one exact distinct post-restart correlation emits no activation, native command, or reassessment prompt ([test](tests/test_native_agent_recovery.property.l1.py))
- Preparation and verification reject every evidence value outside the source-owned process, native-status, current-session, exact-public-agent, and operator-confirmation contract ([test](tests/test_native_agent_recovery.property.l1.py))

### Compliance

- ALWAYS: prepare captures a fresh allowlist before restart and preserves every original pane, worktree, agent type, session, evidence, role, and secondary-authorization identity in a versioned manifest ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery activates absent worktrees through `/operate-prowl`, preserves Prowl-returned post-restart pane identities, and sends one source-owned exact native resume command plus reassessment instruction to each selected unoccupied pane ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery verifies one process-backed, native-status, current-session, or exact public-agent correlation matching each candidate's distinct post-restart pane, worktree, agent type, and complete native session identity ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery preserves absolute public Prowl path identities verbatim and rejects non-absolute path identities without filesystem expansion or resolution ([test](tests/test_native_agent_recovery.compliance.l1.py))
- NEVER: recovery uses `spx agent resume --latest`, transcript or rollout recency, terminal presentation, or a sessionless roster entry to select or verify a native session ([test](tests/test_native_agent_recovery.compliance.l1.py))
- NEVER: recovery closes a pane, launches an identity absent from the prepared manifest, types into an occupied mismatched pane, or treats delivery as workflow success or continuation authority ([audit])
