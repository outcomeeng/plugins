# Agents

PROVIDES local conversion of rendered plugin agent definitions into Codex custom-agent files
SO THAT marketplace maintainers and sync orchestration
CAN exercise wrapper-agent behavior in Codex while the marketplace plugin manifest publishes only Codex-supported plugin surfaces.

## Assertions

### Scenarios

- Given a rendered plugin agent file with `name`, `description`, `model`, `skills`, and `tools` frontmatter, when agent conversion runs, then it emits a Codex custom-agent TOML file with `name`, `description`, mapped `model`, source body, `skills.config` enablement plus skill guidance, and the enforceable Codex config derived from the tool allowlist ([test](tests/test_agents.scenario.l1.py))
- Given a rendered Codex-target plugin agent file whose `model` already names a Codex model and whose frontmatter declares Codex runtime overrides, when agent conversion runs from the generated Codex output tree, then it emits a Codex custom-agent TOML file preserving the model, reasoning effort, sandbox, nickname candidates, MCP server config, source body, and `skills.config` enablement plus skill guidance ([test](tests/test_agents.scenario.l1.py))

### Mappings

- Source `skills` entries map in source order to enabled Codex `skills.config` entries and developer-instruction guidance that states enablement is not a spawn-time preload guarantee ([test](tests/test_agents.mapping.l1.py))
- Source `model` and `effort` frontmatter map to Codex `model` and `model_reasoning_effort` fields using the converter's model mapping ([test](tests/test_agents.mapping.l1.py))
- Source `permissionMode` values with supported Codex equivalents map to `sandbox_mode`, and unsupported values map to manual-review guidance in `developer_instructions` ([test](tests/test_agents.mapping.l1.py))
- Source tool allowlists that omit web-capable tools map to `web_search = "disabled"`, while absent `tools` frontmatter, the `all` tool sentinel, and allowlists that include any web-capable tool leave web search unset for runtime defaults ([test](tests/test_agents.mapping.l1.py))
- Source file-read-only and web-capable-only tool allowlists map to `sandbox_mode = "read-only"` when no explicit `permissionMode` is present; absent `tools` frontmatter, script-capable allowlists, write-capable allowlists, the `all` tool sentinel, and explicit unmapped `permissionMode` values leave sandbox mode unset for runtime defaults plus manual-review guidance ([test](tests/test_agents.mapping.l1.py))

### Compliance

- ALWAYS: converted agents set an agent-type environment marker in `shell_environment_policy.set` so local Codex policy surfaces can distinguish one generated agent from another without matching prompt text or filenames ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: converted agents keep manual-review guidance for source fields whose Codex semantics remain prompt guidance rather than hard execution boundaries - `disallowedTools` and command-level meanings inside `tools` do not restrict commands executed through allowed shell tools, and `skills.config` enables named skills without proving spawn-time preload behavior ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: duplicate source agent names that slugify to the same Codex filename fail conversion before any install writes generated files ([test](tests/test_agents.compliance.l1.py))
- NEVER: agent installation claims or overwrites pre-existing Codex agent files unless they were recorded in the generated-agent manifest - user-owned files remain outside generated ownership even when their content matches generated output ([test](tests/test_agents.compliance.l1.py))
- NEVER: agent conversion writes generated agents into published Codex plugin manifest content - custom agents install through local Codex configuration under `.codex/agents/` ([test](tests/test_agents.compliance.l1.py))
