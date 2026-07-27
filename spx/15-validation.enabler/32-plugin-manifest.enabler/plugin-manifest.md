# Plugin Manifest Validation

PROVIDES discovery and validation of marketplace and plugin manifest files via the Claude Code CLI
SO THAT plugin authors and marketplace maintainers
CAN commit manifest files that the installed Claude Code CLI will accept without running validation manually

## Assertions

### Scenarios

- Given a directory containing `.claude-plugin/marketplace.json`, when validated, then `claude plugin validate` runs against it ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a directory containing `dist/claude/*/` or `src/plugins/*/` with `.claude-plugin/plugin.json`, when validated, then `claude plugin validate` runs against each plugin ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin that fails validation, when validated, then the script exits non-zero and reports which plugin failed ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given no marketplace or plugins found, when validated, then the script exits non-zero with an error ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin with both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` declaring the same `version` field, when validated, then the manifest parity check passes ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin with both manifests but mismatched `version` fields, when validated, then the script exits non-zero and the error names the plugin and both versions ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin with only `.claude-plugin/plugin.json` (no Codex manifest), when validated, then the manifest parity check is not applied — Codex coverage is optional ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a plugin with both manifests but one or both lack a `version` field, when validated, then the script exits non-zero and reports the missing field ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a `claude plugin validate` invocation that does not return within the configured timeout, when validated, then the runner terminates the invocation's process group and reports the target as failed, naming the timed-out command — bounded per `spx/15-validation.enabler/21-subprocess-execution.adr.md` ([test](tests/test_plugin_manifest.scenario.l1.py))
- Given a `claude plugin validate` invocation that exits after spawning a descendant that keeps its output stream open, when validated, then the runner returns as soon as the invocation exits rather than blocking on the descendant — per `spx/15-validation.enabler/21-subprocess-execution.adr.md` ([test](tests/test_plugin_manifest.scenario.l1.py))

### Properties

- Manifest version parity is symmetric: drift in either direction (Claude advanced past Codex, or Codex advanced past Claude) is reported ([test](tests/test_plugin_manifest.property.l1.py))

### Compliance

- NEVER: allow plugin manifest version drift between `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` — repository installation resolves both agent artifacts from one catalog version ([test](tests/test_plugin_manifest.scenario.l1.py))
- NEVER: the manifest-validation runner makes an unbounded capturing subprocess call — capture without a timeout, or any wait on pipe EOF — per `spx/15-validation.enabler/21-subprocess-execution.adr.md` ([audit])
