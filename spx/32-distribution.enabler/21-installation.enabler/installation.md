# Installation

PROVIDES selection-preserving persistent marketplace installation and isolated end-to-end verification from committed checkout declarations
SO THAT marketplace maintainers and release automation
CAN refresh selected Claude Code and Codex plugins without widening either installation while proving full and subset behavior safely in disposable homes

## Assertions

- For each supported agent, isolated installation selects the complete committed catalog in catalog order, and persistent refresh selects the catalog-bounded members that agent reports installed in the invocation checkout or selected home, disabled entries included, in catalog order: an empty inventory bootstraps `spec-tree` alone, a nonempty Claude Code inventory is refreshed through native updates rather than installs, and a Codex inventory is refreshed through its native plugin operations. ([test](tests/test_installation.mapping.l1.py))
- Persistent refresh reaches every project- or local-scope Claude Code install record of a cataloged plugin on the machine: the invocation checkout's own records through the native update, every other such record through a rewrite of its install-record entry to the head of the registered marketplace source's default branch; a record outside the catalog or outside project and local scope is reported and left unchanged; no agent command runs with another checkout as working directory; the marketplace name comes from the committed catalogs and the source from the agent's registry listing; Codex's selected-home configured catalog members include entries with missing caches; the repository-installation node declares and evidences those dispositions.
- ALWAYS: persistent refresh preserves selection and activation through native update operations; an empty selection supplies only `spec-tree` with a warning and disabled activation where no activation is declared, and an agent whose bootstrap the run withholds supplies nothing, warns of no first install, and is reported as installing nothing; the repository-installation node declares and evidences those dispositions.
- Persistent Claude Code refresh is one bounded pass: it plans from the listing it reads at its start, brings every project- or local-scope record of a cataloged plugin to the target whatever version it held before and whether or not its project directory exists, reads the listing again after execution, and exits nonzero when any such record is off the target; it takes no lock and no second pass, and a record's currency between runs is whatever its last native install, native update, or rewrite wrote; the repository-installation node declares and evidences those behaviors.
- ALWAYS: trusted Codex products select skill activation independently of home-wide refresh and the globally registered home subagent definitions.
- ALWAYS: the registered marketplace entry carrying the catalog's name is the source persistent refresh refreshes from and names in its report; an absent entry is registered from the invocation checkout's own declaration.
- ALWAYS: persistent planning rejects every nonempty selected subset that omits `spec-tree` before a state-changing operation.
- ALWAYS: an agent-CLI failure identifies the exact agent and operation and stops every subsequent installation operation, except an established pending-publication absence for a selected plugin in persistent mode.

### Compliance

- ALWAYS: persistent installation targets Claude Code project scope in the invocation checkout for marketplace, inspection, and bootstrap operations, the invocation checkout's own records at their own project or local scope for the native update with the invocation checkout as working directory, every other project- or local-scope record of a cataloged plugin through the install-record rewrite with no command at all, and the selected `CODEX_HOME`, while isolated verification targets only caller-selected disposable homes. ([test](tests/test_installation.compliance.l1.py))
