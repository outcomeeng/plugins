# Definition invocation

The protocol lives at `probes/definition-invocation/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

The five definitions `change-executor`, `change-author`, `change-verifier`, `change-tester` and `change-implementer` are launched by exact name, with no human watching the launch. Reading a definition does not show that Claude Code loads it, preloads its skill, and returns that skill's result contract. This probe shows each exact emitted Claude Code definition doing so in one minimal isolated invocation.

## Environment and preconditions

- The generated tree `dist/claude/spec-tree` is built from the subject commit, and the working tree is clean.
- Claude Code runs from an empty scratch directory outside every repository, with no setting source loaded, no session persistence, and `dist/claude/spec-tree` as its only spec-tree plugin.
- The task message is the literal `not-a-target`, which no fronted skill accepts as a target, so each skill stops before it reads or writes a Change, a store, or a repository.

## Protocol

1. From the scratch directory, for each definition `<name>`, pipe this prompt to `claude -p --plugin-dir <checkout>/dist/claude/spec-tree --setting-sources "" --no-session-persistence --output-format stream-json --verbose --max-budget-usd 2.00 --allowedTools Agent`: "Use the Agent tool exactly once to launch the subagent spec-tree:<name> with the prompt: not-a-target. Do nothing else. Then reply with that subagent's final result verbatim."
2. From the stream, keep the parent's init event (model, the spec-tree plugin path, and whether the definition is listed), the one `Agent` launch, the child's first event with its `parent_tool_use_id` and `subagent_type`, and the launch's tool result.
3. Record the emitted definition's path, front matter, and SHA-256 at the subject commit beside each run.

## Attested run

- Date: 2026-09-30
- Subject commit: `d090bb966859c3b4770a78a4ba2de5410d4fc53f`
- Observations:
  - Each emitted definition carries its native `disallowedTools`: `Agent` and `AskUserQuestion` for the four round definitions, `AskUserQuestion` for `change-executor`.
  - Each parent session listed its definition, loaded spec-tree from `dist/claude/spec-tree`, and made exactly one `Agent` launch with `subagent_type` `spec-tree:<name>` and prompt `not-a-target`.
  - Each child's first event carries the launch's `parent_tool_use_id` and the `subagent_type` of its definition, and each launch's tool result reports `status` `completed`, the `agentType` of its definition, and `resolvedModel` `claude-opus-5-5`, which the Standard profile's `model: opus` selects.
  - `change-executor` returned `not-held` from `spec-tree:execute-change` step 1. `change-author` returned `blocked` with its question and blocked action. `change-verifier` relayed the missing-target stop of `spec-tree:verify`. `change-tester` stopped at Step 1 of `spec-tree:test` with its missing-target result. `change-implementer` returned `blocked` with reason `target-required` from step 1 of `spec-tree:implement-change`.
  - No child wrote a file or ran a store command.
- Artifacts:
  - [change-executor.result.json](change-executor.result.json)
  - [change-author.result.json](change-author.result.json)
  - [change-verifier.result.json](change-verifier.result.json)
  - [change-tester.result.json](change-tester.result.json)
  - [change-implementer.result.json](change-implementer.result.json)

## Attested run: change-executor on the Executor profile

The run above holds for `change-author`, `change-verifier`, `change-tester` and `change-implementer`. This run replaces its `change-executor` result, because the emitted definition now selects the Executor profile.

- Date: 2026-10-03
- Subject commit: `8a5ddbe8d21caa37a7db2d7d304b613c6805b9a8`
- Observations:
  - The emitted definition carries `model: "sonnet"`, `effort: "high"`, and `disallowedTools: "AskUserQuestion"`.
  - The parent session listed `spec-tree:change-executor`, loaded spec-tree from `dist/claude/spec-tree`, and made exactly one `Agent` launch with `subagent_type` `spec-tree:change-executor` and prompt `not-a-target`.
  - The child's first event carries the launch's `parent_tool_use_id` and the `subagent_type` `spec-tree:change-executor`. The launch's tool result reports `status` `completed`, `agentType` `spec-tree:change-executor`, and `resolvedModel` `claude-sonnet-5-5`, which the Executor profile's `model: sonnet` selects.
  - `change-executor` returned `not-held` from `spec-tree:execute-change` step 1. Its one tool call, loading `spec-tree:change-standards`, was refused by the probe's `--allowedTools Agent` grant, and the child reported that refusal without reconstructing the skill.
  - The child wrote no file and ran no store command. The run cost USD 0.19 against the USD 2.00 ceiling.
- Artifacts:
  - [change-executor.result.json](change-executor.result.json)

## Verdict

`passed`: each exact emitted definition loaded natively, started as a child session of one `Agent` launch, and returned a result its fronted skill or its own workflow declares.

## Limitations

- The run exercises only the stop at an unaccepted target; a round that produces an artifact, and a Fixer's repair block, stay unexercised.
- The emitted `effort: medium` is recorded from the definition file; the child's tool result reports the resolved model and no effort value.
- The Codex renderings are not invoked; the node's `ISSUES.md` records that gap.
- A later change to an emitted definition invalidates its record here until the protocol runs again on the new commit.
