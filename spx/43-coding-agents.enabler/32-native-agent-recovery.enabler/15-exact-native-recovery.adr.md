# Exact Native Recovery

Native-agent recovery uses a durable prepare manifest followed by post-restart Prowl activation, pane rebinding, exact native-session launch, and exact correlation verification. A source-owned native command registry selects `claude`, `codex`, or `pi` from the prepared agent type and addresses the prepared session identity directly; recency selectors never choose a recovery session.

## Rationale

Prowl materializes terminal panes lazily when a worktree is activated, so pane UUIDs are process-lifetime identities rather than restart-stable addresses. SPX session registration can be absent or can rank another runtime or session as latest. Preserving the pre-restart pane as provenance while binding each prepared candidate to one post-restart pane keeps topology under Prowl and makes native-session selection exact.

## Invariants

- One prepared candidate contains one original pane, absolute worktree, native agent type, native session, liveness evidence, recovery role, and secondary authorization identity.
- One recovery binding maps one original pane to one distinct post-restart pane in the same worktree.
- One native session identity executes in at most one pane and one worktree.
- An exact native command contains the prepared agent type and complete session identity; no recency selector participates in launch or verification.

## Verification

### Testing

- ALWAYS: preparation maps a complete pre-restart candidate set and exact identity evidence to one durable versioned manifest, rejecting stale, done, incomplete, duplicate, mismatched, and unauthorized candidates ([mapping])
- ALWAYS: activation planning maps prepared worktrees to existing panes or source-owned Prowl activation operations, preserving every original-pane identity for post-restart binding ([mapping])
- ALWAYS: recovery maps each exact agent type and session identity to its source-owned native resume command and one post-restart pane binding ([mapping])
- ALWAYS: repeated recovery with every candidate exactly correlated emits no activation or delivery ([property])
- ALWAYS: verification accepts only distinct bindings whose process-backed, native-status, current-session, or exact public-agent evidence matches the prepared worktree, agent type, and native session identity ([compliance])
- NEVER: preparation, activation, launch, or verification accepts transcript recency, rollout recency, terminal presentation, a roster entry without exact session identity, or a latest-session selector as exact evidence ([compliance])

### Audit

- ALWAYS: `/recover-prowl-agents` owns the two-phase prepare/recover lifecycle while `/operate-prowl` remains the sole owner of public Prowl command construction ([audit])
- NEVER: recovery interprets successful delivery as workflow continuation authority; each resumed session applies the source-owned reassessment instruction before acting ([audit])
