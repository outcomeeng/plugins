# Inter-Worktree Coordination

PROVIDES coordination decisions and message plans for coding agents operating in separate worktrees
SO THAT independently owned workflows
CAN resolve ownership overlap, dependency handoffs, and shared external blockers without centralizing workflow execution

## Assertions

### Mappings

- Overlapping paths or concerns map to an ownership proposal whose boundary becomes agreed only after a matching accepted acknowledgement ([eval](evals/coordination-decision/eval.toml))
- Independent work with no overlap, dependency, shared mutation, or correlated blocker maps to no coordination message ([eval](evals/coordination-decision/eval.toml))

### Compliance

- ALWAYS: coordination emits a structured decision naming whether coordination is needed, the authoritative reason, complete participants, and zero or more protocol-valid messages ([eval](evals/coordination-decision/eval.toml))
- ALWAYS: a delegated mutation carries an exact pane, worktree, branch, and repository target; mutation authorization follows only after a matching accepted ownership acknowledgement and an exact worktree, branch, repository, full-HEAD, and status report matches that target ([eval](evals/coordination-decision/eval.toml))
- ALWAYS: shared blockers correlate only from the same authoritative external-condition key and produce one operator action plus recovery facts for every affected workflow ([eval](evals/coordination-decision/eval.toml))
- NEVER: coordination prescribes workflow-specific retries, reconstructs another workflow's successful state, or substitutes prose inference for missing evidence ([eval](evals/coordination-decision/eval.toml))
- NEVER: coordination authorizes mutation in a sibling worktree or transfer of another workflow's commit without an accepted ownership proposal ([eval](evals/coordination-decision/eval.toml))
- ALWAYS: a dependency handoff that asks another workflow to produce something carries the source-generated structured handback block for the authoritative requester and resolves to a signal gap when the requester is not an authoritative participant or the environment capability has not produced that block ([eval](evals/coordination-decision/eval.toml))
- ALWAYS: a participant named by worktree, repository, or working directory resolves to a complete identity that joins the participant array, and every input participant is preserved including one the classified relationship does not involve ([eval](evals/coordination-decision/eval.toml))
- NEVER: coordination waits on another workflow by polling its pane or leaves the operator to carry a result between two workflows ([audit])
- NEVER: a message is sent directly by coordination; delivery routes through `/message-agents` ([audit])
