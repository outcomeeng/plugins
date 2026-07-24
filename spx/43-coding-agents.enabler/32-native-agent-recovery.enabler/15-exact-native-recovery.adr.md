# Exact Native Recovery

Native-agent recovery uses a durable prepare manifest followed by visible exact-root Prowl activation, pane rebinding, serialized exact native-session launch, exact correlation verification, and separately submitted reassessment. A source-owned native command registry selects `claude`, `codex`, or `pi` from the prepared agent type, exact resume locator, and applicable native home; recency selectors and Prowl workflow status never choose a recovery session. Native launch and continuation prose never share one transport.

## Rationale

Prowl preserves sidebar worktree topology independently from instantiated terminal panes: an unentered known worktree is absent from the pane inventory until visible activation creates its first tab. Preserving the pre-restart pane as provenance while opening only prepared exact-root worktrees and binding each returned pane keeps topology under Prowl without enumerating filesystem worktrees. Prowl workflow status is advisory — a `done` projection can retain unfinished native work — while exact native identity remains authoritative. Interactive launchers consume terminal input, shared-home Codex processes contend during concurrent initialization, and old Claude sessions can require summary resumption, so launches are serialized through input-ready state before separately submitted continuation. Native session storage can also move outside a worktree's default lookup scope, so the prepare manifest preserves the exact Claude resume locator and applicable Codex home that resolve the selected identity.

## Invariants

- One prepared candidate contains one original pane, absolute worktree, native agent type, native session, exact resume locator, applicable native home, liveness evidence, recovery role, secondary authorization identity, and durable reassessment state.
- One recovery binding maps one original pane to one distinct post-restart pane in the same worktree.
- One native session identity executes in at most one pane and one worktree.
- An exact native command contains only the prepared agent type, resume locator or complete session identity, and applicable native home; no continuation prose, Prowl status, or recency selector participates in launch or verification.
- Activation opens only a prepared worktree and accepts only an exact-root result whose returned path and pane bind that target; no Git-worktree or filesystem enumeration creates recovery targets.
- Native launches sharing one home are serialized through input-ready state.
- Reassessment planning requires one checked stable-screen context read for every verified pane, including the controller and already-correlated panes; one absent or failed read permits no continuation send.
- Reassessment reaches a verified non-controller session through a separate checked send whose public input record proves trailing Enter submission exactly once per prepared manifest.
- Explicit plans remain unfinished until their own acceptance scope is reconciled against delivered work; a separate useful result never absorbs them.

## Verification

### Testing

- ALWAYS: preparation maps a complete pre-restart candidate set and exact identity and launch evidence to one durable versioned manifest, rejecting incomplete, duplicate, mismatched, and unauthorized candidates while treating every Prowl status as advisory ([mapping])
- ALWAYS: activation planning maps prepared worktrees to existing panes or source-owned exact-root Prowl activation operations, preserving every original-pane identity for post-restart binding and never enumerating filesystem worktrees ([mapping])
- ALWAYS: recovery maps each exact agent type, session identity, resume locator, and applicable native home to its source-owned native resume command and one post-restart pane binding ([mapping])
- ALWAYS: the complete verified binding set maps with one checked pane read per binding to reassessment planning; absent or failed reads map to zero delivery, while verified non-controller candidates not present in the reassessed set map after the read barrier to one separate delivery ([mapping])
- ALWAYS: repeated recovery with every candidate exactly correlated and reassessed emits no activation or delivery ([property])
- ALWAYS: verification accepts only distinct bindings whose process-backed, native-status, current-session, or exact public-agent evidence matches the prepared worktree, agent type, and native session identity ([compliance])
- NEVER: preparation, activation, launch, or verification accepts transcript recency, rollout recency, terminal presentation, a roster entry without exact session identity, or a latest-session selector as exact evidence ([compliance])

### Audit

- ALWAYS: `/recover-prowl-agents` owns the two-phase prepare/recover lifecycle while `/operate-prowl` remains the sole owner of public Prowl command construction ([audit])
- ALWAYS: the reassessment instruction prioritizes the last unsatisfied operator request, reconciles every explicitly presented plan and context artifact against delivered acceptance scope, retries responses interrupted by authentication or tool failure, restores pending operator interactions without selecting them, preserves original constraints and authority, and asks rather than exits when prior state cannot be classified ([audit])
- NEVER: recovery plans or sends continuation before every verified pane is read, interprets successful delivery as workflow continuation authority, treats distinct useful work as completion of an unreconciled plan, treats restart metadata as cancellation, substitutes repository completion for an unanswered request, or asks for authorization the operator already supplied ([audit])
