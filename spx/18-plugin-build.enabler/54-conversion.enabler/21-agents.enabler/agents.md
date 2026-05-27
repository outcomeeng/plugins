# Agents

PROVIDES local conversion of Claude Code agent definitions into Codex custom-agent files
SO THAT marketplace maintainers and sync orchestration
CAN exercise wrapper-agent behavior in Codex while the marketplace plugin manifest publishes only Codex-supported plugin surfaces.

## Assertions

### Scenarios

- Given a Claude Code agent file with `name`, `description`, `model`, `skills`, and `tools` frontmatter, when agent conversion runs, then it emits a Codex custom-agent TOML file with `name`, `description`, mapped `model`, and `developer_instructions` containing the source body plus skill and tool guidance ([test](tests/test_agents.scenario.l1.py))
- Given a Claude Code agent file that names `skills`, when agent conversion runs, then the Codex custom-agent TOML preserves those skill requirements as developer-instruction guidance because Codex custom agents do not have a Claude-style spawn-time skill preload field ([test](tests/test_agents.scenario.l1.py))
- Given plugin distribution paths changed, when `just sync-marketplace` runs, then sync installs converted Codex custom-agent files into the local Codex agent directory before installed-plugin validation runs ([test](tests/test_agents.scenario.l2.py))

### Mappings

- Claude Code `model` and `effort` frontmatter map to Codex `model` and `model_reasoning_effort` fields using the converter's model mapping ([test](tests/test_agents.mapping.l1.py))
- Claude Code `permissionMode` values with supported Codex equivalents map to `sandbox_mode`, and unsupported values map to manual-review guidance in `developer_instructions` ([test](tests/test_agents.mapping.l1.py))

### Compliance

- ALWAYS: converted agents include manual-review guidance for Claude Code fields whose Codex semantics are prompt guidance rather than hard execution boundaries - `tools`, `disallowedTools`, and `skills` do not enforce Codex permissions or skill preloading ([test](tests/test_agents.compliance.l1.py))
- NEVER: agent installation claims or overwrites pre-existing Codex agent files unless they were recorded in the generated-agent manifest - user-owned files remain outside generated ownership even when their content matches generated output ([test](tests/test_agents.compliance.l1.py))
- NEVER: agent conversion writes generated agents into published Codex plugin manifest content - custom agents install through local Codex configuration such as `.codex/agents/` or `~/.codex/agents/` ([test](tests/test_agents.compliance.l1.py))
