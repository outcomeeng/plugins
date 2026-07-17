# Installation

PROVIDES checkout-bounded reading of the Codex runtime's installed and addable plugin sets and the local Codex plugin-refresh command form
SO THAT marketplace install verification and the isolated installation harness
CAN confirm which plugins Codex reports installed, derive the addable set from the checkout's generated Codex manifests, and refresh through per-plugin installs without misreading a changed CLI contract or mutating a developer's user-scope marketplace state

Install verification and the isolated installation harness read the Codex runtime's installed plugin set through its CLI, derive the addable plugin set from the checkout's generated Codex manifests, and refresh each plugin through a per-plugin install. These operations are bounded to the checkout: they report what the runtime holds and act on the checkout's generated manifests, and never reconcile, repair, or refresh a developer's user-scope marketplace registrations, plugin caches, or agent directories, per `spx/12-marketplace-state.adr.md`.

## Assertions

### Conformance

- ALWAYS: the Codex installed set is read from `codex plugin list --json --marketplace <marketplace>` and parsed as the `name` and `version` of each entry in the `installed` array, scoped to the queried marketplace; a payload that is not an object, lacks an `installed` array of named entries, or omits a string version raises rather than yielding a silent empty set or stale target, so a changed CLI contract is detected instead of misread ([test](tests/test_installed_set.conformance.l1.py))

### Compliance

- ALWAYS: the addable Codex plugin set is read from `dist/codex/*/.codex-plugin/plugin.json` rather than from a hardcoded plugin list ([test](tests/test_codex_plugin_cache.compliance.l1.py))
- NEVER: the Codex refresh invokes `codex plugin marketplace upgrade outcomeeng`; refresh installs each generated Codex plugin through `codex plugin add <plugin>@outcomeeng` ([test](tests/test_codex_plugin_cache.compliance.l1.py))
