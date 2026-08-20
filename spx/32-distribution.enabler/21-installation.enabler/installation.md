# Installation

PROVIDES selection-preserving persistent marketplace installation and isolated end-to-end verification from committed checkout declarations
SO THAT marketplace maintainers and release automation
CAN refresh selected Claude Code and Codex plugins without widening either installation while proving full and subset behavior safely in disposable homes

## Assertions

### Mappings

- For each supported agent, isolated repository installation maps the committed catalog to its complete ordered plugin set, while persistent installation maps the pre-run installed catalog members to catalog order. ([test](tests/test_installation.mapping.l1.py))

### Compliance

- ALWAYS: persistent installation targets Claude Code project scope and the selected `CODEX_HOME`, while isolated verification targets only caller-selected disposable homes. ([test](tests/test_installation.compliance.l1.py))
- ALWAYS: persistent planning rejects every nonempty installed subset that omits `spec-tree` before a state-changing operation. ([test](tests/test_installation.compliance.l1.py))
- ALWAYS: an agent-CLI failure identifies the exact agent and plugin operation and stops every subsequent installation operation. ([test](tests/test_installation.compliance.l1.py))
