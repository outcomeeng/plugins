# Definition invocation

The protocol lives at `probes/definition-invocation/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

The seven definitions `change-executor`, `change-author`, `change-verifier`, `change-tester`, `change-implementer`, `change-skill-author` and `change-subagent-author` are launched by exact name, with no human watching the launch. Reading a definition does not show that Claude Code loads it, starts it as a child of one launch by its exact name, and returns a result its fronted skill or its own workflow declares. This probe shows each exact emitted Claude Code definition doing so in one minimal isolated invocation. For `change-skill-author` and `change-subagent-author` the retained run exercises the `blocked` result for an uninstalled fronted skill, because the probe installs no `instructions` plugin.

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
  This record covers the four round definitions. The run's `change-executor` result is superseded by the run below and is not retained.

- Observations:
  - Each of the four round definitions carries its native `disallowedTools`: `Agent` and `AskUserQuestion`.
  - Each parent session listed its definition, loaded spec-tree from `dist/claude/spec-tree`, and made exactly one `Agent` launch with `subagent_type` `spec-tree:<name>` and prompt `not-a-target`.
  - Each child's first event carries the launch's `parent_tool_use_id` and the `subagent_type` of its definition, and each launch's tool result reports `status` `completed`, the `agentType` of its definition, and `resolvedModel` `claude-opus-5-5`, which the Standard profile's `model: opus` selects.
  - `change-author` returned `blocked` with its question and blocked action. `change-verifier` relayed the missing-target stop of `spec-tree:verify`. `change-tester` stopped at Step 1 of `spec-tree:test` with its missing-target result. `change-implementer` returned `blocked` with reason `target-required` from step 1 of `spec-tree:implement-change`.
  - No child wrote a file or ran a store command.
- Artifacts:
  - [change-author.result.json](change-author.result.json)
  - [change-verifier.result.json](change-verifier.result.json)
  - [change-tester.result.json](change-tester.result.json)
  - [change-implementer.result.json](change-implementer.result.json)

## Attested run: change-executor on the Executor profile

This run records `change-executor`, whose emitted definition selects the Executor profile.

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

## Attested run: the instruction round definitions

This run records `change-skill-author` and `change-subagent-author`, the two definitions that front skills of the `instructions` plugin. The protocol ran unchanged, from an empty scratch directory with `dist/claude/spec-tree` as the only spec-tree plugin and the protocol's `--max-budget-usd 2.00` ceiling.

- Date: 2026-10-03
- Subject commits: `6cbb66684b7e53b3314237b60681e50016757ac9` for `change-skill-author`, and `0942beb61734927d2f07fc7b81c66209e27f876b` for `change-subagent-author`, whose first run on `6cbb66684b7e53b3314237b60681e50016757ac9` is superseded by the run on its next definition and is not retained.
- Observations:
  - Each emitted definition carries `disallowedTools: "AskUserQuestion"`, `model: "opus"` and `effort: "medium"`.
  - Each parent session listed its definition, loaded spec-tree from `dist/claude/spec-tree`, and made exactly one `Agent` launch with `subagent_type` `spec-tree:<name>` and prompt `not-a-target`.
  - Each child's first event carries the launch's `parent_tool_use_id` and the `subagent_type` of its definition, and each launch's tool result reports `status` `completed`, the `agentType` of its definition, and `resolvedModel` `claude-opus-5-5`, which the Standard profile's `model: opus` selects.
  - Each child invoked its fronted skill, `instructions:create-skill` and `instructions:create-subagent` respectively, with the task message. The probe installs no `instructions` plugin, so the Skill tool returned `Unknown skill`, and each child returned a `blocked` result naming the required skill and the exact failure.
  - No child wrote a file or ran a store command. The runs cost USD 0.22 and USD 0.16 against the USD 2.00 ceiling.
- Artifacts:
  - [change-skill-author.result.json](change-skill-author.result.json)
  - [change-subagent-author.result.json](change-subagent-author.result.json)

## Codex protocol

The Codex steps distinguish four observations per definition: discovery by name, loaded configuration, child invocation, and returned result.

Preconditions:

- `dist/codex/spec-tree` is built from the subject commit, and the working tree is clean.
- `CODEX_HOME` is a disposable directory holding an empty `config.toml` and a copy of the saved login. The marketplace catalog of the checkout is registered with `codex plugin marketplace add <checkout>`, `spec-tree@outcomeeng` is installed with `codex plugin add`, and the seven emitted `spec-tree_change-*.toml` definitions are placed byte-identical in `$CODEX_HOME/agents/`, as persistent installation places them.
- `codex exec` runs from an empty scratch directory outside every repository, with `--skip-git-repo-check -s read-only --json`. The task message is the literal `not-a-target`.

Steps:

1. Discovery. In a fresh `codex exec` session, with no tool call, ask for every `agent_type` name beginning `spec-tree_change-` that the subagent-launch tool accepts. Keep the stream as `codex/discovery.jsonl`.
2. For each definition `<name>`, run a fresh `codex exec` session with the prompt: "Call the subagent-launch tool exactly once with agent_type spec-tree_<name>, fork_turns none, and the message: not-a-target. Do nothing else. Then reply with that subagent's final result verbatim." Keep the stream as `codex/spec-tree_<name>.stream.jsonl`.
3. From the session rollouts under `$CODEX_HOME/sessions`, keep the parent's one `spawn_agent` call with its `agent_type` and `fork_turns`, and the child's session metadata (`parent_thread_id`, `agent_role`, depth), `turn_context` (model and effort), the presence of the definition's instruction text in the child's developer context, and the child's tool calls. Keep these with the emitted definition's path and SHA-256 and the parent's final message as `codex/spec-tree_<name>.result.json`, produced by [assemble.py](codex/assemble.py).

## Attested run: the Codex definitions

- Date: 2026-10-11
- Subject commit: `7cc2690b157119862716b4f61c6637907ffb3f21`
- Environment: `codex-cli` 0.162.1 with a ChatGPT saved login, model `gpt-6.1-sol`
- Observations:
  - Discovery: the fresh session listed all seven `spec-tree_change-*` names among the names its launch tool accepts, beside the plugin's own `spec-tree_change-auditor`.
  - Loaded configuration: each child session's metadata carries `agent_role` `spec-tree_<name>`, and its `turn_context` reports model `gpt-6.1-sol` and effort `high`, as the emitted definition declares. Each child's developer context holds the definition's `developer_instructions`.
  - Emitted definitions: the seven definitions at the subject commit declare no tool denial for Codex; each carries `model` `gpt-6.1-sol`, `model_reasoning_effort` `high`, and a `manual_review_guidance` section about its fronted skill. Each result file records the definition's path and SHA-256.
  - Child invocation: each parent made exactly one `spawn_agent` call with `agent_type` `spec-tree_<name>` and `fork_turns` `none`. Each child's `parent_thread_id` is its parent's thread, at depth 1, and no child launched a further agent.
  - Returned result: `change-executor` returned `not-held` from `spec-tree:execute-change`. `change-author` returned `blocked` with its question and blocked action. `change-implementer` returned `blocked` with reason `target-required`. `change-tester` and `change-verifier` returned `blocked` for the non-canonical target. `change-skill-author` returned `blocked` naming `instructions:create-skill` as absent, and `change-subagent-author` returned `blocked` naming `instructions:create-subagent` as absent.
  - Each child loaded its fronted skill by reading its `SKILL.md` from the disposable home's plugin cache. The sandbox was read-only, and no child wrote a file.
- Artifacts:
  - [discovery.jsonl](codex/discovery.jsonl)
  - [spec-tree_change-executor.result.json](codex/spec-tree_change-executor.result.json) and [stream](codex/spec-tree_change-executor.stream.jsonl)
  - [spec-tree_change-author.result.json](codex/spec-tree_change-author.result.json) and [stream](codex/spec-tree_change-author.stream.jsonl)
  - [spec-tree_change-implementer.result.json](codex/spec-tree_change-implementer.result.json) and [stream](codex/spec-tree_change-implementer.stream.jsonl)
  - [spec-tree_change-tester.result.json](codex/spec-tree_change-tester.result.json) and [stream](codex/spec-tree_change-tester.stream.jsonl)
  - [spec-tree_change-verifier.result.json](codex/spec-tree_change-verifier.result.json) and [stream](codex/spec-tree_change-verifier.stream.jsonl)
  - [spec-tree_change-skill-author.result.json](codex/spec-tree_change-skill-author.result.json) and [stream](codex/spec-tree_change-skill-author.stream.jsonl)
  - [spec-tree_change-subagent-author.result.json](codex/spec-tree_change-subagent-author.result.json) and [stream](codex/spec-tree_change-subagent-author.stream.jsonl)

## Verdict

`passed`: each exact emitted Claude Code definition loaded natively, started as a child session of one `Agent` launch, and returned a result its fronted skill or its own workflow declares.

`passed`: each exact emitted Codex definition was discovered by its name in a fresh session, loaded with its declared model and effort, started as the child session of one isolated `spawn_agent` launch by that name, and returned a result its fronted skill or its own workflow declares.

## Limitations

- The run exercises only the stop at an unaccepted target; a round that produces an artifact, and a Fixer's repair block, stay unexercised.
- The emitted effort is recorded from the definition file — `effort: medium` for the six Standard-profile definitions and `effort: high` for `change-executor`; each child's tool result reports the resolved model and no effort value.
- The run of the two instruction round definitions exercises the `blocked` result for an uninstalled fronted skill. A round that runs `instructions:create-skill` or `instructions:create-subagent` whole stays unexercised because the probe installs no `instructions` plugin. Neither fronted skill launches an auditor; the Verifier of such a round is a separate launch by `/execute-change`, outside this protocol.
- The Codex run exercises only the stop at an unaccepted target, like the Claude Code run. The emitted effort and model are recorded from the child's `turn_context`.
- The Codex children can read paths outside the disposable home, because the read-only sandbox restricts writes only. In this run `change-skill-author` and `change-subagent-author` each searched only the scratch tree and returned the uninstalled-skill `blocked` result, but an earlier run of `change-subagent-author` found and read `instructions:create-subagent` in the operator's personal Codex plugin cache. The Codex run therefore does not isolate the installed-plugin set from the host.
- The discovery observation rests on the model reporting the names its launch tool accepts; the launch of each definition by name in step 2 is the stronger evidence.
- The emitted Codex definitions declare no tool denial, so the run observes only that no child launched an agent or wrote a file; each child ran under the read-only sandbox of the protocol, which restricts writes and never restricts agent launches.
- A later change to an emitted definition invalidates its record here until the protocol runs again on the new commit.
