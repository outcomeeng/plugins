# Native Agent Recovery

PROVIDES bounded native-agent recovery into exact restored Prowl panes selected from pre-restart liveness and session evidence
SO THAT interrupted coding-agent sessions
CAN resume through SPX without reviving stale work, duplicating one native session, or treating saved history as proof of prior activity

## Assertions

### Mappings

- Each exact selected Prowl pane and expected native session maps to `resumed` when unoccupied, `already-correlated` when occupied by that session, or a named non-mutating failure when absent, duplicated, mismatched, or occupied by another process ([test](tests/test_native_agent_recovery.mapping.l1.py))
- One candidate per worktree maps to primary recovery; multiple candidates in one worktree map to rejection unless exactly one is primary and every distinct secondary session carries explicit operator authorization ([test](tests/test_native_agent_recovery.mapping.l1.py))
- A candidate backed by pre-restart live-process evidence or explicit operator confirmation maps to eligibility, while pane presentation, a saved transcript or rollout, and session-file recency alone map to leaving the session stopped ([audit])

### Properties

- Repeating recovery after every selected pane has one correlated native agent with the expected distinct session identity sends no command or reassessment prompt ([test](tests/test_native_agent_recovery.property.l1.py))
- Recovery rejects every candidate evidence value outside the source-owned liveness and operator-confirmation contract ([test](tests/test_native_agent_recovery.property.l1.py))

### Compliance

- ALWAYS: recovery invokes exactly `spx agent resume --latest` and sends the source-owned reassessment instruction plus the expected complete native session identity and recovery role in every selected unoccupied pane, leaving native runtime selection exclusively to SPX ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: each newly resumed native agent continues only when its native session identity matches the expected candidate and authoritative evidence shows concrete unfinished work; completed, superseded, `owned_elsewhere`, deliberately terminated, or unclear work exits without mutation or background activity ([audit])
- ALWAYS: recovery verifies one detected native agent with the expected distinct native session identity correlated to each selected pane after the bounded launch phase ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery preserves absolute public Prowl path identities verbatim and rejects non-absolute path identities without filesystem expansion or resolution ([test](tests/test_native_agent_recovery.compliance.l1.py))
- NEVER: recovery creates, restores, focuses, or closes panes, enumerates Git worktrees, or types into an unselected pane ([test](tests/test_native_agent_recovery.compliance.l1.py))
- NEVER: recovery uses saved eligibility evidence to create or reconstruct Prowl topology, reconstructs native session identity from transcripts, or treats resume as workflow success or continuation authority ([audit])
- NEVER: recovery selects a session because a transcript, rollout, pane roster entry, or prior terminal presentation exists without pre-restart live-process evidence or explicit operator confirmation ([audit])
