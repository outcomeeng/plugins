# Exact Native Recovery

Native-agent recovery uses a durable prepare manifest followed by visible exact-root Prowl activation, pane rebinding, serialized exact native-session launch, exact correlation verification, and separately submitted reassessment. The controller running the recovery attests the one pane it occupies, binding its own current-session candidate where the public agent roster cannot identify it. The manifest names the one native session entitled to drive that recovery and is the sole resume state, so an interrupted run continues from what the manifest records rather than from the driving session's memory. A source-owned native command registry selects `claude`, `codex`, or `pi` from the prepared agent type, exact resume locator, and applicable native home; recency selectors and Prowl workflow status never choose a recovery session. Native launch and continuation prose never share one transport.

## Rationale

Prowl preserves sidebar worktree topology independently from instantiated terminal panes: an unentered known worktree is absent from the pane inventory until visible activation creates its first tab. Preserving the pre-restart pane as provenance while opening only prepared exact-root worktrees and binding each returned pane keeps topology under Prowl without enumerating filesystem worktrees. Prowl workflow status is advisory — a `done` projection can retain unfinished native work — while exact native identity remains authoritative. Interactive launchers consume terminal input, shared-home Codex processes contend during concurrent initialization, and old Claude sessions can require summary resumption, so launches are serialized through input-ready state before separately submitted continuation. Native session storage can also move outside a worktree's default lookup scope, so the prepare manifest preserves the exact Claude resume locator and applicable Codex home that resolve the selected identity. That same storage divergence leaves the controller unidentified in the public agent roster when its native transcript resolves under a project root other than its pane's working directory, so strict roster matching reads the controller's own pane as a mismatched occupant and stops the recovery it is running. The controller is the one participant that knows its own pane by direct evidence rather than inference, so it attests that pane and the attestation binds its current-session candidate; every other pane keeps strict roster matching, the attestation is checked against the candidate's worktree, agent type, and session before it binds, and the attested pane is never relaunched.

## Invariants

- One prepared candidate contains one original pane, absolute worktree, native agent type, native session, exact resume locator, applicable native home, liveness evidence, recovery role, secondary authorization identity, and durable reassessment state.
- One recovery binding maps one original pane to one distinct post-restart pane in the same worktree.
- One native session identity executes in at most one pane and one worktree.
- An exact native command contains only the prepared agent type, resume locator or complete session identity, and applicable native home; no continuation prose, Prowl status, or recency selector participates in launch or verification.
- Activation opens only a prepared worktree and accepts only an exact-root result whose returned path and pane bind that target; no Git-worktree or filesystem enumeration creates recovery targets.
- A controller-pane attestation binds at most one pane — the one its own occupant declares it runs in — to the single current-session candidate, and that pane is never activated or relaunched.
- The prepared manifest names the one native session entitled to drive recovery; a recovery driven by any other session performs no mutation.
- The manifest is recovery's only resume state, so each step is re-entrant against its own recorded result and a step the manifest records is never performed a second time.
- Native launches sharing one home are serialized through input-ready state.
- Reassessment planning requires one checked stable-screen context read for every verified pane, including the controller and already-correlated panes; one absent or failed read permits no continuation send.
- Reassessment reaches only a verified non-controller session whose recovery destroyed something for it, through a separate checked send whose public input record proves trailing Enter submission exactly once per prepared manifest.
- Explicit plans remain unfinished until their own acceptance scope is reconciled against delivered work; a separate useful result never absorbs them.

## Verification

- ALWAYS: preparation records the driving session's exact native identity, and a recovery entered by any other native session halts before its first mutation naming the recorded driver
- ALWAYS: an interrupted recovery resumes from the durable manifest at the first step whose result that manifest does not record, performing no step it already records
- NEVER: a repeated recovery step emits a second activation, native launch, pane input, or continuation delivery for a result the manifest already records

### Testing

- ALWAYS: preparation maps a complete pre-restart candidate set and exact identity and launch evidence to one durable versioned manifest, rejecting incomplete, duplicate, mismatched, and unauthorized candidates ([mapping])
- ALWAYS: activation planning maps prepared worktrees to existing panes or source-owned exact-root Prowl activation operations, preserving every original-pane identity for post-restart binding and never enumerating filesystem worktrees ([mapping])
- ALWAYS: recovery maps each exact agent type, session identity, resume locator, and applicable native home to its source-owned native resume command and one post-restart pane binding ([mapping])
- ALWAYS: a controller-pane attestation maps to one binding for the single current-session candidate whose worktree, agent type, and native session the attested pane identifies, and every attestation failing that identification maps to a named non-mutating failure ([mapping])
- ALWAYS: the complete verified binding set maps with one checked pane read per binding to reassessment planning; absent or failed reads map to zero delivery, while after the read barrier each verified non-controller candidate carrying a supplied destroyed fact maps to one separate delivery and every other maps to a recorded judged-intact identity ([mapping])
- ALWAYS: any non-empty Prowl status a live agent reports leaves preparation eligibility unchanged; the vocabulary belongs to Prowl and no source models it ([property])
- ALWAYS: repeated recovery with every candidate exactly correlated and reassessed emits no activation or delivery ([property])
- ALWAYS: verification accepts only distinct bindings whose process-backed, native-status, current-session, or exact public-agent evidence matches the prepared worktree, agent type, and native session identity ([compliance])
- NEVER: preparation, activation, launch, or verification accepts transcript recency, rollout recency, terminal presentation, a roster entry without exact session identity, or a latest-session selector as exact evidence ([compliance])

### Audit

- ALWAYS: `/recover-prowl-agents` owns the two-phase prepare/recover lifecycle while `/operate-prowl` remains the sole owner of public Prowl command construction ([audit])
- ALWAYS: the reassessment instruction states only what the restart destroyed for its one recipient, judged from that recipient's own pane read, and leaves reconciliation, the next action, and any pending operator interaction to the session that holds the conversation ([audit])
- ALWAYS: every send and key to a recovered pane follows one immediately preceding read of that pane's dialog state, and every continuation instruction is one short line carrying the non-controller boundary and the destroyed fact alone ([audit])
- NEVER: recovery plans or sends continuation before every verified pane is read, delivers one instruction to every recipient, sends input to a pane holding a dialog its own authority does not cover, interprets successful delivery as workflow continuation authority, treats distinct useful work as completion of an unreconciled plan, treats restart metadata as cancellation, substitutes repository completion for an unanswered request, or asks for authorization the operator already supplied ([audit])
