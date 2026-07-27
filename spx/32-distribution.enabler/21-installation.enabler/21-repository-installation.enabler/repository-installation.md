# Repository Installation

PROVIDES `just install-marketplace`, which drives real Claude Code and Codex plugin CLIs in disposable agent homes and materializes plugin-owned agent definitions in the invocation checkout
SO THAT marketplace maintainers and the release lifecycle
CAN prove committed repository declarations install end to end without mutating live user homes

## Assertions

### Scenarios

- Given the committed Claude Code and Codex marketplace catalogs, when `just install-marketplace` runs, then each agent registers the checkout marketplace and installs and enables every catalog plugin in a disposable home.
- Given every plugin in the Claude Code and Codex marketplace catalogs, when the isolated installation harness installs the catalog, then every catalog plugin is observable as installed and enabled through the corresponding real agent CLI.
- Given an installed plugin that owns Codex agent definitions, when its lifecycle installation runs, then its generated definitions are placed in the invocation checkout's `.codex/agents/` namespace while definitions outside that plugin's ownership remain unchanged.
- Given an agent marketplace, plugin, or lifecycle operation that fails, when repository installation runs, then it reports the failing agent and plugin operation and performs no later operation.

### Properties

- Running repository installation twice against unchanged declarations and catalogs produces the same installed state and no checkout placement drift.

### Compliance

- NEVER: repository installation reads or writes repository `.codex/config.toml` as Codex plugin installation or enablement state.
- NEVER: repository installation reads or mutates a developer's ambient agent home, marketplace registration, plugin cache, or agent directory.
