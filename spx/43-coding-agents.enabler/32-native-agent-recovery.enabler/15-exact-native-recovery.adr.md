# Exact Native Recovery

Native-agent recovery uses a durable prepare manifest followed by post-restart Prowl activation, pane rebinding, exact native-session launch, exact correlation verification, and separately settled reassessment. A source-owned native command registry selects `claude`, `codex`, or `pi` from the prepared agent type, exact resume locator, and applicable native home; recency selectors never choose a recovery session. Native launch and continuation prose never share one transport.

## Rationale

Prowl materializes terminal panes lazily when a worktree is activated, so pane UUIDs are process-lifetime identities rather than restart-stable addresses. SPX session registration can be absent or can rank another runtime or session as latest. Preserving the pre-restart pane as provenance while binding each prepared candidate to one post-restart pane keeps topology under Prowl and makes native-session selection exact. Interactive native launchers consume the terminal input stream, so continuation prose sent with a launch command remains buffered or is interpreted as an extra launcher argument; exact verification therefore precedes a separate continuation send. Native session storage can also move outside a worktree's default lookup scope, so the prepare manifest preserves the exact Claude resume locator and applicable Codex home that resolve the selected identity.

## Invariants

- One prepared candidate contains one original pane, absolute worktree, native agent type, native session, exact resume locator, applicable native home, liveness evidence, recovery role, secondary authorization identity, and durable reassessment state.
- One recovery binding maps one original pane to one distinct post-restart pane in the same worktree.
- One native session identity executes in at most one pane and one worktree.
- An exact native command contains only the prepared agent type, resume locator or complete session identity, and applicable native home; no continuation prose or recency selector participates in launch or verification.
- Reassessment reaches a verified non-controller session through a separate checked send exactly once per prepared manifest.

## Verification

### Testing

- ALWAYS: preparation maps a complete pre-restart candidate set and exact identity and launch evidence to one durable versioned manifest, rejecting stale, done, incomplete, duplicate, mismatched, and unauthorized candidates ([mapping])
- ALWAYS: activation planning maps prepared worktrees to existing panes or source-owned Prowl activation operations, preserving every original-pane identity for post-restart binding ([mapping])
- ALWAYS: recovery maps each exact agent type, session identity, resume locator, and applicable native home to its source-owned native resume command and one post-restart pane binding ([mapping])
- ALWAYS: verified non-controller candidates not present in the manifest's reassessed set map to one separate reassessment delivery, while settled reassessment extends that set ([mapping])
- ALWAYS: repeated recovery with every candidate exactly correlated and reassessed emits no activation or delivery ([property])
- ALWAYS: verification accepts only distinct bindings whose process-backed, native-status, current-session, or exact public-agent evidence matches the prepared worktree, agent type, and native session identity ([compliance])
- NEVER: preparation, activation, launch, or verification accepts transcript recency, rollout recency, terminal presentation, a roster entry without exact session identity, or a latest-session selector as exact evidence ([compliance])

### Audit

- ALWAYS: `/recover-prowl-agents` owns the two-phase prepare/recover lifecycle while `/operate-prowl` remains the sole owner of public Prowl command construction ([audit])
- ALWAYS: the reassessment instruction prioritizes the last unsatisfied operator request, retries responses interrupted by authentication or tool failure, restores pending operator interactions without selecting them, preserves original constraints and authority, and asks rather than exits when prior state cannot be classified ([audit])
- NEVER: recovery interprets successful delivery as workflow continuation authority, treats restart metadata as cancellation, substitutes repository completion for an unanswered request, or asks for authorization the operator already supplied ([audit])
