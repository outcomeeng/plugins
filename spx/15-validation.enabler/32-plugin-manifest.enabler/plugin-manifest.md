# Plugin Manifest Validation

PROVIDES discovery and validation of marketplace and plugin manifest files via the Claude Code CLI
SO THAT plugin authors and marketplace maintainers
CAN commit manifest files that the installed Claude Code CLI will accept without running validation manually

## Assertions

### Scenarios

- Given a directory containing `.claude-plugin/marketplace.json`, when validated, then `claude plugin validate` runs against it ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a directory containing `plugins/*/` with `.claude-plugin/plugin.json`, when validated, then `claude plugin validate` runs against each plugin ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin that fails validation, when validated, then the script exits non-zero and reports which plugin failed ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given no marketplace or plugins found, when validated, then the script exits non-zero with an error ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin with both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` declaring the same `version` field, when validated, then the manifest parity check passes ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin with both manifests but mismatched `version` fields, when validated, then the script exits non-zero and the error names the plugin and both versions ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin with only `.claude-plugin/plugin.json` (no Codex manifest), when validated, then the manifest parity check is not applied — Codex coverage is optional ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin with both manifests but one or both lack a `version` field, when validated, then the script exits non-zero and reports the missing field ([test](tests/test_plugin_manifest.scenario.l1.py))

### Properties

- Manifest version parity is symmetric: drift in either direction (Claude advanced past Codex, or Codex advanced past Claude) is reported ([test](tests/test_plugin_manifest.scenario.l1.py))

### Compliance

- NEVER: allow plugin manifest version drift between `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` — drift breaks marketplace cache preservation and `validate_install` ([test](tests/test_plugin_manifest.scenario.l1.py))
