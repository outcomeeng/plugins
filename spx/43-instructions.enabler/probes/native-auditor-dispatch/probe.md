# Native auditor dispatch

The protocol lives at `probes/native-auditor-dispatch/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

`skill-auditor` and `subagent-auditor` are launched natively by exact name on Claude Code and on Codex, with no human watching the launch. Reading the definitions and the audit skills does not show that a native launch starts one verification run, records every scope unit and finding through it, seals it, and returns a result that names the run token, the run file, and the rendered projection. A harness that names no scratch directory, as a local Codex session does, leaves the payload location to the audit skill, and only an executed dispatch shows that the skill's payload directory, the file-write tool, and the run-recording commands complete a run there. This probe shows each auditor, on each harness, returning a sealed run from one minimal isolated dispatch.

## Environment and preconditions

- The generated trees `dist/claude/instructions` and `dist/codex/instructions` are built from the subject commit, and the working tree is clean.
- The Claude Code dispatch runs from an empty scratch directory outside every repository, with no setting source loaded, no session persistence, and `dist/claude/instructions` as its only instructions plugin.
- The Codex dispatch runs from an empty scratch directory outside every repository, under a disposable `$CODEX_HOME` that holds the `instructions` plugin installed from the generated Codex tree and its generated agent definitions, with the invoking session's default execution policy and no scratch directory named by the harness.
- The `spx` command-line tool at the version the repository requires is on `PATH` in both sessions.
- Each session holds the maintainer's own credentials for its harness.
- The scratch directory holds two audit targets: a minimal conforming skill file and a minimal conforming subagent definition, each written beside the run and never inside a repository.

## Protocol

1. For each harness (Claude Code, Codex), record the harness version, the installed `instructions` plugin version and path, and the subject commit.
2. Launch the harness non-interactively from its scratch directory with the prompt: "Use the native subagent dispatch exactly once to launch `instructions:skill-auditor` with the path of the skill file in this directory as the task message. Do nothing else. Then reply with that subagent's final result verbatim."
3. Repeat step 2 for `instructions:subagent-auditor` with the path of the subagent definition file.
4. From each session keep the parent's launch record (the exact definition name and the task message), the child's first event or transcript entry, the child's tool calls that create the payload directory and write payload files, and the launch's final result.
5. From each final result take the run token, the run file path, and the rendered projection. Confirm that the run file exists, that it is sealed, and that the projection's terminal status is a verdict.
6. Record, for each of the four dispatches, whether the dispatch stopped before the run started, the directory that held the payload files, and any refused write with the diagnostic it returned.
7. Retain the structured output of each dispatch and its run file beside this file.

## Attested run

- Date:
- Subject commit:
- Observations:
- Artifacts:

## Verdict

## Limitations

- The protocol dispatches each auditor against a minimal conforming target; judgment quality over a defective or large target stays unexercised.
- The Codex dispatch inherits the invoking session's execution policy, so a result under a stricter policy than the one the run records stays unexercised.
- A hosted runner that names `$RUNNER_TEMP` as the payload location stays unexercised.
- A later change to an auditor definition, an audit skill, or the skill standard's payload-path rule invalidates the record here until the protocol runs again on the new commit.
