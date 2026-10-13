---
id: 01a0f110-cfe6-70b6-8a53-a0dfe7503567
malleability: spec
---

# Change Execution

PROVIDES the execution of one Executable Change by its Executor — confirming the claim, running each round's producing skills and Verifiers in agent sessions of their own, integrating the changeset, and closing or releasing the Change
SO THAT an Executor session started for a Change
CAN deliver the Change's Output while producing no artifact itself

The spec-tree plugin ships one subagent definition per skill an Executor session or its rounds run: `change-executor` fronts `/execute-change`, `change-author` fronts `/author`, `change-verifier` fronts `/verify`, `change-tester` fronts `/test`, `change-implementer` fronts `/implement-change`, `change-skill-author` fronts `instructions:create-skill`, and `change-subagent-author` fronts `instructions:create-subagent`. Each Fixer is a fresh session of the definition its round's Author used, per [`spx/15-agent-terminology.pdr.md`](spx/15-agent-terminology.pdr.md).

## Assertions

- ALWAYS: the seven definitions ship for Claude Code only, and `/execute-change` on Codex returns an explicit unavailable result ([audit])

### Compliance

- ALWAYS: `/execute-change` confirms that the winning Claim names its worktree root and loads the latest Handoff before it starts, and executes only an Executable Leaf whose every predecessor is closed and whose blockers are resolved, and refuses a Parent ([audit])
- ALWAYS: an Executor whose record and newest Handoff name no working branch works on the branch its assigned worktree has checked out only when that branch is not the default branch and its name ends with the Change number with no digit before it, as `work/change-<N>` and `executor-<N>` do and `work/change-1<N>` does not; otherwise the worktree counts as naming no branch, and the Executor creates the work branch `work/change-<N>` from the Change's number and starts there; a branch the record or the newest Handoff names stays the working branch ([audit])
- ALWAYS: execution launches, for every round, one agent session of the kind that produces the block's result — decisions and specs, verification evidence, tests, implementation, a skill surface, or a subagent definition — and launches each Fixer as a fresh session of the same kind, handed the earlier round's artifacts and verdicts ([audit])
- ALWAYS: a block whose Node's result is a skill surface — a skill's instructions, another file in a skill directory, or an authored shared fragment — runs as a round of the skill-surface producing kind, and a block whose result is a subagent definition runs as a round of the subagent-definition producing kind; after the round returns, the Executor launches only the Verifiers the merge composition selects for the block, and the round launches none ([audit])
- NEVER: `/execute-change` pairs `instructions:skill-auditor`, `instructions:subagent-auditor`, or `spec-tree:spec-auditor` with a round, because the merge composition selects none of them for a Node at any malleability ([audit])
- ALWAYS: execution takes the Governance mutations blocks and then the Spec mutations blocks in record order, derives each block's results and Verifiers from the merge composition for the Node's malleability after and the tags of its assertions, and records its progress only in its Handoff; neither the Executor nor a round session writes the Change record ([audit])
- NEVER: a round session launches a Verifier; the Executor launches every Verifier that the merge composition selects for the blocks ([audit])
- ALWAYS: a plugin changelog entry is produced in the round that produces the skill or subagent surface it records ([audit])
- ALWAYS: a round whose fronted skill is not installed returns a `blocked` result naming that skill ([audit])
- ALWAYS: `/implement-change` finds the installed `architect-{lang}`, `code-{lang}` and `simplify-{lang}` skills and runs the target language's skills in its one session — `architect-{lang}` for a language decision, `code-{lang}` for implementation, then `simplify-{lang}` where the language ships one — and launches no subagent ([audit])
- ALWAYS: `/execute-change` launches its Verifiers from the configured auditor and reviewer definitions, each named exactly and each with a target-only prompt ([audit])
- NEVER: the Executor produces an artifact of a round; it takes the Governance mutations blocks and then the Spec mutations blocks in order, integrates the changeset, and closes the Change or releases it with a Handoff ([audit])
- ALWAYS: an Executor launches each gate at most twice per Change, counting every rejection from any session, including those of a Fixer round and of the reviewers and auditors `/merge` launches; after the second rejection it releases the Change with both rejections named by gate and run token in the Hazards line of the Handoff, and a third launch of that gate on that Change is refused with the count ([audit])
- NEVER: an Executor repeats a gate until it approves ([audit])
- ALWAYS: a rejection counts when a blocking or debt finding sits on a line the changeset changed or is caused by its edit, and a complete `BLOCKED` diagnostic from an audit gate counts as a rejection with no finding to read; a filed finding, a stale finding and a finding on untouched text count for nothing, a launch that seals no run counts for nothing, and a published revision of the record's body restarts the count ([audit])
- ALWAYS: the cap covers agentic gates only; a deterministic command that fails runs again after its Fixer round outside the cap, and one that fails again after that round releases the Change ([audit])
- ALWAYS: `change-executor`, `change-author`, `change-verifier`, `change-tester`, `change-implementer`, `change-skill-author` and `change-subagent-author` each front exactly one skill, hold no logic, and inherit the invoking session's execution policy ([audit])
- ALWAYS: each of the seven definitions, as the Claude Code build emits it, loads natively, starts as the child session of one launch by its exact name, and returns a result its fronted skill or its own workflow declares ([probe](probes/definition-invocation/probe.md))
- ALWAYS: a load-gated command `/implement-change` runs executes in the foreground, and the skill reports its result only after every such command has exited ([audit])
- ALWAYS: `/execute-change` launches `assertion-auditor` as the Verifier for an evidence obligation on a node's `[audit]` assertions, and reads its verdict from the sealed run whose token the launch returns: a `rejected` terminal status rejects whatever the finding count, and a refused payload or finish is a blocked result ([audit])
