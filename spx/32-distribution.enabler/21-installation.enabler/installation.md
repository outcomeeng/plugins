# Installation

PROVIDES selection-preserving persistent marketplace installation and isolated end-to-end verification from committed checkout declarations
SO THAT marketplace maintainers and release automation
CAN refresh selected Claude Code and Codex plugins without widening either installation while proving full and subset behavior safely in disposable homes

## Assertions

- For each supported agent, isolated installation selects the complete committed catalog in catalog order, and persistent refresh selects the catalog-bounded members that agent reports installed in the invocation checkout or selected home, disabled entries included, in catalog order: an empty inventory bootstraps `spec-tree` alone, a nonempty Claude Code inventory is refreshed through native updates rather than installs, and a Codex inventory is refreshed through its native plugin operations. ([test](tests/test_installation.mapping.l1.py))
- Persistent refresh reaches every project- or local-scope Claude Code install record on the machine for a cataloged plugin whose project path exists and whose readable project settings declare no noncanonical marketplace source for the native update, reporting every other record unchanged, and Codex's selected-home configured catalog members include entries with missing caches; the repository-installation node declares and evidences those dispositions.
- ALWAYS: persistent refresh preserves selection and activation through native update operations; an empty selection supplies only `spec-tree` with a warning and disabled activation where no activation is declared.
- ALWAYS: trusted Codex products select skill activation independently of home-wide refresh and the globally registered home subagent definitions.
- NEVER: an existing noncanonical marketplace registration reaches a persistent state-changing operation; source repair requires an explicit operation outside refresh.
- ALWAYS: persistent planning rejects every nonempty selected subset that omits `spec-tree` before a state-changing operation.
- ALWAYS: an agent-CLI failure identifies the exact agent and operation and stops every subsequent installation operation, except an established pending-publication absence for a selected plugin in persistent mode.

### Compliance

- ALWAYS: persistent installation targets Claude Code project scope in the invocation checkout for marketplace, inspection, and bootstrap operations, each recorded plugin's own project or local scope and project path for its native update, and the selected `CODEX_HOME`, while isolated verification targets only caller-selected disposable homes. ([test](tests/test_installation.compliance.l1.py))
