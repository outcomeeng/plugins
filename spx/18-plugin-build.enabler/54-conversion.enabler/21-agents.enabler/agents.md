# Agents

PROVIDES conversion of rendered plugin agent definitions into the Codex-native custom-agent artifact the build publishes with each plugin
SO THAT every Codex consumer and hosted agent environment
CAN run the marketplace's agents, which a Codex plugin manifest cannot declare, per `spx/12-marketplace-state.adr.md`.

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
- NEVER: an agent whose source path resolves to no `<plugin>/agents` ancestor receives a marker - the marker namespaces every generated agent by its owning plugin, so a source outside that namespace fails conversion rather than emitting an unnamespaced marker ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: converted agents keep manual-review guidance for source fields whose Codex semantics remain prompt guidance rather than hard execution boundaries - `disallowedTools` and command-level meanings inside `tools` do not restrict commands executed through allowed shell tools, and `skills.config` enables named skills without proving spawn-time preload behavior ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: two sources whose outputs claim the same path in a target's generated tree fail the build before it writes any generated file ([test](tests/test_agents.compliance.l1.py))
- NEVER: placing a plugin's converted agents touches a file outside the namespace that plugin's slug prefixes - a definition the developer authored, or one another plugin provides, survives placement and pruning unchanged even when its content matches generated output ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: for a target whose agent namespace is flat, a converted agent's filename and `name` carry the plugin as slug prefix, `<plugin>_<agent>`, so an agent-harness policy matching on name distinguishes the marketplace's agents from agents the developer authored ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: the build publishes each converted agent as plugin tree content in its target's generated tree, and the plugin manifest declares the surfaces that target resolves through the manifest without declaring agents ([test](tests/test_agents.compliance.l1.py))
