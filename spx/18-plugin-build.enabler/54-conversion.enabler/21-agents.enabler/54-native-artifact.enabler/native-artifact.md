# Native Artifact

PROVIDES source-to-TOML conversion for the content and skill bindings of one rendered plugin agent definition
SO THAT the agent conversion pipeline and Codex consumers
CAN preserve authored agent behavior in the Codex-native custom-agent surface

## Assertions

### Scenarios

- Given a rendered plugin agent file with `name`, `description`, `model`, `skills`, and `tools` frontmatter, when agent conversion runs, then it emits a Codex custom-agent TOML file with `name`, `description`, mapped `model`, source body, `skills.config` enablement plus skill guidance, and the enforceable Codex config derived from the tool allowlist ([test](tests/test_native_artifact.scenario.l1.py))
- Given a rendered Codex-target plugin agent file whose `model` already names a Codex model and whose frontmatter declares Codex runtime overrides, when agent conversion runs from the generated Codex output tree, then it emits a Codex custom-agent TOML file preserving the model, reasoning effort, sandbox, nickname candidates, MCP server config, source body, and `skills.config` enablement plus skill guidance ([test](tests/test_native_artifact.scenario.l1.py))

### Mappings

- Source `skills` entries map in source order to enabled Codex `skills.config` entries and developer-instruction guidance that states enablement is not a spawn-time preload guarantee ([test](tests/test_native_artifact.mapping.l1.py))
- Source `model` and `effort` frontmatter map to Codex `model` and `model_reasoning_effort` fields using the converter's model mapping ([test](tests/test_native_artifact.mapping.l1.py))
