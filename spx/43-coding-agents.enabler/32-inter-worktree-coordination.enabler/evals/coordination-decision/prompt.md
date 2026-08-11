<!-- Generated from the complete producer at src/plugins/coding-agents/skills/coordinate-agents/SKILL.md. -->

Apply the complete coordination producer below to the supplied authoritative evidence. Return only the producer's structured JSON verdict. Do not invoke tools or send messages during this evaluation.

---
name: coordinate-agents
description: >-
  ALWAYS invoke this skill when coding agents in separate worktrees may overlap, depend on each other, share an external blocker, or need ownership coordination.
allowed-tools: Skill
---

<objective>
A structured coordination decision that preserves independent workflow ownership.
</objective>

<evidence_model>

Use only explicit SPX facts, public runtime projections, checked command results, and operator-confirmed external changes as authoritative evidence. Treat prose inference as advisory. A missing authoritative fact is a signal gap, never permission to scan harness transcripts.

</evidence_model>

<workflow>

1. Identify every participant with complete agent, pane, worktree, branch, repository, and applicable run identities. An operator names a participant by worktree, repository, or working directory rather than by pane UUID; resolve that naming to a complete identity through `/operate-prowl`'s operator-target resolution, and report participants back to the operator in the terms they used.
2. Classify the relationship from authoritative evidence:
   - `ownership-overlap`: paths, concerns, or an external mutation overlap.
   - `dependency-handoff`: one workflow has a checked fact another consumes.
   - `shared-blocker`: workflows name the same authoritative external-condition key.
   - `independent`: authoritative evidence explicitly establishes no overlap, dependency, shared mutation, or correlated blocker.
   - `signal-gap`: authoritative evidence is absent or cannot establish either a relationship or independence. Advisory prose alone ALWAYS maps here.
3. Emit the structured verdict before delivery:

```json
{
  "status": "coordination-needed | no-coordination | signal-gap",
  "reason": "ownership-overlap | dependency-handoff | shared-blocker | independent | insufficient-evidence",
  "participants": [],
  "operatorAction": null,
  "messages": []
}
```

For a shared blocker, replace `operatorAction: null` with this complete object:

```json
{
  "externalConditionKey": "<complete authoritative key>",
  "status": "<operator-confirmed status>"
}
```

Preserve every input participant in the verdict's `participants` array, dropping none — including a participant the classified relationship does not involve. An operator-named target resolved in step 1 joins that array as a complete identity, because it is a party to the coordination; resolution adds, never replaces. The array therefore holds exactly the input participants plus any resolved target, and never a participant no evidence names.

Each message carries every field in the source-owned message contract: complete `recipientPath` equal to the recipient participant's absolute worktree, complete `toPane` UUID, `kind`, `subject`, `facts`, `request`, `coordinationReference`, `mutationTarget`, `observedState`, and `accepted`. `facts` is always an array of strings, including branches with exactly one fact. Use null for every field that does not apply. `kind` MUST be exactly `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. Omit or set `coordinationReference` to null for initiating proposals and facts so `/message-agents` creates a UUID; every response kind preserves the active proposal UUID. Only an `acknowledgement` carries boolean `accepted`; every other kind carries `accepted: null`.

Use these branch-owned payloads:

| Branch                      | `subject`                          | `facts`                                                                                                               | `request`                                                                                                   |
| --------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Ownership proposal          | `Ownership overlap`                | one `overlap=<path-or-concern>` string per checked overlapping item                                                   | `Accept or reject this ownership proposal.`                                                                 |
| Delegated-mutation proposal | `Delegated mutation ownership`     | `target identity and state are authoritative`                                                                         | `Report exact pre-mutation state and accept or reject ownership.`                                           |
| Dependency handoff          | `Dependency fact`                  | the checked dependency fact only                                                                                      | null                                                                                                        |
| Production request          | `Dependency production request`    | the exact checked `requestedArtifact` value, then `returnPane=<requester-pane>` and `handbackCommand=<exact-command>` | `Send the handback command when the result is written.`                                                     |
| Shared-blocker recovery     | `Shared blocker restored`          | `externalConditionKey=<key>` and `status=<operator-confirmed-status>`                                                 | null                                                                                                        |
| Mutation authorization      | `Delegated mutation authorization` | `accepted ownership and observed state match the target`                                                              | `Recreate the required change in the target worktree; do not mutate or transfer from the sibling worktree.` |

4. Apply the protocol:

- A checked path or concern overlap produces an `ownership-proposal` with one `overlap=<path-or-concern>` fact per overlapping item; its boundary remains proposed until a matching accepted acknowledgement arrives.
- A dependency handoff sends `kind: "fact"` with checked facts and `request: null`, not another workflow's continuation instructions.
- A dependency handoff that asks another workflow to *produce* something is a production request — its own branch, distinct from handing over an already-checked dependency fact. It still sends `kind: "fact"`. Its first `facts` string is the exact checked `requestedArtifact` value unchanged, with no field-name prefix; the next two are exactly `returnPane=<requester-pane>` and `handbackCommand=<exact-command>`. Its `request` is exactly `Send the handback command when the result is written.` The requester cannot poll — polling loops are blocked by design — so a request with no return path is one the requester can never learn the answer to, and the operator ends up relaying it by hand. When the produced artifact is a file, the file carries the payload and the handback carries only the signal and the complete path. Emit `status: "signal-gap"`, `reason: "insufficient-evidence"`, and no message when the requester's own pane is not among the authoritative participants, since a return path cannot be fabricated.
- A delegated mutation begins with an `ownership-proposal` whose `mutationTarget` contains the recipient's exact pane UUID, worktree path, branch, repository, full HEAD SHA, and status. The recipient performs no mutation until it returns both a matching `acknowledgement` with `accepted: true` and a `mutation-state` message with the same coordination reference and an `observedState` containing its exact worktree, branch, repository, full HEAD SHA, and status.
- When delegated-mutation evidence has no `observedState`, emit one ownership proposal carrying the exact target and request the state report.
- Treat `acceptedAcknowledgement` as authoritative only when its kind is `acknowledgement`, `accepted` is true, its coordination reference equals the active proposal reference, its sender is the target participant, and its recipient is the coordinating participant. When observed state exists but acknowledgement evidence is missing, rejected, or mismatched, emit `status: "coordination-needed"`, `reason: "ownership-overlap"`, and no message.
- When any observed worktree, branch, repository, HEAD, or status value differs from the target, emit `status: "coordination-needed"`, `reason: "ownership-overlap"`, and no message. A mismatch produces no authorization.
- Emit one `mutation-authorization` only when the accepted acknowledgement is valid and every observed value matches. Target the exact recipient pane, preserve the active coordination reference, echo the target and observed state, and set `request` exactly to `Recreate the required change in the target worktree; do not mutate or transfer from the sibling worktree.`
- Every sibling worktree stays read-only to both workflows. Transfer an exact commit only through a separate ownership proposal and accepted acknowledgement; delegated-mutation authorization never transfers a sibling commit.
- A shared blocker produces exactly one non-null `operatorAction` carrying its complete `externalConditionKey` and operator-confirmed `status`. When restoration is operator-confirmed, keep that action record and produce one `kind: "fact"` recovery message for every affected participant.
- Independent work produces `status: "no-coordination"`, `reason: "independent"`, `operatorAction: null`, and no message only when authoritative evidence explicitly establishes independence. Blocker evidence with distinct complete `externalConditionKey` values and no other relationship evidence establishes that the blockers are independent.
- A signal gap produces `status: "signal-gap"`, `reason: "insufficient-evidence"`, `operatorAction: null`, and no message.

5. Invoke `/message-agents` once for each planned message, passing its complete `recipientPath`, `toPane`, and semantic fields unchanged. NEVER call Prowl directly from this skill.
6. Preserve each delivery result separately from the coordination verdict. A delivery counts only when `/message-agents` reports a checked submitted turn; prefilled text or transport without trailing-Enter evidence remains a delivery failure. Each operating workflow re-evaluates its own state after receiving facts.

</workflow>

<constraints>

- NEVER prescribe workflow-specific retries, reconstruct another workflow's successful state, or choose its checkpoint or continuation.
- NEVER establish ownership from a sent proposal; only a matching accepted acknowledgement establishes the boundary.
- NEVER combine blockers whose authoritative external-condition keys differ.
- NEVER authorize a delegated mutation before exact target/state verification, or authorize editing, staging, stashing, checkout, reset, or commit in a sibling worktree.
- NEVER send directly; delivery belongs to `/message-agents`.
- NEVER wait on another workflow by polling its pane, re-reading it on a timer, or treating one empty read as evidence it produced nothing. A read establishes that pane's state at the instant it ran, never that a request is unanswered.
- NEVER leave the operator to carry a result between two workflows. When a request needs an answer, the request itself carries the return path.

</constraints>

<failure_modes>

**A production request went out with no way to answer it.** Claude classified a dependency handoff correctly and sent the checked need, but omitted `returnPane=` and `handbackCommand=`. The recipient produced the result and had no address to send it to. Claude could not poll — polling loops are blocked by design — so it read the recipient's pane once, saw nothing, and moved on while the finished result sat on disk; the operator carried the answer between the two workflows by hand. A production request without both facts is unanswerable by construction.

**One empty pane read was treated as a negative result.** Claude read a recipient's pane, saw nothing relevant, and concluded the workflow had produced nothing. The read established that pane's state at the instant it ran and nothing more. Absence of a handback is an open request; only a returned message closes it.

**A resolved operator target silently changed the participant set.** Claude resolved an operator-named worktree to a complete identity and then returned only that identity, dropping an input participant the classified relationship did not involve. Every input participant is preserved and the resolved target is added; resolution never replaces the array it augments.

</failure_modes>

<success_criteria>

- The structured verdict names whether coordination is needed, its authoritative reason, complete participants, and protocol-valid messages whose delivery result proves submission rather than editor prefill.
- Shared blockers yield one human-owned action and facts for every affected workflow without centralizing execution.
- Delegated mutations carry an exact target envelope, require an exact pre-mutation state report, and produce no authorization on any identity mismatch.
- Independent work and signal gaps produce no message.

</success_criteria>

The authoritative coordination evidence (JSON-encoded):

```json
{input_json}
```
