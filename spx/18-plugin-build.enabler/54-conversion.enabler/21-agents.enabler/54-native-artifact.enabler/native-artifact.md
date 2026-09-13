# Native Artifact

PROVIDES source-to-TOML conversion for the content and skill bindings of one rendered plugin agent definition
SO THAT the agent conversion pipeline and Codex consumers
CAN preserve authored agent behavior in the Codex-native custom-agent surface

## Assertions

### Scenarios

- Given a plugin agent file with `name`, `description`, a profile selection, `skills`, and `tools` frontmatter, when agent conversion runs, then it emits a Codex custom-agent TOML file with `name`, `description`, the complete native configuration of the selected profile, source body, `skills.config` enablement plus skill guidance, and the enforceable Codex config derived from the tool allowlist ([test](tests/test_native_artifact.scenario.l1.py))
- Given a plugin agent file selecting a central profile and declaring sandbox, nickname candidates, and MCP server configuration, when agent conversion runs, then it emits the selected profile's complete native model and reasoning configuration while preserving those independent operational settings, source body, and `skills.config` enablement plus skill guidance ([test](tests/test_native_artifact.scenario.l1.py))

### Mappings

- Source `skills` entries map in source order to enabled Codex `skills.config` entries and developer-instruction guidance that states enablement is not a spawn-time preload guarantee ([test](tests/test_native_artifact.mapping.l1.py))
- Every central profile maps directly to its complete Codex-native configuration; an absent selection maps to Standard, with no model-alias or effort translation ([test](tests/test_native_artifact.mapping.l1.py))
