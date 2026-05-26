# Known issues — agents conversion enabler

## FOLLOW-UP [evidence]: name-collision invariant lacks declared evidence

`outcomeeng.distribution.agents.convert_agents` raises `AgentConversionError`
when two Claude agent names slugify to the same Codex agent filename, but the
agents node does not yet declare an assertion for that invariant and the current
test files do not exercise the collision path.

Future evidence work in this node should add a compliance assertion and test for
duplicate converted filenames across source agent files.
