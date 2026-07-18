<!-- Generated from the complete producer at src/plugins/coding-agents/skills/coordinate-agents/SKILL.md. -->

Apply the complete coordination producer below to the supplied authoritative evidence. Return only the producer's structured JSON verdict. Do not invoke tools or send messages during this evaluation.

---
name: coordinate-agents
description: >-
  ALWAYS invoke this skill when coding agents in separate worktrees may overlap, depend on each other, share an external blocker, or need ownership coordination.
allowed-tools: Read, Skill
---

<objective>
A structured coordination decision that preserves independent workflow ownership and routes every planned delivery through `/message-agents`.
</objective>

<evidence_model>

Use only explicit SPX facts, public runtime projections, checked command results, and operator-confirmed external changes as authoritative evidence. Treat prose inference as advisory. A missing authoritative fact is a signal gap, never permission to scan harness transcripts.

</evidence_model>

<workflow>

1. Identify every participant with complete agent, pane, worktree, branch, repository, and applicable run identities.
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

Each message carries a complete `toPane` UUID, `kind`, `subject`, a `facts` array of strings, `request`, `coordinationReference`, `mutationTarget`, and `observedState`. `kind` MUST be exactly `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. Use `fact` for dependency and recovery facts. Use `request: null` when no recipient action is requested. Omit or set `coordinationReference` to null for initiating proposals and facts so `/message-agents` creates a UUID; every response kind preserves the active proposal UUID.
4. Apply the protocol:

- Ownership overlap produces an `ownership-proposal`; its boundary remains proposed until a matching accepted acknowledgement arrives.
- A dependency handoff sends `kind: "fact"` with checked facts and `request: null`, not another workflow's continuation instructions.
- A delegated mutation begins with an `ownership-proposal` whose `mutationTarget` contains the recipient's exact pane UUID, worktree path, branch, repository, full HEAD SHA, and status. The recipient performs no mutation until it reports `kind: "mutation-state"` with the same coordination reference and an `observedState` containing its exact worktree, branch, repository, full HEAD SHA, and status. Emit `mutation-authorization` only when every reported value matches the target exactly; echo the checked target and observed state in that authorization.
- When delegated-mutation evidence has no `reportedState`, emit one ownership proposal carrying the exact target and request the state report.
- When any reported worktree, branch, repository, HEAD, or status value differs from the target, emit `status: "coordination-needed"`, `reason: "ownership-overlap"`, and no message. A mismatch produces no authorization.
- When every reported value matches, emit one `mutation-authorization` to the target pane with the active coordination reference, exact target, and observed state. When `neededSource.transferAcknowledged` is false, set `request` exactly to `Recreate the required change in the target worktree; do not mutate or transfer from the sibling worktree.`
- Every sibling worktree stays read-only to both workflows. Transfer an exact commit only after the source owner separately proposes and acknowledges that transfer.
- A shared blocker produces exactly one non-null `operatorAction` carrying its complete `externalConditionKey`. When restoration is operator-confirmed, keep that action record and produce one `kind: "fact"` recovery message for every affected participant.
- Independent work produces `status: "no-coordination"`, `reason: "independent"`, `operatorAction: null`, and no message only when authoritative evidence explicitly establishes independence. Blocker evidence with distinct complete `externalConditionKey` values and no other relationship evidence establishes that the blockers are independent.
- A signal gap produces `status: "signal-gap"`, `reason: "insufficient-evidence"`, `operatorAction: null`, and no message.

5. Invoke `/message-agents` once for each planned message. NEVER call Prowl directly from this skill.
6. Preserve each delivery result separately from the coordination verdict. Each operating workflow re-evaluates its own state after receiving facts.

</workflow>

<constraints>

- NEVER prescribe workflow-specific retries, reconstruct another workflow's successful state, or choose its checkpoint or continuation.
- NEVER establish ownership from a sent proposal; only a matching accepted acknowledgement establishes the boundary.
- NEVER combine blockers whose authoritative external-condition keys differ.
- NEVER authorize a delegated mutation before exact target/state verification, or authorize editing, staging, stashing, checkout, reset, or commit in a sibling worktree.
- NEVER send directly; delivery belongs to `/message-agents`.

</constraints>

<success_criteria>

- The structured verdict names whether coordination is needed, its authoritative reason, complete participants, and protocol-valid messages.
- Shared blockers yield one human-owned action and facts for every affected workflow without centralizing execution.
- Delegated mutations carry an exact target envelope, require an exact pre-mutation state report, and produce no authorization on any identity mismatch.
- Independent work and signal gaps produce no message.

</success_criteria>

The authoritative coordination evidence (JSON-encoded):

```json
{input_json}
```
