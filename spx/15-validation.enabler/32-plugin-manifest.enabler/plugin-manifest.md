# Plugin Manifest Validation

PROVIDES discovery and validation of marketplace and plugin manifest files via the Claude Code CLI
SO THAT plugin authors and marketplace maintainers
CAN commit manifest files that the installed Claude Code CLI will accept without running validation manually

## Assertions

### Scenarios

- Given a directory containing `.claude-plugin/marketplace.json`, when validated, then `claude plugin validate` runs against it ([test](tests/test_plugin_manifest.unit.py))
- Given a directory containing `plugins/*/` with `.claude-plugin/plugin.json`, when validated, then `claude plugin validate` runs against each plugin ([test](tests/test_plugin_manifest.unit.py))
- Given a plugin that fails validation, when validated, then the script exits non-zero and reports which plugin failed ([test](tests/test_plugin_manifest.unit.py))
- Given no marketplace or plugins found, when validated, then the script exits non-zero with an error ([test](tests/test_plugin_manifest.unit.py))
