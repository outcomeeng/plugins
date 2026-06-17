# Agent Tools

Agent-facing tool interfaces present command forms by harness environment. Skills and agents that instruct Claude to call `spx`, `gh`, or any other CLI name the supported interactive and programmatic forms for payload input, waiting, and mutation, so users see reliable behavior across Claude Code, Codex, and hosted runner contexts.

## Rationale

Claude Code, Codex, and hosted runners do not share one shell contract. Interactive sessions can read and approve multiline commands, while programmatic runners may require one physical shell line, reject command continuations, sandbox filesystem writes, or parse pipelines as separately approved operations. Teaching the command form by harness keeps the skill surface safe without pushing users into temporary files or post-hoc repairs.

## Product properties

1. Agent-facing tool guidance is scoped by environment: interactive Claude Code and Codex sessions, programmatic Claude Code and Codex runs, and hosted programmatic runners such as GitHub Actions.
2. Payload-bearing commands receive their body over stdin. Interactive guidance prefers quoted heredocs when the harness accepts multiline shell. Programmatic guidance uses one physical `printf '%s\n' ... | <tool>` line when the runner requires a single command line.
3. GitHub PR check waiting uses exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30` in every supported harness. The governing skill states the bounded return condition: the command exits when all PR checks finish, and `--fail-fast` exits on the first failed check. Other tool waits are not exposed from skills or agents unless a product decision names the exact command and return condition first.

## Verification

### Audit

- ALWAYS: skills and agents that instruct Claude to call `spx`, `gh`, or another CLI present command forms by supported harness environment — interactive Claude Code and Codex, programmatic Claude Code and Codex, and hosted programmatic runners such as GitHub Actions when relevant ([audit])
- ALWAYS: payload-bearing tool guidance uses stdin-oriented command forms and names the safe form for each supported harness; interactive forms may use quoted heredocs, and programmatic forms use one physical `printf '%s\n' ... | <tool>` line where runner parsers require it ([audit])
- NEVER: payload-bearing tool guidance routes through temporary files, helper files, shell command substitution, or post-hoc text substitution to assemble or repair the body ([audit])
- ALWAYS: GitHub PR check waiting guidance uses exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30`, with the bounded return condition stated by the governing skill ([audit])
- NEVER: skills or agents instruct Claude to wait for GitHub PR checks through runtime heartbeats, runtime timers, shell-owned sleeps, `while` or `until` polling loops, `gh run watch`, background keep-alive commands, any other `gh pr checks` watcher form, or command continuations that the runner parses as separate operations ([audit])
- ALWAYS: state-changing external tool calls require explicit user instruction in the same turn ([audit])
