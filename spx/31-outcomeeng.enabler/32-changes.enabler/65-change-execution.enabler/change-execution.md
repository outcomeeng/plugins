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
- ALWAYS: an Executor whose record and newest Handoff name no working branch works on the branch its assigned worktree has checked out, unless that branch is the default branch; on a detached or default-branch checkout it creates the work branch `work/change-<N>` from the Change's number and starts there, and a branch the record or the newest Handoff names stays the working branch ([audit])
- ALWAYS: for every round, `/execute-change` launches one subagent session of the definition that fronts the producing skill the Mutation row needs — `change-author` for `/author`, `change-verifier` for `/verify`, `change-tester` for `/test`, `change-implementer` for `/implement-change`, `change-skill-author` for `instructions:create-skill`, `change-subagent-author` for `instructions:create-subagent` — and launches each Fixer as a fresh session of the same definition, handed the earlier round's artifacts and verdicts ([audit])
- ALWAYS: a Mutation row whose Node's result is a skill surface — a `SKILL.md`, another file in a skill directory, or an authored shared fragment — runs as a `change-skill-author` round with `instructions:skill-auditor` as its Verifier, and a row whose result is a subagent definition runs as a `change-subagent-author` round with `instructions:subagent-auditor` as its Verifier; the Executor launches that Verifier after the round returns, as the row's results name it, and the round launches none ([audit])
- ALWAYS: `/execute-change` takes the `## Mutations` rows in record order, and after each round records the audited content the round produced as an `## Artifacts` link through `author-change` ([audit])
- NEVER: a round session launches a Verifier; the Executor launches every Verifier that the results of the `## Mutations` rows name ([audit])
- ALWAYS: a plugin changelog entry is produced in the round that produces the skill or subagent surface it records ([audit])
- ALWAYS: a round whose fronted skill is not installed returns a `blocked` result naming that skill ([audit])
- ALWAYS: `/implement-change` finds the installed `architect-{lang}`, `code-{lang}` and `simplify-{lang}` skills and runs the target language's skills in its one session — `architect-{lang}` for a language decision, `code-{lang}` for implementation, then `simplify-{lang}` where the language ships one — and launches no subagent ([audit])
- ALWAYS: `/execute-change` launches its Verifiers from the configured auditor and reviewer definitions, each named exactly and each with a target-only prompt ([audit])
- NEVER: the Executor produces an artifact of a round; it takes the `## Mutations` rows in order, integrates the changeset through `/merge`, and closes the Change through `/close-change` or releases it with a Handoff through `/release-change` ([audit])
- ALWAYS: an Executor launches each gate at most twice per Change, counting every rejection from any session, including those of a Fixer round and of the reviewers and auditors `/merge` launches; after the second rejection it releases the Change with both rejections named by gate and run token in the Hazards line of the Handoff, and a third launch of that gate on that Change is refused with the count ([audit])
- NEVER: an Executor repeats a gate until it approves ([audit])
- ALWAYS: a rejection counts when a blocking or debt finding sits on a line the changeset changed or is caused by its edit, and a complete `BLOCKED` diagnostic from an audit gate counts as a rejection with no finding to read; a filed finding, a stale finding and a finding on untouched text count for nothing, a launch that seals no run counts for nothing, and a published revision of the record's body restarts the count ([audit])
- ALWAYS: the cap covers agentic gates only; a deterministic command that fails runs again after its Fixer round outside the cap, and one that fails again after that round releases the Change ([audit])
- ALWAYS: `change-executor`, `change-author`, `change-verifier`, `change-tester`, `change-implementer`, `change-skill-author` and `change-subagent-author` each front exactly one skill, hold no logic, and inherit the invoking session's execution policy ([audit])
- ALWAYS: each of the seven definitions, as the Claude Code build emits it, loads natively, starts as the child session of one launch by its exact name, and returns a result its fronted skill or its own workflow declares ([probe](probes/definition-invocation/probe.md))
- ALWAYS: a load-gated command `/implement-change` runs executes in the foreground, and the skill reports its result only after every such command has exited ([audit])
- ALWAYS: `/execute-change` reads the verdict of each `skill-auditor` and `subagent-auditor` launch from the sealed run whose token the launch returns: a `rejected` terminal status rejects whatever the finding count, and a refused payload or finish is a blocked result ([audit])
- ALWAYS: `/execute-change` launches `assertion-auditor` as the Verifier for an evidence obligation on a node's `[audit]` assertions, and reads its verdict from the sealed run whose token the launch returns ([audit])
