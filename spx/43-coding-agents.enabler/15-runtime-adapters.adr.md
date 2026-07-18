# Coding-Agent Runtime Adapters

Native-agent recovery and agent-message transport are Python 3.13+ standard-library adapters shipped inside the `coding-agents` plugin. Prowl remains the sole authority for persisted pane topology. Recovery accepts exact live pane identities selected from public Prowl evidence, while native runtime and session selection belongs to SPX through the exact `spx agent resume --latest` command. The resumed native agent receives a reassessment instruction and owns whether concrete unfinished work warrants continuation or the recovered process exits again.

## Rationale

Prowl persists and restores its panes, so a plugin-owned pane manifest duplicates runtime state and creates false topology drift. Runtime-specific validation and transport remain plugin-local, while SPX owns cross-runtime native-session selection. Agent judgment handles whether a visibly stopped pane is an obvious recovery candidate and whether resumed work remains authorized; deterministic code validates exact targets and performs bounded delivery without inventing a stop heuristic.

## Invariants

- Repeating native-agent recovery against a selected pane already occupied by its detected native agent launches no additional session and sends no reassessment prompt.
- Recovery never creates, restores, or persists a Prowl pane.
- Message delivery never changes ownership state without a separately validated acknowledgement.
- Delegated mutation authorization preserves one coordination reference across target proposal, observed-state report, and authorization, and every identity matches the live message endpoint for that phase.
- Every subprocess invocation is argument-vector based, bounded by a timeout, and reaped before return.

## Verification

### Testing

- ALWAYS: adapters validate every Prowl response before consuming identity or status fields ([compliance])
- ALWAYS: recovery invokes exactly `spx agent resume --latest` in each selected unoccupied pane and sends the source-owned reassessment instruction to that same pane ([compliance])
- ALWAYS: recovery is idempotent for selected panes already correlated to detected native agents ([property])
- ALWAYS: runtime adapters preserve complete identity values from public Prowl responses and reject non-absolute path identities without expanding or resolving them through the filesystem ([compliance])
- ALWAYS: delegated-mutation envelopes validate target and observed-state identities before delivery ([compliance])
- NEVER: recovery creates panes, enumerates Git worktrees, persists topology, uses `shell=True`, inspects private Prowl storage, scans harness transcripts, reconstructs native session identity, or starts background work ([compliance])

### Audit

- ALWAYS: skills retain pane-selection and continuation judgment while Python owns exact-target validation, bounded launch transport, and correlation ([audit])
- ALWAYS: external commands cross a dependency-injected `CommandRunner` Protocol and the default runner uses argument vectors, captured output, stdin, and bounded timeouts ([audit])
- ALWAYS: tests inject explicit spies or stubs through the runner Protocol when interaction observability or failure simulation requires a double ([audit])
- NEVER: tests replace subprocess, Prowl, or SPX behavior through framework mocks or monkeypatching ([audit])
- NEVER: the coding-agent adapter layer takes ownership of an operating workflow's successful state, retries, checkpoints, or continuation decisions ([audit])
