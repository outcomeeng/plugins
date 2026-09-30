---
id: 01a0f110-cfe6-70b6-8a53-a0dfe7503567
malleability: spec
---

# Change Execution

PROVIDES the execution of one Executable Change by its Executor — confirming the claim, running each round's producing skills and Verifiers in agent sessions of their own, integrating the changeset, and closing or releasing the Change
SO THAT an Executor session started for a Change
CAN deliver the Change's Output while producing no artifact itself

The spec-tree plugin ships one subagent definition per skill an Executor session or its rounds run: `change-executor` fronts `/execute-change`, `change-author` fronts `/author`, `change-verifier` fronts `/verify`, `change-tester` fronts `/test`, and `change-implementer` fronts `/implement-change`. Each Fixer is a fresh session of the definition its round's Author used, per `spx/15-agent-terminology.pdr.md`.

## Assertions

- ALWAYS: `/execute-change` confirms that the winning Claim names its worktree root and loads the latest Handoff before it starts, and executes only an Executable lineage leaf with Refined predecessors and no unresolved blocker ([audit])
- ALWAYS: for every round, `/execute-change` launches one subagent session of the definition that fronts the producing skill the Activity needs — `change-author` for `/author`, `change-verifier` for `/verify`, `change-tester` for `/test`, `change-implementer` for `/implement-change` — and launches each Fixer as a fresh session of the same definition, handed the earlier round's artifacts and verdicts ([audit])
- ALWAYS: `/implement-change` finds the installed `architect-{lang}`, `code-{lang}` and `simplify-{lang}` skills and runs the target language's skills in its one session — `architect-{lang}` for a language decision, `code-{lang}` for implementation, then `simplify-{lang}` where the language ships one — and launches no subagent ([audit])
- ALWAYS: `/execute-change` launches its Verifiers from the configured auditor and reviewer definitions, each named exactly and each with a target-only prompt ([audit])
- NEVER: the Executor produces an artifact of a round; it sequences Activities, integrates the changeset through `/merge`, and closes the Change through `/close-change` or releases it with a Handoff through `/release-change` ([audit])
- ALWAYS: `change-executor`, `change-author`, `change-verifier`, `change-tester` and `change-implementer` each front exactly one skill, hold no logic, and inherit the invoking session's execution policy ([audit])
- ALWAYS: a load-gated command `/implement-change` runs executes in the foreground, and the skill reports its result only after every such command has exited ([audit])
