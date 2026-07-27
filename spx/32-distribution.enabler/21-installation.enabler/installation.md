# Installation

PROVIDES persistent marketplace installation and isolated end-to-end verification from committed checkout declarations
SO THAT marketplace maintainers and release automation
CAN refresh selected Claude Code and Codex installations while proving the same catalogs safely in disposable homes

## Assertions

### Compliance

- ALWAYS: repository installation derives each agent's complete plugin set from that agent's committed marketplace catalog. ([test](tests/test_installation.conformance.l1.py))
- ALWAYS: persistent installation targets Claude Code project scope and the selected `CODEX_HOME`, while isolated verification targets only caller-selected disposable homes. ([test](tests/test_installation.compliance.l1.py))
- ALWAYS: an agent-CLI failure identifies the exact agent and plugin operation and stops every subsequent installation operation. ([test](tests/test_installation.compliance.l1.py))
