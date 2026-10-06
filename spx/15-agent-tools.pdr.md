# Agent Tools

Agent-facing tool interfaces present command forms by harness environment. Skills and agents that instruct Claude to call `spx`, `gh`, or any other CLI name the supported interactive and programmatic forms for payload input, so users see reliable behavior across Claude Code, Codex, and hosted runner contexts.

## Rationale

Claude Code, Codex, and hosted runners do not share one shell contract. Interactive sessions can read and approve multiline commands, while programmatic runners may require one physical shell line, reject command continuations, sandbox filesystem writes, or parse pipelines as separately approved operations. Teaching the command form by harness keeps the skill surface safe without pushing users into temporary files or post-hoc repairs.

GitHub's GraphQL budget belongs to the account, not to a session, so one unbounded paginated read spends the budget that every session on that account shares. A page bound written in the skill text keeps any one call from spending it, and a blocked result at the bound keeps a read that may be partial from passing as complete.

## Product properties

1. Agent-facing tool guidance is scoped by environment: interactive Claude Code and Codex sessions, programmatic Claude Code and Codex runs, and hosted programmatic runners such as GitHub Actions, for a skill a hosted workflow runs.
2. Payload-bearing commands receive their body over stdin. Interactive guidance prefers quoted heredocs when the harness accepts multiline shell. Programmatic guidance uses one physical `printf '%s\n' ... | <tool>` line when the runner requires a single command line.
3. A skill that instructs a `gh` call returning a collection — a `gh` list or search command, a `gh api` call with `--paginate` or to a collection endpoint, or a `gh api graphql` call reading a connection — names that call's page bound in its own text: a `--limit`, a page size with a page count, or a single page with its page size named; and a call whose result fills its bound returns a blocked result naming the bound, because a full result cannot show whether pages remain. A single-object read such as `gh pr view` or `gh issue view`, and `gh pr checks`, is outside this property even when its result embeds a collection.

## Verification

### Audit

- ALWAYS: skills and agents that instruct Claude to call `spx`, `gh`, or another CLI present command forms by supported harness environment — interactive Claude Code and Codex, programmatic Claude Code and Codex, and hosted programmatic runners such as GitHub Actions for a skill a hosted workflow runs ([audit])
- ALWAYS: payload-bearing tool guidance uses stdin-oriented command forms and names the safe form for each supported harness; interactive forms may use quoted heredocs, and programmatic forms use one physical `printf '%s\n' ... | <tool>` line where runner parsers require it ([audit])
- NEVER: payload-bearing tool guidance routes through temporary files, helper files, shell command substitution, or post-hoc text substitution to assemble or repair the body ([audit])
- NEVER: skill guidance instructs a `gh` call returning a collection — a `gh` list or search command, a `gh api` call with `--paginate` or to a collection endpoint, or a `gh api graphql` call reading a connection — without naming its page bound, including a list or search command that relies on the default limit of `gh`, `--paginate` without a page count, and a single-page collection read without a named page size, or reads a result that fills its page bound as complete ([audit])
