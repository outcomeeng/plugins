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

- ALWAYS: the seven definitions ship for Claude Code only, and `/execute-change` on Codex returns an explicit unavailable result

### Compliance

- ALWAYS: `/execute-change` confirms that the winning Claim names its worktree root and loads the latest Handoff before it starts, and executes only an Executable lineage leaf with Refined predecessors and no unresolved blocker ([audit])
- ALWAYS: for every round, `/execute-change` launches one subagent session of the definition that fronts the producing skill the Activity needs — `change-author` for `/author`, `change-verifier` for `/verify`, `change-tester` for `/test`, `change-implementer` for `/implement-change`, `change-skill-author` for `instructions:create-skill`, `change-subagent-author` for `instructions:create-subagent` — and launches each Fixer as a fresh session of the same definition, handed the earlier round's artifacts and verdicts ([audit])
- ALWAYS: an Activity whose result is a skill surface — a `SKILL.md`, another file in a skill directory, or an authored shared fragment — runs as a `change-skill-author` round with `instructions:skill-auditor` as its Verifier, and an Activity whose result is a subagent definition runs as a `change-subagent-author` round with `instructions:subagent-auditor` as its Verifier ([audit])
- ALWAYS: a plugin changelog entry is produced in the round that produces the skill or subagent surface it records ([audit])
- ALWAYS: a round whose fronted skill is not installed returns a `blocked` result naming that skill ([audit])
- ALWAYS: `/implement-change` finds the installed `architect-{lang}`, `code-{lang}` and `simplify-{lang}` skills and runs the target language's skills in its one session — `architect-{lang}` for a language decision, `code-{lang}` for implementation, then `simplify-{lang}` where the language ships one — and launches no subagent ([audit])
- ALWAYS: `/execute-change` launches its Verifiers from the configured auditor and reviewer definitions, each named exactly and each with a target-only prompt ([audit])
- ALWAYS: `/execute-change` reads the verdict of each `adr-auditor`, `pdr-auditor`, `spec-auditor`, `test-evidence-auditor`, `eval-evidence-auditor` and `changeset-coherence-auditor` launch from the sealed run whose token the launch returns: a `rejected` run rejects whatever its finding count, a launch whose run spx refused a payload or the finish of is blocked, and a verdict read from legacy verdict JSON, a transcript, a task-output file, or text parsed into a scratch file is an unusable result ([audit])
- NEVER: the Executor produces an artifact of a round; it sequences Activities, integrates the changeset through `/merge`, and closes the Change through `/close-change` or releases it with a Handoff through `/release-change` ([audit])
- ALWAYS: `change-executor`, `change-author`, `change-verifier`, `change-tester`, `change-implementer`, `change-skill-author` and `change-subagent-author` each front exactly one skill, hold no logic, and inherit the invoking session's execution policy ([audit])
- ALWAYS: each of the seven definitions, as the Claude Code build emits it, loads natively, starts as the child session of one launch by its exact name, and returns a result its fronted skill or its own workflow declares ([probe](probes/definition-invocation/probe.md))
- ALWAYS: a load-gated command `/implement-change` runs executes in the foreground, and the skill reports its result only after every such command has exited ([audit])
- ALWAYS: `/execute-change` reads the verdict of each `skill-auditor` and `subagent-auditor` launch from the sealed run whose token the launch returns: a `rejected` terminal status rejects whatever the finding count, and a refused payload or finish is a blocked result ([audit])
