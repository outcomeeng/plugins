# Definition invocation

The protocol lives at `probes/definition-invocation/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

The seven definitions `change-executor`, `change-author`, `change-verifier`, `change-tester`, `change-implementer`, `change-skill-author` and `change-subagent-author` are launched by exact name, with no human watching the launch. Reading a definition does not show that Claude Code loads it, starts it as a child of one launch by its exact name, and returns a result its fronted skill or its own workflow declares. This probe shows each exact emitted Claude Code definition doing so in one minimal isolated invocation. For `change-skill-author` and `change-subagent-author` the retained run exercises the `blocked` result for an uninstalled fronted skill, because the probe installs no `instructions` plugin.

## Environment and preconditions

- The generated tree `dist/claude/product-tree` is built from the subject commit, and the working tree is clean.
- Claude Code runs from an empty scratch directory outside every repository, with no setting source loaded, no session persistence, and `dist/claude/product-tree` as its only product-tree plugin.
- The task message is the literal `not-a-target`, which no fronted skill accepts as a target, so each skill stops before it reads or writes a Change, a store, or a repository.

## Protocol

1. From the scratch directory, for each definition `<name>`, pipe this prompt to `claude -p --plugin-dir <checkout>/dist/claude/product-tree --setting-sources "" --no-session-persistence --output-format stream-json --verbose --max-budget-usd 2.00 --allowedTools Agent`: "Use the Agent tool exactly once to launch the subagent product-tree:<name> with the prompt: not-a-target. Do nothing else. Then reply with that subagent's final result verbatim."
2. From the stream, keep the parent's init event (model, the product-tree plugin path, and whether the definition is listed), the one `Agent` launch, the child's first event with its `parent_tool_use_id` and `subagent_type`, and the launch's tool result.
3. Record the emitted definition's path, front matter, and SHA-256 at the subject commit beside each run.

## Attested run

The protocol ran unchanged for all seven definitions, from an empty scratch directory outside every repository, with `dist/claude/product-tree` as the only product-tree plugin (version 0.107.2), Claude Code 2.1.309, and the protocol's `--max-budget-usd 2.00` ceiling. Earlier records for these definitions are superseded and not retained.

- Date: 2026-10-25
- Subject commit: `896d293a3b68dac512690cbad2118e88986d283c` for all seven definitions; the working tree was clean when the run started.
- Observations:
  - Every emitted definition carries `model: "sonnet"`; `change-executor` carries `effort: "high"` and `disallowedTools: "AskUserQuestion"`, and the six others carry `effort: "medium"` and `disallowedTools: Agent, AskUserQuestion`. Each result file records the definition's SHA-256 at the subject commit.
  - Each parent session listed its definition, loaded product-tree from `dist/claude/product-tree`, and made exactly one `Agent` launch with `subagent_type` `product-tree:<name>` and prompt `not-a-target`.
  - Each child's first event carries the launch's `parent_tool_use_id`, and each launch's tool result reports `status` `completed`, the `agentType` of its definition, and `resolvedModel` `claude-sonnet-5-5`, which `model: sonnet` selects.
  - `change-executor` returned `not-held` from step 1 of `product-tree:execute-change` and made no tool call. `change-author` returned `blocked` with its question and blocked action. `change-verifier` returned the `blocked: unsupported-target` row of `product-tree:verify`. `change-implementer` returned `blocked` with reason `target-required` from `product-tree:implement-change`.
  - `change-tester` loaded `product-tree:test`, then its Skill call for `product-tree:test-evidence-standards` returned an execution error because the protocol's `--allowedTools Agent` grant refuses it, and the child returned `blocked` naming that skill and the exact failure.
  - `change-skill-author` and `change-subagent-author` invoked `instructions:author-skill` and `instructions:author-subagent` with the task message. The probe installs no `instructions` plugin, so the Skill tool returned `Unknown skill` for each, and each child returned `blocked` naming the required skill and the exact failure.
  - No child wrote a file or ran a store command. The seven runs cost USD 0.20, 0.18, 0.16, 0.18, 0.15, 0.15 and 0.15 against the USD 2.00 ceiling each.
- Artifacts:
  - [change-executor.result.json](change-executor.result.json)
  - [change-author.result.json](change-author.result.json)
  - [change-verifier.result.json](change-verifier.result.json)
  - [change-tester.result.json](change-tester.result.json)
  - [change-implementer.result.json](change-implementer.result.json)
  - [change-skill-author.result.json](change-skill-author.result.json)
  - [change-subagent-author.result.json](change-subagent-author.result.json)

## Verdict

`passed`: each exact emitted definition loaded natively, started as a child session of one `Agent` launch, and returned a result its fronted skill or its own workflow declares.

## Limitations

- The run exercises only the stop at an unaccepted target; a round that produces an artifact, and a Fixer's repair block, stay unexercised.
- The emitted effort is recorded from the definition file, `effort: medium` for six definitions and `effort: high` for `change-executor`; each child's tool result reports the resolved model and no effort value.
- The run of `change-tester` stops at a skill load the protocol's tool grant refuses, so `product-tree:test` past its prerequisite load stays unexercised.
- The run of the two instruction round definitions exercises the `blocked` result for an uninstalled fronted skill. A round that runs `instructions:author-skill` or `instructions:author-subagent` whole stays unexercised because the probe installs no `instructions` plugin. Neither fronted skill launches an auditor; the Verifier of such a round is a separate launch by `/apply-change`, outside this protocol.
- The Codex renderings are not invoked; the node's `ISSUES.md` records that gap.
- A later change to an emitted definition invalidates its record here until the protocol runs again on the new commit.
