# Native Agent Recovery

PROVIDES bounded native-agent recovery into exact Prowl panes selected from live public evidence
SO THAT stopped coding-agent sessions
CAN resume through SPX and re-evaluate whether work should continue without duplicating Prowl topology or keeping deliberately stopped sessions alive

## Assertions

### Mappings

- Each exact selected Prowl pane maps to `resumed` when unoccupied, `already-correlated` when occupied by one detected native agent, or a named non-mutating failure when absent, duplicated, or occupied by another process ([test](tests/test_native_agent_recovery.mapping.l1.py))
- Obvious visible evidence of a terminated coding-agent session maps to recovery selection, while an ordinary shell, conflicting evidence, or uncertain intent maps to leaving the pane stopped until the operator decides ([audit])

### Properties

- Repeating recovery after every selected pane has one correlated native agent sends no command or reassessment prompt ([test](tests/test_native_agent_recovery.property.l1.py))

### Compliance

- ALWAYS: recovery invokes exactly `spx agent resume --latest` and sends the source-owned reassessment instruction in every selected unoccupied pane, leaving native runtime and session selection exclusively to SPX ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: each newly resumed native agent continues only when authoritative evidence shows concrete unfinished work; completed, deliberately terminated, or unclear work exits without mutation or background activity ([audit])
- ALWAYS: recovery verifies one detected native agent correlated to each selected pane after the bounded launch phase ([test](tests/test_native_agent_recovery.compliance.l1.py))
- ALWAYS: recovery preserves absolute public Prowl path identities verbatim and rejects non-absolute path identities without filesystem expansion or resolution ([test](tests/test_native_agent_recovery.compliance.l1.py))
- NEVER: recovery creates, restores, focuses, or closes panes, enumerates Git worktrees, or types into an unselected pane ([test](tests/test_native_agent_recovery.compliance.l1.py))
- NEVER: recovery persists topology or session identity, reconstructs native session identity, or treats resume as workflow success or continuation authority ([audit])
